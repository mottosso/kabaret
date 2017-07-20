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

    The kabaret.core.apps.command package:
        Defines the Arg and Command classes, used to 
        create some App commands.
        
        Also defines the CommandHistory class, used to 
        store a list of command instances.
        
        A Command is defined by subclassing the Command
        class and adding Arg instances as class attributes.
        
        A command class must be associated to an App class 
        in order to be effective. You must use the App's
        cmd.register decorator to do so:

        class MyApp(App):
            ...
        
        MyApp.cmds.register
        class MyCommand(Command):
            arg_1 = Arg()
            ...

        The AppHost holds a CommandHistory which is filled
        up with each Command that it triggers.
        The CommandHistory tells each command it holds that
        they are in a CommandHistory by calling their
        set_in_history() method.
        This makes the Command able to call the CommandHistory's
        on_command_changed() method whenever some state changes
        in them.
        The CommadHistory will then inform the AppHost of such
        change so that it can emit whatever event he wants to 
        broadcast the change.
'''
import weakref

from kabaret.core.utils.ordereddict import OrderedDict


class Arg(object):
    '''
    Represents an argument of a Command.
    
    The 'name' instance attribute will be set by 
    the Command meta class upon Command subclass definition.

    A Command Arg is to be used as a Command class attribute:
    
    class MyCommand(Command):
        first_arg = Arg(label='The First Argument', default=1, ui="int(0,255)")
        second_arg = Arg(label='The Second Argument', default=1, ui="int(0,255)")
        
    The Command will later access its value as an instance attribute:
        def doit(self):
            return self.first_arg * self.second_arg
    '''
    # Ordered Class Attr Trick Part1: this counter ups at each instanciation
    _arg_index = 0 # used by CommandType to make args ordered in class definition
    
    def __init__(self,
        default=None,
        label=None,
        types=None,
        ui=None,
    ):
        '''
        Creates a new Arg.
        The 'label' will default to the Arg name if not given here
        (the Command meta class will set it).
        
        The 'default' argument will be the value of this Arg
        if the Command did not have a value for this Arg in its
        constructor.
        
        The 'types' argument is not yet used but may in the future
        be use to validate that the value of the Arg has a 
        valid type.
        
        The 'ui' argument will be used by UI to provide editor 
        interface.
        '''
        self.index = Arg._arg_index
        Arg._arg_index += 1
        
        self.name = None
        self.label = label
        self.types = types
        self.default = default
        self.ui = ui
    
class CommandType(type):
    '''
    This is the Command meta class.
    It creates an ArgDescriptor for each Arg declared in the
    Command class, stores each Arg in the class attribute '_ARGS'
    and the ordered Arg names in '_ARG_NAMES'.
    
    It sets the Command's UNDOABLE class attribute to True
    if the subclass declares an 'undoit' method.
    
    '''
    def __new__(cls, class_name, bases, class_dict):
        Arg._arg_index = 0 # Ordered Class Attr Trick Part2: reset for each class
        args = {}
        for n, o in class_dict.items():
            if isinstance(o, Arg):
                o.name = n
                if o.label is None:
                    o.label = n
                args[n] = o
                class_dict[n] = ArgDescriptor(n)
        
        class_dict['CMD_NAME'] = class_name
        
        if class_dict.get('CMD_LABEL', None) is None:
            class_dict['CMD_LABEL'] = class_name
        
        class_dict['UNDOABLE'] = False
        if 'undoit' in class_dict and class_name != 'Command':
            class_dict['UNDOABLE'] = True
            
        class_dict['_ARGS'] = args
        class_dict['_ARG_NAMES'] = [ arg.name for arg in sorted(args.values(), cmp=cls.arg_cmp) ]
        command_class = super(CommandType, cls).__new__(cls, class_name, bases, class_dict)
        return command_class

    @staticmethod
    def arg_cmp(a, b):
        '''
        Used to order a list of Arg according to their
        'index' attribute. 
        '''
        return cmp(a.index, b.index)
    
class ArgDescriptor(object):
    '''
    This descriptor lets you access the Command's
    Arg when called from the Command class, and the 
    Arg value when called from one of the Command
    instances.
    '''
    
    
    def __init__(self, name):
        self.name = name
        
    def __get__(self, cmd, cmd_type):
        if cmd is None:
            return cmd_type._ARGS[self.name]
        try:
            return cmd._arg_values[self.name]
        except KeyError:
            return cmd_type._ARGS[self.name].default

class CommandError(Exception):
    '''
    A CommandError is raised when a Command execution
    (its doit() method call) failed.
    '''
    # In order for Pyro to report errors correctly, all
    # exception class must use a single string argument
    # on their constructor :/ 
    # So we use the CommandError.build() class method
    # to format the message.
    def __init__(self, message):
        super(CommandError, self).__init__(message)

    @classmethod
    def build(cls, command, original_error):
        return cls('There was an error in command %r: %s\n(see the AppHost output for the trace.)'%(
                command.script(), original_error,
            )
        )

class Command(object):
    '''
    Base class for all App commands.
    
    One must subclass this class and declare the command
    arguments using Arg instance as class attributes.
    The doit() method must be implemented to execute the 
    command.
    The undoit() method must be implemented for the command
    to be undoable.
    
    class MyCommand(Command):
        first_arg = Arg()
        second_arg = Arg(default=None)
        
        def doit(self):
            if self.second_arg is None:
                return self.first_arg
            return self.first_arg + self.second_arg
            
    
    '''
    __metaclass__ = CommandType

    APP_KEY = '_NO_APP_'    # set by the <App>.cmds.register decorator
    CMD_NAME = None         # set by the metaclass
    
    CMD_TOPICS = []
    CMD_BLOCKS_TOPICS = []
    CMD_LABEL = None
    CMD_MENUS = []
    CMD_ICON = None

    class STATUS:
        INIT = 0
        RUNNING = 1
        ERROR = 2
        CANCEL = 3
        DONE = 4
        
        @classmethod
        def to_str(cls, value):
            return [
                'Initializing', 
                'Running', 
                'Error', 
                'Cancel', 
                'Done', 
            ][value]
            
    def __init__(self, *args, **kwargs):
        '''
        Creates an new instance of this Command.
        The command arguments must match the class'
        Arg attributes.
        '''
        self.app = None
        
        self._arg_values = {}
        for name, arg in zip(self._ARG_NAMES, args):
            if name in kwargs:
                raise TypeError(
                    'Commmand %r got multiple values for argument %r'%(
                        self.__class__.__name__, name
                    )
                )
            self._arg_values[name] = arg
        for name in kwargs.keys():
            if name not in self._ARG_NAMES:
                raise TypeError(
                    'Command %r got an unexpected keyword argument %r'%(
                        self.__class__.__name__, name
                    )
                )
        self._arg_values.update(kwargs)
        
        self._status = self.STATUS.INIT
        self.command_error = None
        
        self._in_history = weakref.WeakKeyDictionary()
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        self._status = value
        for k, v in self._in_history.items():
            k.on_command_changed(v)
            
    @classmethod
    def ui_infos(cls, name=None):
        return {
            'name':name or '_UNKNOWN_CMD_NAME_',
            'topics':cls.CMD_TOPICS,
            'blocks_topics':cls.CMD_BLOCKS_TOPICS,
            'label':cls.CMD_LABEL,
            'menus':cls.CMD_MENUS,
            'icon':cls.CMD_ICON,
        }
    
    @classmethod
    def usage(cls):
        return '%s.cmds.%s(%s)'%(
            cls.APP_KEY, cls.CMD_NAME, 
            ', '.join([ '%s=%r'%(k, v.default) for k, v in cls._ARGS.items() ])
        )
    
    def script(self):
        '''
        Returns a script representation of the command.
        (Ala usage() but with actual arg values)
        '''
        return '%s.cmds.%s(%s)'%(
            self.__class__.APP_KEY, self.__class__.CMD_NAME, 
            ', '.join([ '%s=%r'%(k, v) for k, v in self._arg_values.items() ])
        )
        
#    def get_args(self):
#        return self.__class__._args
#    
#    def get_values(self):
#        return self._values
    
    def run(self):
        '''
        Runs the command, dealing with
        status update and error handling.
        '''
        self.status = self.STATUS.RUNNING
        try:
            ret = self.doit()
        except Exception, err:
            self.status = self.STATUS.ERROR
            self.command_error = CommandError.build(self, err)
            import traceback
            traceback.print_exc()
            raise self.command_error
        else:
            self.status = self.STATUS.DONE
        return ret
    
    def doit(self):
        '''
        Subclasses must override this method so that
        it does the command job and return the command
        result.
        
        Use the instance attributes to get the command 
        arguments:
            def doit(self):
                return self.first_arg * self.first_arg
        
        '''
        raise NotImplementedError
    
    def undoit(self):
        '''
        Subclasses must override this method
        to make the command undoable.
        '''
        raise NotImplementedError

    def set_in_history(self, entry_id, history):
        '''
        Called by a CommandHistory when it wants to
        keep track of this command.
        The Command is then responsible to call
        adequat methods on the history when some of
        its state changes.
        '''
        self._in_history[history] = entry_id

    def unset_in_history(self, history):
        '''
        Called by a CommandHistory that keeps 
        track of this command when it those
        not want to keep keeping track of it :)
        '''
        del self._in_history[history]

class CommandHistory(object):
    '''
    The CommandHistory keep a list of command.
    
    The CommandHistory tells each command it holds that
    they are in a CommandHistory by calling their 
    set_in_history() method.
    This makes the Command able to call the CommandHistory's
    on_command_changed() method whenever some state changes
    in them.
    The CommadHistory will then inform the AppHost of such
    change so that it can emit whatever event he wants to 
    broadcast the change.
    
    A Command is added to a CommandHistory with the append()
    method which return an entry_id (and a dropped_id).
    Each entry in a CommandHistory can give information
    about itself with the get_entry_infos(entry_id) method.
    One can fetch informations about all the entries with
    the get_entries_infos() method.
    
    A CommandHistory will forget about the oldest Commands
    when it reaches the maximum number of entries (30 currently).
    When this happens, the append method will return a non-None
    value in second argument: the entry_id of the Command that
    is no longer held by the CommandHistory.
    
    '''
    
    #TODO: make entries hierarchical so we support macro-commands
    class Entry(object):
        '''
        This internally represents an entry in a CommandHistory.
        The CommandHistory uses the to_dict() method to fetch all
        the informations available for the Command
        of this entry.
        '''
        def __init__(self, command):
            self.command = command
        
        def to_dict(self):
            return {
            'ui_infos': self.command.ui_infos(),
            'script': self.command.script(),
            'doc': self.command.__doc__,
            'app': self.command.app.APP_KEY,
            'status': self.command.status,
            'status_str': self.command.STATUS.to_str(self.command.status)
            }
            
    def __init__(self, on_command_changed=None):
        self._last_id = 0
        self.max_entries = 30
        self._entries = OrderedDict()
        self._on_command_changed = on_command_changed
        
    def _get_new_id(self):
        self._last_id += 1
        return self._last_id
    
    def append(self, command):
        '''
        Returns the id of the new history entry
        and the id of one discared entry (or None)
        '''
        entry_id = self._get_new_id()
        self._entries[entry_id] = self.Entry(command)
        command.set_in_history(entry_id, self)
        droped_id = None
        if len(self._entries) > self.max_entries:
            try:
                droped_id, dropped_entry = self._entries.popitem(0)
            except KeyError:
                print '####==-=-=-=-=-=-=- FUCKED HISTORY...'
            else:
                dropped_entry.command.unset_in_history(self)
        return entry_id, droped_id
    
    def get_entry_infos(self, entry_id):
        '''
        Returns a dict of informations about the
        Command entry having the given entry_id.
        '''
        return self._entries[entry_id].to_dict()
    
    def get_entries_infos(self):
        '''
        Return a dict of {entry_id: entry_infos} with
        all entries in this CommandHistory.
        Each entry_infos is a dict in the form returned
        by get_entry_infos(entry_id)
        '''
        return [ 
            (entry_id, self.get_entry_infos(entry_id))
            for entry_id in self._entries.keys()
        ]
        
    def on_command_changed(self, entry_id):
        '''
        Called by a command knowing to be in this history
        when its state changes.
        '''
        if self._on_command_changed is not None:
            self._on_command_changed(entry_id)




if __name__ == '__main__':
    class TestCmd(Command):
        name = Arg(default='DEFAULT')
        value = Arg()
        value2 = Arg()
        value3 = Arg()
        value4 = Arg()
        
        def doit(self):
            print "Doing TestCmd(%r, %r)"%(self.name, self.value)
            return self.name, self.value
        
        def undoit(self):
            print "UnDoing TestCmd(%r, %r)"%(self.name, self.value)
            return self.value, self.name 

    class TestCmd2(Command):
        value5 = Arg()

    for arg in TestCmd2._ARGS.values():
        print arg, arg.name, arg.index
        
    cmd = TestCmd(app=None)
    assert cmd.doit() == ('DEFAULT', None)
    assert cmd.undoit() == (None, 'DEFAULT')

    cmd = TestCmd(None, value=12)
    print cmd.doit()
    assert cmd.doit() == (None, 12)
    assert cmd.undoit() == (12, None)
    
    cmd = TestCmd(value=12)
    print cmd.doit()
    assert cmd.doit() == ('DEFAULT', 12)
    assert cmd.undoit() == (12, 'DEFAULT')

        