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

    The kabaret.flow.params.status module.
    Defines the StatusParam and StatusParamValue.
    A node using some StatusParam can summarize a list of status
    and affect other node's status when one of hers changes.
    
    
'''
raise Exception('THIS IS NOT IMPLEMENTED AND SHOULD NOT BE USED')

#TODO: implement the status choices and propagation scheme

from .param import ParamValue, Param


class StatusParamValue(ParamValue):
    def __init__(self, status_name, node):
        super(StatusParamValue, self).__init__(status_name, node)

class StatusParam(Param):
    _VALUE_CLASS = StatusParamValue

    def __init__(self, default=None):
        super(StatusParam, self).__init__(default)
