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

    The kabaret.flow.params.trigger module.
    Defines the TriggerParam and the TriggerParamValue.
    A Node using TriggerParam is able to run some Node defined code. 
    This is how the flow interacts with non-flow data.
    
'''
from .param import ParamValue, Param

class TriggerError(AttributeError):
    def __init__(self, node, param_name, message):
        self.node = node
        self.param_name = param_name
        self.message = message
        super(TriggerError, self).__init__(
            'Error after trigger %r in %r (a %r). Error was: %s'%(
                param_name, node.path(), node.__class__.__name__, message
            )
        )

class TriggerParamValue(ParamValue):
    '''
    The TriggerParamValue call its node's trigger() when
    its set() method is called. The data argument of
    this method is not used and should be None.
    
    The data set is the value returned by the trigger()
    call.
    
    As a convenience, the TriggerParamValue is callable,
    which acts as a call to set(None)
    '''
        
    def __call__(self):
        self.set(None)
        
    def set(self, data=None): #@ReservedAssignment
        '''
        Triggers this param.
        
        The data argument is not used.
        The base class implementation is called with
        the result of this value's node trigger()
        method.
        '''
        try:
            data = self.node.trigger(self.param_name)
        except Exception, err:
            self.set_error(
                TriggerError(
                    self.node, self.param_name, 
                    str(err)
                )
            )
            import traceback
            print '# TRIGGER ERROR', self.path()
            print '# TRIGGER ERROR stack begin -----------------'
            traceback.print_exc()
            print '# TRIGGER ERROR stack end -------------------'
        else:
            super(TriggerParamValue, self).set(data)

class TriggerParam(Param):
    '''
    A TriggerParam holds a TriggerParamValue.
    
    No matter what you set on this param, the ui_info
    'editor' will always be 'trigger'.
    '''
    
    
    _VALUE_CLASS = TriggerParamValue

    def ui_infos(self, node=None):
        ret = super(TriggerParam, self).ui_infos(node)
        ret['editor'] = 'trigger'
        return ret
    