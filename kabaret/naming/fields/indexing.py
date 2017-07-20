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
    The kabaret.naming.fields.indexing module.
    
'''

from .field import Field, FieldValueError


class IndexingField(Field):
    prefix = 'PREFIX'
    padding = '#'

    def pformat(self, indent=0, ns=''):
        return super(IndexingField, self).pformat(indent, ns)+' (Indexed %s<%s>)'%(self.prefix, 'x'*len(self.padding))

    def validate(self):
        super(IndexingField, self).validate()
        if not self._value.startswith(self.prefix):
            raise FieldValueError(
                'Value %r is invalid for %r: missing prefix %r.'%(
                    self._value, self.key, self.prefix
                )
            )
        
        rest = self._value[len(self.prefix):]
        if not rest.isdigit():
            raise FieldValueError(
                'Value %r is not invalid for %r: index %r is not digit.'%(
                    self._value, self.key, rest
                )
            )
            
        striped = rest.lstrip('0')
        paddlen = (self.padding.count('#')*4)+self.padding.count('@')
        if len(rest) != paddlen and not len(striped) > paddlen:
            raise FieldValueError(
                'Value %r is not invalid for %r: bad padding len (should be %r)'%(
                    self._value, self.key, self.prefix+str(int(rest)).zfill(paddlen)
                )
            )

    def _after_set_value(self):
        self.index = int(self._value[len(self.prefix):])

    def next_value(self, offset=1):
        paddlen = (self.padding.count('#')*4)+self.padding.count('@')
        return '%s%s'%(self.prefix, str(self.index+offset).zfill(paddlen))

