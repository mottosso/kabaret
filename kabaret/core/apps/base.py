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

    The kabaret.core.apps.base package:
        Defines the App abstract class.

        An App purpose is to encapsulate a concept so that you can
        switch it from a project to another one.
        
        It can use setting stored in the project.
        It defines some Commands that can be triggered from clients
        and can register to Events.
        
        An App has a str class attribute 'APP_KEY' use to weakly
        type it.
        The AppHost uses it to route client commands to the 
        corresponding app.
        
        An app can access other apps if it has specified the
        dependency in its REQ_APPS class attribute:
        
        class MyApp(App):
            APP_KEY = 'MY_APP_KEY'
            REQ_APPS = ['OTHER_APP_KEY']
            
            my_app.OTHER_APP_KEY.some_command(some_arg='some_value')


'''
import inspect 

from kabaret.core import conf
from .command import Command

class LinkedAppError(Exception):
    pass

class AppType(type):
    '''
    App class type.
    
    Validates the APP_KEY attribute of the App subclass.
    Adds a ReqAppDescriptor for each required app.
    Ensure the App.cmds class attribute is an empty 
    CommandCollection instance.
    
    '''
    def __new__(cls, class_name, bases, class_dict):
        if bases != (object,):
            # validate the app key
            APP_KEY = class_dict.get('APP_KEY', None)
            if not APP_KEY:
                for base in bases:
                    base_app_key = getattr(base, 'APP_KEY', None)
                    if base_app_key and APP_KEY:
                        raise AttributeError( 
                            'Multiple APP_KEY found in App base classes: %r'%(
                                bases
                            )
                        )
                    APP_KEY = base_app_key
            if not isinstance(APP_KEY, basestring):
                raise AttributeError(
                    'Invalid APP_KEY %r for App %r'%(
                        APP_KEY, class_name
                    )
                )
            class_dict['APP_KEY'] = APP_KEY
        
        # Build the REQ_APPS descriptors:
        req_app_descriptors = {}
        req_app_keys = class_dict.get('REQ_APPS', [])
        for app_key in req_app_keys:
            if app_key in class_dict:
                #TODO: also lookup bases attributes
                raise LinkedAppError(
                    "Cannot link to app %r: a class attribute has this name"%(
                        app_key
                    )
                )
            req_app_descriptors[app_key] = ReqAppDescriptor(app_key)
            
#        # Build api
#        commands = {}
#        for n, o in class_dict.items():
#            #print class_name, n
#            #print '   ', o, dir(o)
#            if inspect.isclass(o) and issubclass(o, Command):
#                class_dict[n] = cls.make_command_func(n, o)
#                commands[n] = o
        
        # Reset the command collection for each class:
        if bases != (object,):
            if 'cmds' in class_dict:
                raise AttributeError(
                    'The \'cmds\' class attribute is reserved, '
                    'cannot use it to store %r'%(
                        class_dict['cmds'],
                    )
                )
            class_dict['cmds'] = CommandCollection(APP_KEY)

        # augment the class_dict
        class_dict.update(req_app_descriptors)
#        class_dict['_commands'] = commands
        
        # now create the class
        app_class = super(AppType, cls).__new__(cls, class_name, bases, class_dict)
        return app_class

#    @staticmethod
#    def make_command_func(name, cmd_class):
#        def trigger_app_command(app, *args, **kwargs):
##            if args:
##                raise TypeError(
##                    'Command must use keyword arguments!\n  %s\n  got: %s, %s,'%(
##                        cmd_class.usage(), args, kwargs
##                    )
##                )
#            try:
#                cmd = cmd_class(*args, **kwargs)
#            except TypeError, err:
#                message = err.message+'\n  %s\n  got:'%(cmd_class.usage(), kwargs)
#                raise TypeError(message)
#            else:
#                cmd.app = app
#            
#            # Deal with authorization and command history
#            app.host.before_command_run(cmd)
#            
#            # Run the command
#            ret = cmd.run()
#            return ret
#        
#        return trigger_app_command
    
#class API(object):
#    def __init__(self, actions):#, menus):
#        super(API, self).__init__()
#        self.actions = actions
#        #self.menus = menus
#    
##    def to_dict(self):
##        return {
##            'actions':[a.to_dict() for a in self.actions ],
##            #'menus':[m.to_dict() for m in self.menus ],
##        }
##    
##    def from_dict(self, d):
##        self.actions = [ AppAction.from_dict(ad) for ad in d['actions'] ]
#    
#    def get_menus(self):
#        all_names = []
#        [ all_names.extend(a.menus) for a in self.actions.values() ]
#        return set(all_names)
#    
#    def get_actions(self, menu, blocked_topics=[]):
#        '''
#        Return all the actions of the requested menus
#        with topic not listed in blocked_topics.
#        
#        If menu is None, all menus are returned.
#        '''
#        return [
#            a for a in self.actions.values()
#            if (menu is None or menu in a.menus) and not [ True for t in a.topics if t in blocked_topics ]
#        ]
            
class ReqAppDescriptor(object):
    def __init__(self, app_key):
        super(ReqAppDescriptor, self).__init__()
        self.app_key = app_key
    
    def __get__(self, app, apptype):
        if app is None:
            raise UnboundLocalError('Cannot get req app without app instance')
        if self.app_key not in app._req_apps:
            req_app = app.host.app(self.app_key)
            if req_app is None:
                raise LinkedAppError(
                    'Cannot find app %r required by app %r'%(
                        self.app_key, app.APP_KEY
                    )
                )
            return req_app

#class AppAction(object):
#    def __init__(self, name=None, topics=[], blocking_for=[], label=None, menus=[], icon=None):
#        self.name = name
#        self.topics = topics
#        self.blocking_for = blocking_for
#        self.label = label
#        self.menus = menus
#        self.icon = icon
#    
#    def to_dict(self):
#        return {
#            'name':self.name,
#            'topics':self.topics,
#            'blocking_for':self.blocking_for,
#            'label':self.label,
#            'menus':self.menus,
#            'icon':self.icon,
#        }
#    
#    @classmethod
#    def from_dict(cls, d):
#        return cls(**d)

#class AppActionMenu(object):
#    def __init__(self, name):
#        self.name = name
#        self.actions = []

class CommandTrigger(object):
    '''
    A CommandTrigger is a callable that will
    run an instanced of the given Command class
    in the given App.
    '''
    def __init__(self, app, command_class):
        super(CommandTrigger, self).__init__()
        self._app = app
        self._command_class = command_class
    
    def __call__(self, *args, **kwargs):
        try:
            command = self._command_class(*args, **kwargs)
        except TypeError, err:
            message = err.message+'\n  %s\n  got:  %r'%(self._command_class.usage(), kwargs)
            raise TypeError(message)
        else:
            command.app = self._app
        
        # Deal with authorization, command echo and command history
        self._app.host.before_command_run(command)
        
        # Run the command
        ret = command.run()
        return ret

class CommandGetter(object):
    '''
    A CommandGetter is a namespace of CommandTrigger 
    for a given App instance.
    '''
    def __init__(self, app, command_collection):
        self._app = app
        self._command_collection = command_collection
        self._triggers = {}
    
    def get_command(self, command_name):
        '''
        Returns a CommandTrigger for the Command class
        named 'command_name'.
        The Command class must be registered to this
        CommandGetter's command_collection.
        
        On the fist call for a given command_name, the 
        CommandTrigger is created.
        Further calls with the same command_name will
        return this CommandTrigger.
        '''
        try:
            return self._triggers[command_name]
        except KeyError:
            pass
        
        try:
            command_class = self._command_collection.get_command(command_name)
        except KeyError:
            raise AttributeError(
                'The App %r does not have a %r command'%(
                    self._app, command_name
                )
            )
        trigger = CommandTrigger(self._app, command_class)
        self._triggers[command_name] = trigger
        return trigger

    def iter_commands(self):
        '''
        Iterates on each (command_name, command_class)
        registered in this CommandGetter's command_collection.
        '''
        return self._command_collection._commands.iteritems()
    
    def __getattr__(self, command_name):
        '''
        x.command_name <=> x.get_command(command_name)
        '''
        return self.get_command(command_name)
    
class CommandCollection(object):
    '''
    A CommandCollection stores Command classes 
    associated with an App.
    It is used as a namespace for the stored commands.
    
    It must be used as a Descriptor on an App subclass.
    '''
    def __init__(self, app_key):
        super(CommandCollection, self).__init__()
        self.app_key = app_key
        self._commands = {}
    
    def register(self, command_class):
        '''
        Registers a command to this collection.
        Use it as a descriptor on the Command subclasses:
        
        @MyApp.cmds.register
        class MyCommand(Command):
            ...
            
        '''
        name = command_class.CMD_NAME
        if name in self._commands:
            raise self.Error(
                'A Command %r is already registered to App %r'%(
                    name, self.app
                )
            )
        command_class.APP_KEY = self.app_key
        self._commands[name] = command_class

    def get_command(self, name):
        '''
        Returns the command registered as 'name'.
        Raises a KeyError if the name is not associated
        with a command.
        '''
        return self._commands[name]
    
    def __get__(self, app, app_type):
        '''
        Returns self when call on an App class:
            MyApp.cmds <=> MyApp.cmds
            
        Returns the App instance's CommandGetter (creating
        it if not done yet) when called on an App
        instance:
            my_app.cmds <=> my_app._command_getter
            
        '''
        if app is None:
            return self
        if app._command_getter is None:
            app._command_getter = CommandGetter(app, self)
        return app._command_getter

class App(object):
    '''
    An App defines a set of commands usable in the context
    of a project.
    
    Is has a unique APP_KEY (class attribute)

    Each class defines a REQ_APPS list containing the 
    keys of other apps that are required (used) by this one.
    In the App instance, those required App will be accessible
    thru the attribute named like the required app key, i.e:
        class MyApp(App):
            REQ_APPS = ['BACKEND']
        ...
        app = MyApp(host)
        app.BACKEND.get_infos()
        
    All apps of a project are instantiated at startup time
    so you should avoid doing much in the app constructor.
    It is a good practice to init your class attributes
    with None and only load them at the first access
    (or after some kind of cache flush)
    
    
    '''
    __metaclass__ = AppType
#    _api = None
    
    APP_KEY = None
    REQ_APPS = []

    cmds = CommandCollection(None) # this is here just for code completion, subclasses will have it reseted by the metaclass
    
#    @staticmethod
#    def action(name=None, topics=[], blocking_for=[], label=None, menus=[], icon=None):
#        '''
#        Make a method of an App available to remote users and in GUI Menus.
#        
#        '''
#        action = AppAction(name, topics, blocking_for, label, menus, icon)
#        def action_decorator(decorable, action=action):
#            decorable._kabaret_action = action
#            if action.name is None:
#                action.name = decorable.func_name
#            return decorable
#        return action_decorator
#    
#    @staticmethod
#    def query(name=None, topics=[], blocking_for=[], label=None, menus=[], icon=None):
#        '''
#        Make a method of an App available to remote users and in GUI Menus.
#        
#        '''
#        #TMP:
#        return App.action(name, topics, blocking_for, label, menus, icon)
#    
#        action = AppAction(name, topics, blocking_for, label, menus, icon)
#        def query_decorator(decorable, action=action):
#            decorable._kabaret_query = action
#            if action.name is None:
#                action.name = decorable.func_name
#            return decorable
#        return query_decorator
        
    def __init__(self, host):
        '''
        Instantiates the App in the 'host' AppHost.
        The host is responsible for the App instantiation,
        you should not create App yourself.
        The host will configure the App right after its
        creation by calling appropriate methods (set_event_emitter,
        set_event_handler_adder, ...)
        
        The App keys declared in the REQ_APPS class attribute
        will be accessible with attribute named with each APP_KEY:
            class MyApp(App):
                REQ_APPS = [OTHER_APP]
            
            my_app = MyApp(host)
            my_app.OTHER_APP.do_something()
        
        Commands registered with the App are accessible in 
        the 'cmds' attribute:
            @MyApp.cmds.register
            class DoSomething(Command):
                def doit(self):
                    ...
            
            my_app.cmds.DoSomething()
            
        '''
        super(App, self).__init__()
        
        self._command_getter = None # will be a CommandGetter, set by CommandCollection on first access.
        
        self.host = host
        self._req_apps = {}  # api_key -> app instance
        
        self._event_emitter = None
        self._event_handler_adder = None
        
    def set_event_emitter(self, callable):
        '''
        Called by the host supporting this app.
        Calls to emit_event previous to a call
        to this method will have no effect and will
        be silently ignored.
        
        In particular, this means you cannot emit
        events in the App __init__ method.
        You should wait for the App to be configured before
        emiting events. The _host_init_done method is
        a good place if you need to emit event asap.
        '''        
        self._event_emitter = callable
    
    def emit_event(self, event):
        '''
        Emits an app event.
        
        The event will be received by apps or
        clients views that registered themself for a matching
        event.
        
        Beware that you cannot emit events before the
        app is configured by its host. 
        (see set_event_emitter() for details)
        '''
        if self._event_emitter is not None:
            self._event_emitter(event)
    
    def set_event_handler_adder(self, callable):
        '''
        Called by the host supporting this app.
        Calls to add_app_event_handler previous to a call
        to this method will raise a RuntimeError.
        
        In particular, this means you cannot register to
        some events in the App __init__ method.
        You should wait for the App to be configured before
        registering event handlers. The _host_init_done method is
        a good place to do it.
        '''
        self._event_handler_adder = callable
    
    def add_app_event_handler(self, handler, path, etype):
        '''
        Registers an event handler for the given path and 
        etype.

        Beware that you cannot register event hanlders before 
        the app is configured by its host. 
        (see set_event_handler_adder() for details)
        '''
        if self._event_handler_adder is None:
            raise RuntimeError('No app event handler adder was defined')
        self._event_handler_adder(handler, path, etype)

    def _load_settings(self, key, path):
        '''
        Tells the application to load the settings 
        in the folder 'path'.
        You must override _load_settings and not
        this one to let your App configure itself. #TODO: this comment make no sens.
        '''
        print '#--- LOADING APP SETTINGS', self.APP_KEY
        settings_class = self._get_setting_class()
        settings_context = self._get_setting_context()
        if settings_class is None:
            self._apply_settings(None)
            return
        settings = settings_class()
        settings_file = '%s/%s.kbr'%(path, key)
        try:
            settings.load(settings_file, **settings_context)
        except conf.ConfigMissingError:
            # Save the default config so that
            # admin users can edit it.
            settings.save(settings_file)
            
        except conf.ConfigError:
            import traceback
            traceback.print_exc()
            # using default settings.
            pass
        
        self._apply_settings(settings)
        
    def _get_setting_context(self):
        '''
        Returns the context to use when
        reading the settings file.
        See kabaret.core.conf.Config.load()
        
        The default implementation returns
        an empty dict.
        '''
        return {}
    
    def _get_setting_class(self):
        '''
        Returns the class to use for the App
        settings.
        The returned class must be a sub-class
        of kabaret.core.conf.Config that does
        not need argument in its constructor.
        
        If the App does not save/read settings, 
        None should be returned (which is the 
        default behavior)
        
        '''
        return None
    
    def _apply_settings(self, settings):
        '''
        Called when the App settings are ready to 
        be applied.
        
        If the class does not use settings (by
        overriding _get_settings_class), the 
        settings argument will be None
        
        The default implementation does
        nothing.
        '''
        pass

    def _host_init_done(self):
        '''
        Called when the AppHost has finished
        loading all apps.
        You can use this placeholder to do 
        app initialization that rely on other
        applications.
        
        As all apps are created before the AppHost
        calls this, you can safely emit event or register
        event handlers here.
        But you cannot be sure that required apps have already
        set up their event handler.
        
        The default implementation does nothing.
        '''
        pass
    
    

        