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

    The kabaret.core.conf package:
        Defines the Config class used to read
        config data from a python syntax file.
        
        See Config's documentation
    
'''

import os
import pprint 

class ConfigError(Exception):
    pass

class ConfigMissingError(Exception):
    def __init__(self, filename):
        super(ConfigMissingError, self).__init__(
            'Config file %r not found'%(filename,)
        )
        self.filename = filename



class Attribute(object):
    '''
    An Attribute is used to hold a value in a Config.
    '''
    
    def __init__(self, default_value, description=None, allowed_types=None):
        super(Attribute, self).__init__()
        self.default_value = default_value
        self.value = default_value
        self.description = description
        self.allowed_types = allowed_types
    
    def assert_allowed(self, value):
        if self.allowed_types is not None and not isinstance(value, self.allowed_types):
            raise ValueError('should be instance of %r'%(self.allowed_types,))
        
    def set(self, value):
        if value is None:
            self.reset()
            return 
        self.assert_allowed(value)
        self.value = value
    
    def get(self):
        return self.value
    
    def reset(self):
        self.value = self.default_value

    def pformat(self, indent=0):
        if hasattr(self.value, 'pformat'):
            value_str = self.value.pformat(indent+1)
        else:
            value_str = pprint.pformat(self.value, indent=indent)
        return '='+value_str

    def to_script(self, namespace):
        if hasattr(self.value, 'to_script'):
            value_str = self.value.to_script(namespace)
        else:
            value_str = namespace+' = '+pprint.pformat(self.value)
        if self.description:
            one_liner = ' '.join(i.strip() for i in self.description.split('\n'))
            value_str = '%-40s # %s'%(value_str,one_liner)
        return value_str
        
class Group(object):
    '''
    A Group is used to hold some Attribute or Group
    in a Config.
    '''
    def __init__(self, description, **subs):
        super(Group, self).__init__()
        self._description = description
        self._locked_structure = True
        self._subs = {}
        for k, v in subs.items():
            if isinstance(v, (Attribute,Group)):
                self._subs[k] = v
            else:
                self._subs[k] = Attribute(v)

    def get(self):
        return self
    
    def set(self, value):
        raise AttributeError('Cannot set a Group.')
    
    def __getattr__(self, name):
        # This is called if the attribute 'name' was
        # not found.
        if name.startswith('__'):
            # We need to prevent pickle
            # to think we have a __setstate__
            # method.
            raise AttributeError('%r object has no attribute %r'%(self.__class__.__name__,name))
        
        try:
            sub = self._subs[name]
            return sub.get()
        except KeyError:
            raise AttributeError('Value not found: %r'%(name,))

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super(Group, self).__setattr__(name, value)
        
        if isinstance(value, (Attribute,Group)):
            if self._locked_structure:
                raise AttributeError('Cannot change attribute or group (%r)'%(name,))
            self._subs[name] = value
            return
        
        attr = self._subs.get(name)
        if attr is None:
            raise AttributeError('No such config attribute %r'%(name,))
        
        try:
            attr.set(value)
        except ValueError, err:
            raise ValueError('Bad %r for %r: %s'%(type(value), name, err))
        
    def pformat(self, indent=0):
        ret = indent and ['('] or []
        for name in sorted(self._subs.keys()):
            value = self._subs[name]
            if hasattr(value, 'pformat'):
                value_str = value.pformat(indent+1)
            else:
                value_str = repr(value)
            ret.append(''.join(('  '*indent, name, value_str)))
        if indent:
            ret.append('  '*(indent-1)+')')
        return '\n'.join(ret)
    
    def to_script(self, namespace=''):
        ret = self._description and ['','#']+[
            '# '+i.strip()
            for i in self._description.split('\n')
        ]+['#'] or ['#']
        if not namespace:
            ret += ['']
        for name in sorted(self._subs.keys()):
            value = self._subs[name]
            this_namespace = namespace and namespace+'.'+name or name
            if hasattr(value, 'to_script'):
                value_str = value.to_script(this_namespace)
            else:
                value_str = this_namespace+' = '+repr(value)
            ret.append(value_str)
        ret.append('')
        return '\n'.join(ret)
        
class Config(Group):
    '''
    A Config defines a finite list of attributes.
    The attribute values can be loaded from a 
    python-like file.
    
    You create a config by subclassing this class
    and declare attributes with default values, 
    description, type checking in _define()
    
    Application can then instantiate the config class
    and load the value from a file.
    If the file does not follow the config structure
    (attributes and group names and types), exceptions
    will be raised (AttributeError or ValueError)

    Subclassing a Config will inherit the base's
    Attributes if you call the base's _define()
    in your overridden _define()
    
    You can pretty print a Config using the pformat()
    method.
    You can save the config to a file for later load,
    but you should refrain yourself from doing for more
    than config initialization since it would defeat 
    the purpose of all this: allowing the user to use 
    python code in his config files.
    
    Example of Config definition:
    
        class MyConfig(Config):
            """
            This docstring is the description
            of the config and may be presented
            to the end user.
            """
            def _define(self):
                super(MyConfig, self)._define()
                self.OPTION_GROUP = Group(
                    'A Group Of Related Options',
                    allow_beer = True,
                    allow_wine = False,
                )
                self.ANOTHER_OPTION = 'the interesting value'
                self.NB = Attribute(1, 'The number of glasses', int)
    
    Example of config file for MyConfig:
    
        # This is my own personal config.
        import utils
        
        today = utils.get_today()
        max = 12
        
        if today == 'Saturday':
            OPTION_GROUP.allow_beer = True
            NB = max
        else:
            OPTION_GROUP.allow_beer = False
        
        if is_mom_birthday(today):
            NB = None # (revert to default value)
            
    Example of MyConfig usage:
    
        conf = MyConfig()
        conf.load('path/to/user.conf')
        if conf.OPTION_GROUP.allow_beer:
            for i in range(conf.NB):
                drink_beer()
                
    '''
    EXTRA_CONTEXT = {}
    
    def __init__(self):
        super(Config, self).__init__(description=self.__class__.__doc__)
        self._locked_structure = False
        self._define()
        self._locked_structure = True
    
    def _define(self):
        raise NotImplementedError
    
    def save(self, filename, do_backup=True):
        if do_backup:
            if os.path.exists(filename):
                i = 1
                bak_name = '%s.old_%03i'%(filename, i)
                while os.path.exists(bak_name):
                    i += 1
                    bak_name = '%s_%i.old'%(filename, i)
                os.rename(filename, bak_name)
            
        with open(filename, 'w') as w:
            w.write(self.to_script())
            w.write('\n\n')

    def load(self, filename, **context):
        '''
        Load the values from the given filename.
        
        The context provides global value in the 
        execution of the file.
        '''
        if not os.path.isfile(filename):
            raise ConfigMissingError(filename)
        
        context.update(self.EXTRA_CONTEXT)
        
        subs = self._subs.copy()
        try:
            execfile(filename, context, subs)
        except Exception, err:
            import traceback
            traceback.print_exc()
            raise ConfigError('Error reading config: %s'%(err,))
        
        for k, v in subs.items():
            s = self._subs.get(k)
            if s is None:
                # just skip defined names
                continue
            if s != v:
                # affect known attributes
                setattr(self, k, v)



if __name__ == '__main__':
    class MyConfig(Config):
        '''This is the config description.
        
        It is used in the to_script meth.
        '''
        
        def _define(self):
            self.GROUP_A = Group(
                'description of group A',
                VALUE_A='test AA',
                VALUE_B='test AB',
            )
            
            self.GROUP_B = Group(
                '''
                Big description
                in multiple lines
                for the group B
                ''',
                A_VALUE_A='test BA',
                A_VALUE_B=Attribute('test BB', 'The value test BB', str),
                SUB_GROUP = Group(
                    'A Group in another group?',
                    v1 = 1,
                    v2 = 2
                )
            )
                
            self.VALUE_A = Attribute(21, 'The value A', int)
            self.VALUE_B = Attribute(12, 'The value B')

    config = MyConfig()
    print config.pformat()
    config.load(__file__+'/../test_config')
    print config.to_script()
