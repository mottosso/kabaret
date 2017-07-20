'''
    Copyright (c) Supamonks Studio and individual contributors.
    All rights reserved.

    This file is part of kabaret, a python Digital Creation Framework.

    Kabaret is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.
        
    Redistributions in binary form must reproduce the above copyright 
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
    
    Kabaret is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.
    
    You should have received a copy of the GNU Lesser General Public License
    along with kabaret.  If not, see <http://www.gnu.org/licenses/>

--

    The kabaret.core.ro.client package:
        Define the ClientView, ClientService and Client classes.
    
''' 

import sys
import os
import select
import contextlib
import Queue

import Pyro4
import Pyro4.utils.flame

from kabaret.core.project.station_config import get_station_class
from kabaret.core.events.dispatcher import EventDispatcher
from kabaret.core.events.event import Event

from kabaret.core.utils import get_user_name

from . import url
from . import CommunicationError
from . import worker

from . import this_host

ENV_PROJECT_NAME = 'KABARET_PROJECT_NAME'
ENV_APPHOST_URL = 'KABARET_APPHOST_URL'
ENV_FOCUS_ID = 'KABARET_FOCUS_ID'

class ClientView(object):
    def __init__(self, client, app_name):
        super(ClientView, self).__init__()

        #print '#################----------- NEW VIEW', client, self
        self.client = client
        self.app_name = app_name
        
        self._is_active = True
    
    def is_active(self):
        return self._is_active
    
    def on_view_toggled(self, visible):
        self._is_active = visible

    def on_disconnect(self):
        pass
    
    def on_connect(self):
        pass


class ClientService(object):
    def __init__(self, client, event_queue):
        self._client = client
        
        self.event_queue = event_queue
                
    def receive_event(self, event):
        self.event_queue.put(event)

    def ping(self):
        return 'pong' 
    
class RemoteApps(object):
    def __init__(self, client):
        self._client = client
        self._remote_apps = {}
    
    def keys(self):
        '''
        Returns all the APP_KEYS declared here.
        '''
        return self._remote_apps.keys()
    
    def __getitem__(self, app_key):
        return self._remote_apps[app_key]
    
    def __getattr__(self, app_key):
        return self._remote_apps[app_key]
    
    def add_app(self, app_key, is_proj_app=False):
        self._remote_apps[app_key] = RemoteApp(self._client, app_key, is_proj_app)
        
    def clear(self):
        self._remote_apps = {}
        
class RemoteApp(object):
    def __init__(self, client, app_key, is_proj_app=False):
        super(RemoteApp, self).__init__()
        self.client = client
        self.app_key = app_key
        self.is_proj_app = is_proj_app
        
        self.cmds = RemoteCmds(self)

    def _do_cmd(self, command_name, args, kwargs):
        if self.is_proj_app:
            return self.client.run_proj_app_command(
                self.app_key, 
                command_name, 
                args, kwargs
            )
        else:
            return self.client.run_app_command(
                self.app_key, 
                command_name, 
                args, kwargs
            )

class RemoteCmds(object):
    def __init__(self, remote_app):
        super(RemoteCmds, self).__init__()
        self._remote_app = remote_app
        
    def _do_cmd(self, command_name, args, kwargs):
        return self._remote_app._do_cmd(command_name, args, kwargs)
    
    def get_command(self, command_name):
        return RemoteCommand(
            self, command_name
        )
        
    def __getattr__(self, command_name):
        return self.get_command(command_name)

class RemoteCommand(object):
    def __init__(self, remote_cmds, command_name):
        super(RemoteCommand, self).__init__()
        self.remote_cmds = remote_cmds
        self.command_name = command_name
        
    def __call__(self, *args, **kwargs):
        return self.remote_cmds._do_cmd(self.command_name, args, kwargs)

class Client(object):
    _WORKER_CLASS = worker.Worker

    def __init__(self, project_name='DefaultProject'):
        super(Client, self).__init__()
        
        self.station_class = get_station_class()
        self._host_python_paths = []
        
        self.project_name = project_name
        
        self._event_queue = Queue.Queue(0)
        self._daemon = None
        
        self._backservice = None
        self._init_backservice()
        
        self._worker = None
        self._init_worker()
        
        self.apphost = None
        self.async_apphost = None
        
        self._current_future_target = [] # contextual result handler queue
        self._no_result = False          # context for one way calls
        self._futures = set()
        
        self.apps = RemoteApps(self)         # Client apps commands 
        self.project_apps = RemoteApps(self) # Project apps commands 
        
        self._event_dispatcher = EventDispatcher()
        
        self._focus_id = None # an id to focus on. some views will use it
        
        self._views = [] # list of ClientView instances
    
    def _configure_worker(self, worker):
        worker._type = 'Kabaret Studio'
        worker.add_features('kabaret')
     
    def get_available_apphost_infos(self, match_station_class=True):
        '''
        Returns a list of keyword usable for
        the connect() method:
            projects = client.get_available_apphost_infos()
            client.connect(**projects[0])
        
        If match_station_class is True, only the apphost with the same
        station_class as this client will be considered.
        '''
        ret = []
        try:
            with url.get_service() as service:
                for name in service.list().keys():
                    for_type, kwargs = url.From(name)
                    if for_type == url.For.apphost:
                        if not match_station_class or kwargs['station_class'] == self.station_class:
                            kwargs['match_station_class'] = match_station_class
                            ret.append(kwargs)
        except url.UrlError:
            return []
        return ret
    
    def _init_backservice(self):
        self._backservice = ClientService(self, self._event_queue)
        if self._daemon is None:
            self._daemon = Pyro4.Daemon(
                # We need to use the host IP here because the apphost
                # might run on a host w/o proper DNS resolution
                this_host(name=False)
            )
        self._daemon.register(self._backservice)

    def _init_worker(self):
        self._worker = self._WORKER_CLASS(self)
        self._configure_worker(self._worker)
        if self._daemon is None:
            self._daemon = Pyro4.Daemon(
                # We need to use the host IP here because the apphost
                # might run on a host w/o proper DNS resolution
                this_host(name=False)
            )
        self._daemon.register(self._worker)
        self._worker.set_waiting()
        
    def register_view(self, view):
        self._views.append(view)
        if self.connected():
            view.on_connect()
            
    def shutdown(self):
        print 'Shutting down client'
        self.disconnect()
        self._daemon.shutdown()
        self._daemon = None
        
    def disconnect(self):
        if self.apphost is not None:
            [ view.on_disconnect() for view in self._views ]
            if self._backservice is not None:
                try:
                    self.apphost.drop_client(self._backservice)
                except Pyro4.errors.CommunicationError, err:
                    # the apphost using our backservice
                    # is not there anymore...
                    print 'Call to apphost.drop_client failed', str(err)
            if self._worker is not None:
                try:
                    self.apphost.drop_worker(self._worker)
                except Pyro4.errors.CommunicationError, err:
                    # the apphost using our worker
                    # is not there anymore...
                    print 'Call to apphost.drop_worker failed', str(err)
                finally:
                    self._worker._id = None
            self.apphost._pyroRelease()
            self.apphost = None
            self.async_apphost = None
            
        self._unapply_station_config()
        self._clear_remote_apps()

    def connect_from_env(self):
        '''
        Use the environment variable to choose a project name
        and an apphost url, and try to connect on it.
        '''
        project_name = os.environ.get(ENV_PROJECT_NAME, None)
        if project_name is None:
            raise ValueError(
                'Could not find %r in environment, cannot connect client.'%(ENV_PROJECT_NAME,)
            )
            
        apphost_url = os.environ.get(ENV_APPHOST_URL, None)
        if apphost_url is None:
            raise ValueError(
                'Could not find %r in environment, cannot connect client.'%(ENV_APPHOST_URL,)
            )
            
        self.set_apphost_from_url(project_name, apphost_url)

    def connect(
            self, project_name=None, host=None, user=None, 
            station_class=None, match_station_class=True
        ):
        '''
        Connects to the AppHost for the given project name.
        If the client is already connected, disconnect is 
        called prior to establishing a new connection.
        
        If project_name is None, the last one is used (or the
        one given in the constructor)
        
        If host and user are None, they default to the current
        host and the current user.
        
        The station_class and match_station_class arguments are
        passed to url.For.apphost() call. See its doc for more 
        explanations.
        '''
        project_name = project_name or self.project_name
        
        if project_name is None:
            raise ValueError(
                'No project name specified and no default value found: cannot connect.'
            )
                
        apphost_url=url.For.apphost(project_name, user, host, station_class, match_station_class)
        self.set_apphost_from_url(project_name, apphost_url)
        
    def set_apphost_from_url(self, project_name, apphost_url, local_url=False):
        '''
        Connects to the given remote AppHost.
        The project_name must match the project in the url or the behavior is
        unknown.
        '''
        if self.connected():
            self.disconnect()

        self.project_name = project_name
            
        self.apphost = url.resolve(apphost_url, local=local_url, ping=True)

        self.async_apphost = Pyro4.async(self.apphost)
        self.apphost._pyroOneway.add('register_client')
        self.apphost._pyroOneway.add('drop_client')
        self.apphost._pyroOneway.add('register_worker')
        self.apphost._pyroOneway.add('drop_worker')
        self.apphost.register_client(self._backservice)
        self.apphost.register_worker(self._worker)
        self.tick() # to let the backservice and workers get connected from apphost side
        
        self._apply_station_config()
        self._init_remote_apps()

        [ view.on_connect() for view in self._views ]

    def connected(self):
        return self.apphost is not None
    
    def _unapply_station_config(self):
        for path in self._host_python_paths:
            try:
                sys.path.remove(path)
            except ValueError:
                pass
        self._host_python_paths = []

    def _apply_station_config(self):
        self._host_python_paths = self.apphost.get_client_python_paths()
        # The paths are ordered so we need to reverse the
        # list if we prepend each:
        for path in reversed(self._host_python_paths):
            if path not in sys.path:
                sys.path.insert(0, path)

    def _clear_remote_apps(self):
        self.apps.clear()
        self.project_apps.clear()
            
    def _init_remote_apps(self):
        self.apps.clear()
        for app_key in self.apphost.app_keys():
            self.apps.add_app(app_key)
    
        self.project_apps.clear()
        for app_key in self.apphost.app_keys(in_project=True):
            self.project_apps.add_app(app_key, is_proj_app=True)
    
    def kill_apphost(self):
        self.apphost._pyroOneway.add('kill')
        self.apphost.kill()
        
    def tick(self):
        if self.apphost is None:
            return 'Disconnected'
        
        while True:
            # flush all pyro socket events (callbacks from self.apphost)
            s,_,_ = select.select(self._daemon.sockets,[],[],0.01)
            if s:
                self._daemon.events(s)
            else:
                break

        nb_events = 0
        max_events_per_tick = 50
        while nb_events<max_events_per_tick:
            try:
                event = self._event_queue.get_nowait()
            except Queue.Empty:
                break
            nb_events += 1
            self.receive_event(event)
        events_status = 'E:'+str(nb_events)
        
        for f in list(self._futures): # list it so that we can pop from it)
            if f.ready:
                self._futures.remove(f)
                try:
                    value = f.value
                except CommunicationError:
                    # all the futures are lost and
                    # would raise too, we need to
                    # drop them and let the user
                    # reconnect.
                    self._futures = set()
                    print 'DISCONNECING AFTER Communication Error'
                    self.disconnect()
                    #return 'Disconnected' 
                except Exception, err:
                    import sys
                    Pyro4.util.excepthook(*sys.exc_info())
                    if f._on_err is not None:
                        f._on_err(f, err)
                        continue
                    else:
                        self.on_get_result_error(f, err)
                    
                #print 'FUTURE READY', value
                try:
                    f._on_result(f.value)
                except Exception, err:
                    import traceback
                    traceback.print_exc()
                    self.on_result_handler_error(f, err)
                    
        future_status = 'Q:'+str(len(self._futures))
        return ' '.join((events_status, future_status))
    
    
    def run_proj_app_command(self, app_key, command_name, args, kwargs):
        return self._run_apphost_command('do_project_command', app_key, command_name, args, kwargs)

    def run_app_command(self, app_key, command_name, args, kwargs):
        return self._run_apphost_command('do_command', app_key, command_name, args, kwargs)
        
    def _run_apphost_command(self, apphost_method_name, app_key, command_name, args, kwargs):
        if self._current_future_target:
            if self._no_result:
                raise Exception('Cannot be async and one way! (result_to + no_result)')
            #import time
            #print '------------------- FUTURED', apphost_cmd_name, path, time.time()
            future = getattr(self.async_apphost, apphost_method_name)(
                app_key, command_name, args, kwargs
            )
            # The _on_result and _on_err are attributes added to 
            # the Pyro4.core.FutureResult instance returned by self.async_apphost
            future._on_result, future._on_err = self._current_future_target[-1]
            self._futures.add(future)
            return future
        else:
            if self._no_result:
                self.apphost._pyroOneway.add('do_cmd')
            else:
                try:
                    self.apphost._pyroOneway.remove('do_cmd')
                except KeyError:
                    pass
            #print 'REMOTE COMMAND', getattr(self.apphost, apphost_method_name)
            #print 'apphost:', self.apphost
            ret = getattr(self.apphost, apphost_method_name)(
                app_key, command_name, args, kwargs
            )
            #print '--->', ret
            return ret
        
    @contextlib.contextmanager
    def no_result(self):
        self._no_result = True
        try:
            yield
        finally:
            self._no_result = False
        
    @contextlib.contextmanager
    def result_to(self, callable, on_err=None):
        self._current_future_target.append((callable, on_err))
        try:
            yield
        finally:
            self._current_future_target.pop()
        
    def receive_event(self, event):
        #print 'Client', self, 'got event:', event
        try:
            self._event_dispatcher.dispatch(event)
        except:
            # we can't raise here or the apphost will
            # consider us deconnected.
            print '#------------------ ERROR IN EVENT HANDLING [TRACE BEGIN]'
            import traceback
            traceback.print_exc()
            print '#------------------ ERROR IN EVENT HANDLING [TRACE END]'
            
        if event.etype == event.TYPE.MESSAGE:
            self.on_message(event.data)
            
    def add_event_handler(self, handler, app_key, path, etype=None):
        self._event_dispatcher.add_handler(
            handler, app_key, path, etype
        )

    def remove_event_handler(self, handler):
        self._event_dispatcher.remove_handler(handler)
        
    def send_event(self, event):
        self._event_dispatcher.dispatch(event)

    def set_focus_id_from_env(self):
        focus_id_str = os.environ.get(ENV_FOCUS_ID, None)
        if focus_id_str is None:
            print 'Could not find %r in environment, cannot set current id.'%(ENV_FOCUS_ID,)
            return
        try:
            focus_id = eval(focus_id_str)
        except:
            print 'Could not parse %r from environment, cannot set current id.'%(ENV_FOCUS_ID,)
            return

        self._set_focus_id(focus_id)

    def set_focus_id(self, focus_id):
        self._set_focus_id(focus_id)
        
    def _set_focus_id(self, focus_id):
        self._focus_id = focus_id
        self.send_event(
            Event('GUI', ['FLOW', 'Nav', 'root', 'Focus Parent'], Event.TYPE.UPDATED, focus_id[:-1])
        )
        self.send_event(
            Event('GUI', ['FLOW', 'Nav', 'live_bookmark', 'Focus'], Event.TYPE.UPDATED, focus_id)
        )
        self.send_event(
            Event('GUI', ['FLOW', 'Nav', 'Focus'], Event.TYPE.UPDATED, focus_id)
        )

    def on_worker_checkpoint(self, message, step_number, nb_steps):
        self.send_event(
            Event('GUI', ['WorkQueue'], Event.TYPE.UPDATED, None)
        )
        
    def get_commands(self, app_key=None, menu=None):
        '''
        Returns the ui information of the commands in the 
        given app (or all apps) that are present
        in the given menu (or all menus).
        ''' 
        if not self._current_future_target:
            return self.apphost.get_commands(app_key, menu)
        #else:
        future = self.async_apphost.get_commands(app_key, menu)
        future._on_result, future._on_err = self._current_future_target[-1]
        self._futures.add(future)
    
    def get_command_history(self):
        '''
        Returns entry_id and entry_infos for each command 
        in the apphost command history.
        '''
        if not self._current_future_target:
            return self.apphost.get_command_history()
        #else:
        future = self.async_apphost.get_command_history()
        future._on_result, future._on_err = self._current_future_target[-1]
        self._futures.add(future)

    def get_embedded_worker_id(self, features=None, documents=[], allow_busy=False):
        '''
        Returns the id of the worker embedded in this client.
        
        If features is not None, it must be a list of str.
        In this case, None is returned if the embedded worker
        does not fulfill all the listed features.
        
        The documents argument must be None or a list of acceptable
        value for the worker's get_document_name() return value.
        If a list and the worker doc is not in this list, None
        is returned.
        
        '''
        if not allow_busy and self._worker.is_busy():
            return None
        
        if features is not None and not self._worker.has_features(features):
            return None
        
        if documents is not None and self._worker.get_document_name() not in documents:
            return None
        
        return self._worker.get_id()
    
    def get_embedded_worker_infos(self):
        '''
        Returns all informations on the embedded worker in a dict.
        '''
        if self._worker is None:
            return {}
        return self._worker.get_infos()
    
    def set_embedded_worker_paused(self, b):
        '''
        Pause/UnPause the embedded worker.
        '''
        if self._worker is None:
            return
        self._worker.set_paused(b)
    
    def is_embedded_worker_paused(self):
        return self._worker.is_paused()
    
    def get_workers_infos(self, this_user_only=False, this_host_only=False):
        user = this_user_only and get_user_name() or None
        host = this_host_only and this_host() or None
        
        if not self._current_future_target:
            return self.apphost.get_workers_infos(user, host)
        #else:
        future = self.async_apphost.get_workers_infos(user, host)
        future._on_result, future._on_err = self._current_future_target[-1]
        self._futures.add(future)
    
    def drop_apphost_disconnected_workers(self):
        self.apphost.drop_disconnected_workers()
        
    def on_get_result_error(self, future, error):
        print 'ERROR while getting future result:\n %s\n %s'%(future, error)
        raise error
    
    def on_result_handler_error(self, future, error):
        print 'ERROR while processing future result:\n %s\n %s'%(future, error)
        raise error
    
    def on_result(self, result):
        print 'on_result', result 

    def on_message(self, msg):
        #print 'CLIENT MESSAGE:', msg
        pass