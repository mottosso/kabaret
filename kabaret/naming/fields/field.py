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
    The kabaret.naming.fields.field module.
    
'''


class FieldError(ValueError):
    pass

class FieldValueError(FieldError):
    pass

class FieldConfigError(FieldError):
    pass


class FieldKeyDescriptor(object):
    def __get__(self, field, field_type):
        if field is None:
            return field_type.KEY
        return field.key_override or field_type.KEY
    
class FieldType(type):
    def __new__(cls, class_name, bases, class_dict):
        if bases != (object,):
            # this is not the 'Field' class definition
            # Check 'key' name is not used (so that the 
            # FieldKeyDescriptor is not overridden):
            if 'key' in class_dict:
                raise ValueError(
                    "You cannot override the 'key' when subclassing Field"
                )
            # Set default KEY and check it:
            key = class_dict.get('KEY', class_name)
            if key is not None and Field._key_index_sep in key:
                raise ValueError(
                    'The key %r is not valid: should not contain %r.'%(
                        key, Field._key_index_sep
                    )
                )
            reserved_keywords = ('verbose', 'debug')
            if key in reserved_keywords:
                raise ValueError(
                    'The key %r is not valid: it is one of the reserved keywords %r.'%(
                        key, reserved_keywords
                    )
                )
                
            class_dict['KEY'] = key
        else:
            # this is only executed when defining the 'Field' class
            class_dict['key'] = FieldKeyDescriptor()
        return  super(FieldType, cls).__new__(cls, class_name, bases, class_dict)

class Field(object):
    '''
    The Field is used to validate a string to use as a kabaret.naming.path.PathItem name.
    
    A Field class has a 'KEY' attribute that defines the key to generate or to consume in 
    a config.
    If the KEY class attribute is None (the default), the name of the class will be used.
    
    A Field is optional when the class attribute 'optional' is True.
    
    You define the Field used in your naming convention by subclassing the Field (or one
    of its convenient subclasses).
    ::
        Class Basename(kabaret.naming.fields.field.Field):
            KEY = 'base'
            optional = False
        
        class Ext(kabaret.naming.fields.field.Field):
            KEY = 'extension'
            optional = True
    
    See the subclasses for specialized Fields.
    '''
    __metaclass__ = FieldType
    
    KEY = None
    optional = False
    
    _key_index_sep = '@'
    
    @classmethod
    def make_indexed_key(cls, key, index):
        key, _old_index = cls.get_key_index(key) 
        return '%s%s%i'%(key, cls._key_index_sep, index)
    
    @classmethod
    def get_key_index(cls, key):
        if cls._key_index_sep in key:
            key, index = key.split(cls._key_index_sep, 1)
            return key, index
        return key, None
    
    def __init__(self, parent):
        self._path = None      
        self._parent = None
        self._value = None
    
        self.key_override = None
    
    def pformat(self, indent=0, ns=''):
        return '    '*indent+ns+'%s=%r'%(self.key, self.value())

    def __str__(self):
        return '<%s.%s %s:%r>'%(self.__module__, self.__class__.__name__, self.key, self.value())

    def forbidden_chars(self):
        if self._parent is None:
            return '' 
        return self._parent.forbidden_chars()

    def root_field(self):
        if self._parent is None:
            return self
        return self._parent.root_field()
    
    def path(self):
        return self.root_field()._path
    
    def value(self):
        return self._value
    
    def has_value(self):
        if self.optional and self._value is None:
            return False
        return True
    
    def set_value(self, value):
        if self._value is not None:
            raise FieldError('The field %r is already set'%(self.key,))
        self._value = value
        self.validate() # raise 
        self._after_set_value()
    
    def set_config(self, config, allowed_index=None):
        key = self.key
        
        # First try key w/o index:
        try:
            self.set_value(config[self.key])
        except KeyError:
            if allowed_index is None:
                raise FieldConfigError(
                    'Could not find %r in config %r'%(
                        key, config
                    )
                )
        else:
            return set([key])
        
        # If allowed, try indexed key:
        key = self.make_indexed_key(key, allowed_index)
        try:
            self.set_value(config[key])
        except KeyError:
            raise FieldConfigError(
                'Could not find %r or %r in config %r'%(
                    self.key, key, config
                )
            )
        else:
            return set([key])
        
            
    def _after_set_value(self):
        pass
    
    @classmethod
    def consume_value(cls, parent, values):
        if not values and not cls.optional:
            raise FieldValueError('Missing value for field %r'%(cls.key,))
            
        field = cls(parent)
        if not values:
            return field, values

        try:
            field.set_value(values[0])
        except FieldValueError:
            if cls.optional:
                return field, values
            raise
        return field, values[1:]
    
    @classmethod
    def consume_config(cls, parent, config):
        field = cls(parent)
        try:
            key_set = field.set_config(config)
        except FieldConfigError:
            if cls.optional:
                return field, set()
            raise
        return field, key_set
    
    def validate(self):
        for c in self.forbidden_chars():
            if c in self._value:
                raise FieldValueError(
                    'Value %r is not invalid for %r: forbidden character %s found.'%(
                        self._value, self.key, c
                    )
                )

    def config(self):
        key = self.key
        if key is None:
            return {}
        return {key: self.value()}

    @classmethod
    def get_config_keys(cls):
        '''
        Return a (somehow ordered) list of 
        all the keys needed in this Field config.
        '''
        if cls.key is None:
            return []
        return [cls.key]
