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
    The kabaret.naming.fields.compound module.
    
'''

from .field import FieldType, Field, FieldValueError


class CompoundFieldType(FieldType):
    def __new__(cls, class_name, bases, class_dict):
        # Build the field descriptors:
        fields = class_dict.get('fields', [])
        for field in fields:
            key = field.key
            if key in class_dict:
                #TODO: look into bases too...
                raise Exception(
                    'field key %r clashes for CoumpoundField class %r (%r)'%(
                        key, class_name, class_dict[key]
                    )
                )  
            class_dict[key] = FieldDescriptor(key)
                    
        # create and return the final class
        return  super(CompoundFieldType, cls).__new__(cls, class_name, bases, class_dict)

class FieldDescriptor(object):
    def __init__(self, key):
        self.key = key
    
    def __get__(self, field, field_class):
        return field._fields[self.key]
    
class CompoundField(Field):
    __metaclass__ = CompoundFieldType
    
    fields = []
    separator = '-'
    shadow_fields = False
    
    def __init__(self, parent):
        super(CompoundField, self).__init__(parent)
        self._fields = {}

    def pformat(self, indent=0, ns=''):
        ret = [super(CompoundField, self).pformat(indent, ns)+' (Compound sep=%r)'%self.separator]
        for f in self.fields:
            ret.append(self._fields[f.key].pformat(indent, ns+self.key+'.'))
        return '\n'.join(ret)

    def forbidden_chars(self):    
        return self._parent.forbidden_chars() + self.separator
    
    def value(self):
        if not self.fields:
            return super(CompoundField, self).value()
        
        if not self._fields:
            return '???' # not set yet
        
        values = []
        for field_type in self.fields:
            field = self._fields[field_type.key]
            if not field.has_value():
                continue
            values.append(field.value())
        return self.separator.join(values)

    def set_value(self, value):
        if not self.fields:
            return super(CompoundField, self).set_value(value)
        
        values = value.split(self.separator)
        for field_type in self.fields:
            field, values = field_type.consume_value(self, values)
            self._fields[field.key] = field
            
        if values:
            raise FieldValueError(
                'Values %r not consumed from %r'%(values, value)
            )

    def config(self):
        if not self.fields or self.shadow_fields:
            return super(CompoundField, self).config()
        
        config = {}
        for field in self._fields.values():
            config.update(field.config())
        
        return config

    @classmethod
    def get_config_keys(cls):
        '''
        Return a set of all the keys
        needed in this Field config.
        '''
        if not cls.fields or cls.shadow_fields:
            return super(CompoundField, self).get_config_keys()
        
        ret = []
        for field_type in cls.fields:
            ret.extend(field_type.get_config_keys())
        return ret

    def set_config(self, config, allowed_index=None):
        if not self.fields:
            return super(CompoundField, self).set_config(config, allowed_index)

        consumed_keys = set()
        for field_type in self.fields:
            field, key_set = field_type.consume_config(self, config)
            self._fields[field.key] = field
            consumed_keys.update(key_set)
        
        return consumed_keys
