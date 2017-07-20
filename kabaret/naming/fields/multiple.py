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
    The kabaret.naming.fields.multiple module.
    
'''

from .field import Field,FieldError


class MultipleFields(Field):
    field_type = Field
    separator = '_'
    
    def __init__(self, parent):
        super(MultipleFields, self).__init__(parent)
        self._fields = []

    def pformat(self, indent=0, ns=''):
        ret = [super(MultipleFields, self).pformat(indent, ns)+' (MultipleFields<%s>)'%(self.field_type.key)]
        for i, f in enumerate(self._fields):
            ret.append(
                '    '*(indent+1)+'[%i]=%r'%(i, f.value())
            )
        return '\n'.join(ret)

    def forbidden_chars(self):    
        return self._parent.forbidden_chars() + self.separator

    def has_value(self):
        if self.optional and not self._fields:
            return False
        return True

    def __getitem__(self, index):
        return self._fields[index]
    
    def value(self):
        return self.separator.join([ str(f.value()) for f in self._fields ])

    def _append_field(self, value):
        index = len(self._fields)
        field = self.field_type(self)
        field.key_override = '%s_%i'%(field.key, index)
        field.set_value(value) # may raise FieldValueError
        self._fields.append(field)
        
    def set_value(self, value):
        if self._fields:
            raise FieldError('The field %r is already set'%(self.key,))
        values = value.split(self.separator)
        for field_value in values:
            self._append_field(field_value)
