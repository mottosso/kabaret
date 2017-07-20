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

    The kabaret.flow.params.computed module.
    Defines the ComputedParam and ComputedParamValue.
    A Node using ComputedParam is able to provide dynamic value. 
    This is how the flow provides intelligence.
    
'''
from .param import ParamValue, Param

class ComputeError(AttributeError):
    def __init__(self, node, param_name, message):
#        self.node = node
#        self.param_name = param_name
#        self.message = message
        super(ComputeError, self).__init__(
            'Error computing %r in %r (a %r). Error was: %s'%(
                param_name, node.path(), node.__class__.__name__, message
            )
        )

class ComputedParamValue(ParamValue):
    '''
    The ComputedParamValue call its node's compute_param() when
    its get() method is call while it is dirty.
    
    The node compute_param must then call set() on this ParamValue
    or a ComputeError will be raised.
    Any Exception raise while in compute_param will be wrapped in
    a ComputeError, stored in the 'error' attribute and raised.
    
    Unlike the Param, the ComputedParam does not disconnect its
    sources when set.
    This is so the compute method can use the source in the 
    computation. for example:
        def compute(self, param_name):
            if param_name == 'my_param':
                if self.my_param.has_source():
                    # use the source to compute
                    self.my_param.set(', '.join(self.my_param.get_from_sources()))
                else:
                    # use a default computation
                    self.my_param.set('default value')
    '''
    def __init__(self, param_name, node):
        super(ComputedParamValue, self).__init__(param_name, node)
        self._disconnect_on_set = False

    def get(self):
        if not self.error and self._dirty:
            try:
                self.node.compute(self.param_name)
            except Exception, err:
                if 1:
                    print '#\n#COMPUTE ERROR (%s)\n# %r\n#\n'%(self.param_name, self.uid(),)
                    import traceback
                    traceback.print_exc()
                self.set_error(
                    ComputeError(
                        self.node, self.param_name, 
                        str(err)
                    )
                )
                return self.data

            if self._dirty:
                self.set_error(
                    ComputeError(
                        self.node, self.param_name, 
                        "compute() did not compute me! (i\'m still dirty)"
                    )
                )

        return self.data

class ComputedParam(Param):
    _VALUE_CLASS = ComputedParamValue
