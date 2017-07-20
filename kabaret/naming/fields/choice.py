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
    The kabaret.naming.fields.choice module.
    
'''

from .field import Field, FieldValueError

class ChoiceField(Field):
    choices = []
    allow_None = False
    
    def pformat(self, indent=0, ns=''):
        return super(ChoiceField, self).pformat(indent, ns)+' (Choices: %r)'%(self.choices,)

    def validate(self):
        super(ChoiceField, self).validate()
        if self._value is None and self.allow_None:
            return
        if self._value not in self.choices:
            raise FieldValueError(
                'Value %r is invalid for %r: should be one of %r'%(
                    self._value, self.key, self.choices
                )
            )
