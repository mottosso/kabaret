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

    The kabaret.core.apphost package:
        Defines the AppHost class.
        
        The AppHost is responsible for the instantiation of every app declared in
        the project it is connected to.
        When doing so, the AppHost does not check app dependencies. The
        app list is considered validated by the project.
        (See kabaret.core.project.check.check_project or the kabadmin.py
        command line tool)
        
        Once alive, the AppHost is responsible for the app commands execution
        and events dispatching to apps and clients.
        
        The hosted apps have their event tool configured to work with
        the host (using set_event_emitter() and set_event_handler_adder())
        See kabaret.core.app.base for more on that.
        
        For a client to be able to receive events, it must call 
        register_client().
        It is a good practice to call drop_client() when the client 
        disconnects from the AppHost.
    
'''

import inspect
import contextlib

from kabaret.core.project.station_config import get_station_class
from kabaret.core.events.dispatcher import EventDispatcher
from kabaret.core.events.event import Event
from kabaret.core.apps import load_apps
from kabaret.core.apps.command import CommandHistory


class ClientWorker(object):
    '''
    Wrapper for clients' workers
    '''
    class ConnectionError(Exception):
        pass
    
    def __init__(self, manager, worker):
        super(ClientWorker, self).__init__()
        self._manager = manager
        self._worker = worker
        self._id = None
        self._connected = None
    
    def _on_change(self):
        self._manager.changed(self)
        
    def set_id(self, worker_id):
        if self._id is not None:
            raise Exception('This Worker ID is already set to '+repr(self._id))

        try:
            self._worker.set_id(worker_id)
        except:
            self._id = None
        else:
            self._id = worker_id
        finally:
            self._on_change()
    
    def check_connected(self):
        before = self._connected
        try:
            self._worker.ping()
        except:
            self._connected = False
        else:
            self._connected = True
        
        if before != self._connected:
            self._on_change()
        return self._connected
        
    def connected(self, update=False):
        if update:
            return self.check_connected()
        return self._connected
    
    def get_id(self):
        return self._id
    
    def get_infos(self):
        if not self.connected():
            return {
                'type': '???',
                'features': [],
                'document': 'not connected',
                'status': 'not connected',
                'station_class': '???',
                'host': 'not connected',
                'user': 'not connected',
                'paused': False,
            }
        return self._worker.get_infos()
    
    def ping(self):
        if not self.connected():
            return None
        return self._worker.ping()

    def get_type(self):
        if not self.connected():
            return '???'
        return self._worker.get_type()
    
    def get_station_class(self):
        if not self.connected():
            return '???'
        return self._worker.get_station_class()
    
    def get_features(self):
        if not self.connected():
            return []
        return self._worker.get_features()
    
    def has_features(self, features):
        return set(features).issubset(self.get_features())
    
    def get_document_name(self):
        if not self.connected():
            return 'not connected'
        return self._worker.get_document_name()
    
    def get_status(self):
        if not self.connected():
            return 'not connected'
        return self._worker.get_status()
    
    def get_host(self):
        if not self.connected():
            return 'not connected'
        return self._worker.get_host()
        
    def get_user(self):
        if not self.connected():
            return 'not connected'
        return self._worker.get_user()
        
    def is_busy(self):
        if not self.connected():
            raise self.ConnectionError('Cannot get busy state on un-connected worker')
        return self._worker.is_busy()
    
    def _start_busy(self):
        if not self.connected():
            raise self.ConnectionError('Cannot start_busy on un-connected worker')
        self._worker.begin_busy()
        self._on_change()
    
    def _end_busy(self):
        if not self.connected():
            raise self.ConnectionError('Cannot end_busy on un-connected worker')
        self._worker.end_busy()
        self._on_change()

    @contextlib.contextmanager
    def busy(self, clear_namespace=True):
        if self.is_busy():
            raise Exception('This worker is already busy')
        
        if clear_namespace:
            self.clear_namespace()
        self._start_busy()
        try:
            yield
        except:
            raise
        finally:
            self._end_busy()
            
    def clear_namespace(self):
        if not self.connected():
            raise self.ConnectionError() 
        self._worker.clear_namespace()

    def set_focus_id(self, focus_id):
        if not self.connected():
            raise self.ConnectionError()
        self._worker.set_focus_id(focus_id)
        
    def execute(self, code):
        if not self.connected():
            raise self.ConnectionError() 
        self._worker.execute(code)

    def evaluate(self, expression):
        if not self.connected():
            raise self.ConnectionError() 
        return self._worker.evaluate(expression)

    def _func_to_code(self, func):
        lines = inspect.getsourcelines(func)[0]
        indent = inspect.indentsize(lines[0])
        code = ''.join([ i[indent:] for i in lines ])
        return code
    
    def send_func(self, func):
        if not self.connected():
            raise self.ConnectionError()
        code = self._func_to_code(func)
        if not self.connected():
            raise self.ConnectionError()
        self._worker.receive_func(code)

    def call(self, name, *args, **kwargs):
        if not self.connected():
            raise self.ConnectionError() 
        return self.evaluate(
            '%s(%s)'%(
                name,
                ', '.join(
                    [ repr(i) for i in args ]
                    +[ '%s=%r'%(k,v) for k,v in kwargs.items() ]
                )
            )
        )
            
class Workers(object):
    '''
    Manages a list of ClientWorkers.
    '''        
    def __init__(self, apphost):
        self._next_id = 1
        self.apphost = apphost
        self._workers = []
    
    def add_worker(self, worker):
        '''
        Wraps the worker in a ClientWorker
        and store the wrapper.
        Returns the id assigned to the worker.
        '''
        wrapper = ClientWorker(self, worker)
        self._workers.append(wrapper)
        
        worker_id = self._next_id
        self._next_id += 1
        wrapper.set_id(worker_id)
        

        event = Event(
            'HOST', ['Workers'], Event.TYPE.CREATED, worker_id
        )
        self.apphost.emit_app_event(event)

        return worker_id
    
    def changed(self, worker):
        '''
        Called by on the my workers after it changed.
        '''
        event = Event(
            'HOST', ['Workers', worker.get_id()], Event.TYPE.UPDATED, None
        )
        self.apphost.emit_app_event(event)
        
    def get_infos(self, user=None, host=None):
        '''
        Returns a list like [id, {'type':str, 'features':list, 'status':str, 'station_class':str}, ...]

        If user is not None, only the workers of this user are returned.
        If host is not None, only the workers on this host are returned.
        '''
        infos = []
        for w in self._workers:
            w.check_connected()
            if user is not None and w.get_user() != user:
                continue
            if host is not None and w.get_host() != host:
                continue
            worker_id = w.get_id()
            infos.append((
                worker_id, w.get_infos()
            ))
        return infos

    def get(self, worker_id):
        for w in self._workers:
            w.check_connected()
            if w.get_id() == worker_id:
                return w
    
    def drop(self, worker):
        ok = False
        print '###### DROP WORKER', worker
        for w in list(self._workers):
            if w._worker == worker:
                self._workers.remove(w)
                print '   dropped ClientWorker', w
                event = Event(
                    'HOST', ['Workers', w.get_id()], Event.TYPE.DELETED, None
                )
                self.apphost.emit_app_event(event)

        print '    client worker not found :/'

    def drop_disconnected(self):
        print '###### PRUNE WORKERS'
        for w in list(self._workers):
            if not w.check_connected():
                self._workers.remove(w)
                print '   dropped ClientWorker', w
        event = Event(
            'HOST', ['Workers'], Event.TYPE.UPDATED, None
        )
        self.apphost.emit_app_event(event)
        
class AppHost(object):
    def __init__(self, project):
        super(AppHost, self).__init__()
        self._project = project
        self.project_name = project.get_project_name()

        self.station_config = self._project.get_station_config(
            get_station_class()
        )
        self.station_config.apply()
        
        self._clients = set()
        self._workers = Workers(self)
        
        # this event dispatcher let the app
        # connect to others apps events.
        self._event_dispatcher = EventDispatcher()

        self._command_history = CommandHistory(self.on_command_changed)
        
        self._apps = {}
        self._load_apps()
        
    def _load_apps(self):
        # instanciate the apps
        app_refs = self._project.get_settings().APPS
        self._apps = load_apps(app_refs, apphost=self)
        
        # setup the apps
        setting_dir = self.station_config.project_dirs['SETTINGS_DIR']
        for key, app in self._apps.items():
            app.set_event_emitter(self.emit_app_event)
            app._load_settings(key, setting_dir)
        
        for app in self._apps.values():
            app._host_init_done()
    
    def app_keys(self, in_project=False):
        '''
        Returns a list of app keys declared in this
        apphost (or in the project if in_project is True)
        ''' 
        if in_project:
            return self._project.app_keys()
        return self._apps.keys()
        
    def app(self, app_key, in_project=False):
        '''
        Returns the hosted app declared with the given key, or
        None if no such app was declared in the project
        settings.
        '''
        if in_project:
            return self._project.app(app_key)
        return self._apps.get(app_key, None)
    
    def get_commands(self, app_key=None, menu=None):
        '''
        Returns the ui information of the commands in the 
        given app (or all apps) that are present
        in the given menu (or all menus).
        '''
        actions = {}
        for key, app in self._apps.items():
            if app_key is not None and key != app_key:
                continue
            if key not in actions:
                actions[key] = []
            actions[key].extend(
                [
                    a.ui_infos(n) for n, a in app.cmds.iter_commands() 
                    if (menu is None) or menu in a.CMD_MENUS
                ]
            )
        return actions
    
    def get_project_dir(self, dir_name):
        '''
        Returns the path of the project dir 'dir_name'
        as define in the host station_config set by
        the project upon host connection.
        
        The dir_name key must exist in the project
        shape defined in the project settings.
        '''
        return self.station_config.project_dirs[dir_name]
    
    def get_client_python_paths(self):
        return self.station_config.get_python_paths()
    
    def drop_client(self, client):
        print '###### DROP CLIENT', client
        try:
            self._clients.remove(client)
            print '   dropped'
        except:
            print '   client not found'

        # Emit anyway:
        event = Event('HOST', ['Clients'], Event.TYPE.UPDATED, None)
        self.emit_app_event(event)

    def get_workers_infos(self, user=None, host=None):
        '''
        Returns a list like [id, {'type':str, 'features':list}, ...]
        
        If user is not None, only the workers of this user are returned.
        If host is not None, only the workers on this host are returned.
        '''
        return self._workers.get_infos(user, host)
    
    def get_worker(self, worker_id):
        return self._workers.get(worker_id)
    
    def execute_in_worker(self, worker_id, code):
        worker = self.get_worker(worker_id)

        if worker is None:
            raise ValueError('Cannot find a worker with id %r'%(self.worker_id,))
        if not worker.check_connected():
            raise RuntimeError('The worker with id %r is not connected!'%(self.worker_id,))
        
        worker.execute(code)
        
        return

    def eval_in_worker(self, worker_id, code):
        worker = self.get_worker(worker_id)

        if worker is None:
            raise ValueError('Cannot find a worker with id %r'%(self.worker_id,))
        if not worker.check_connected():
            raise RuntimeError('The worker with id %r is not connected!'%(self.worker_id,))
        
        return worker.evaluate(code)
    
    def drop_disconnected_workers(self):
        '''
        Remove all the disconnected workers from
        the worker list.
        '''    
        self._workers.drop_disconnected()
        
    def register_client(self, client):
        print '###### ADDING CLIENT', client
        self._clients.add(client)

        print '#------ CLIENTS:'
        for c in list(self._clients):
            try:
                print '   ', c.ping(), c
            except Exception, err:
                print '   DEAD, droping', c
                print '   ERR was', err
    
    def drop_worker(self, worker):
        self._workers.drop(worker)
        
    def register_worker(self, worker):
        print '###### ADDING WORKER', worker
        self._workers.add_worker(worker)
        print '#------ WORKERS:'
        for w in list(self._workers._workers):
            try:
                print '   ', w.ping(), w
            except Exception, err:
                print '   DEAD, droping', w
                print '   ERR was', err
    
    def find_worker_featuring(self, features):
        ret = None
        for worker in self._workers._workers:
            if worker.has_features(features):
                try:
                    worker.ping()
                except Exception, err:
                    # most likely a communication error
                    # but we are not in ro so we
                    # are not allowed to check it.
                    # we simply drop the worker
                    print 'WORKER ERROR:', err
                    print '!!! We should be dropping this Worker', worker
                    #dead_workers.add(worker)
                else:
                    ret = worker
                    break
        return ret
    
    def get_workers_features(self):
        ret = set()
        for worker in self._workers._workers:
            ret.update(worker.get_features())
        return tuple(ret)
    
    def add_event_handler(self, handler, path, etype=None):
        '''
        This gives each app in the host the opportunity
        to receive events from other apps.
        '''
        self._event_dispatcher.add_handler(
            handler, path, etype
        )

    def emit_app_event(self, event):
#        print '#------------- EMIT APP EVENT'
        # dispatch event to apps first
        self._event_dispatcher.dispatch(event)
    
        # publish to clients if still needed:
        dead_clients = set()
        for c in list(self._clients): # copy since it will be modified if emitting sub-events
            #print '#------- Client', c
            if not event.propagating:
                break
            try:
                #print '#-- client.receive_event call'
                c.receive_event(event)
                #print '#-- client.receive_event done'
            except Exception, err:
                # most likely a communication error
                # but we are not in ro so we
                # are not allowed to check it.
                # we simply drop the client
                print err
                print '!!! Dropping Client', c
                dead_clients.add(c)

        self._clients -= dead_clients

    def do_command(self, app_key, command_name, args, kwargs):
        #print 'AppHost got command %s.cmds.%s(*%r, **%r)'%(app_key, command_name, args, kwargs)
        
        # Get the command to run
        try:
            command = self.app(app_key).cmds.get_command(command_name)
        except Exception, err:
            import traceback
            traceback.print_exc()
            print '  ERROR:', err
            raise
                
        # Run the command and returns the result
        #TODO: clean up command access/execution
        # This is actually a function in the app that
        # instantiates the command, deals with history
        # and executes the command. Kind of convoluted.
        # Should probably be cleaned up.
        return command(*args, **kwargs)
        
    def do_project_command(self, app_key, command_name, *args, **kwargs):
        raise NotImplementedError(
            "Project Apps are not yet functional. (%r)"%((app_key, command_name, args, kwargs),)
        )        
    
    def before_command_run(self, command):
        '''
        Called by the apps when one of their command is about
        to be executed.
        
        Must raise if the command is not allowed.
        (#TODO: define exception for this)
        
        If executed is granted (nothing raised), the apphost 
        command history is updated to contain this new command.
        '''
        created_id, dropped_id  = self._command_history.append(command)
        
        event = Event(
            'HOST', ['CommandHistory'], Event.TYPE.CREATED,
            (created_id, self._command_history.get_entry_infos(created_id))
        )
        self.emit_app_event(event)
        event = Event(
            'HOST', ['CommandEcho'], Event.TYPE.MESSAGE,
            command.script()
        )
        self.emit_app_event(event)
        
        if dropped_id is not None:
            event = Event(
                'HOST', ['CommandHistory'], Event.TYPE.DELETED,
                dropped_id
            )
            self.emit_app_event(event)

    def on_command_changed(self, entry_id):
        '''
        Called by the command history when the state
        of a command has changed.
        This sends an Event with the command updated data.
        '''        
        #TODO: decide if sending only the entry id would be better 
        # It depends on the probability of numerous handler
        # on the CommandHistory events.
        # Since I'm pretty sure that the command history is useless, I won't
        # bother to decide now.
        
        entry_infos = self._command_history.get_entry_infos(entry_id)
        event = Event(
            'HOST', ['CommandHistory'], Event.TYPE.UPDATED,
            (entry_id, entry_infos)
        )
        self.emit_app_event(event)
    
    def get_command_history(self):
        '''
        Returns a list of (entry_id, entry_data) of all
        the command history.
        '''
        return self._command_history.get_entries_infos()
