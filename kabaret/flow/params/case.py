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

    The kabaret.flow.params.case module.
    Defines the CaseParam class.
    A Node using some CaseParam is able to represent different scenarios 
    saved in some kabaret.flow.case.CaseData
    
'''

from .param import Param, ParamValue

class CaseParamValue(ParamValue):
    '''
    The CaseParamValue sets the corresponding item
    of its node's case when its data changes.
    '''
    def __init__(self, param_name, node):
        super(CaseParamValue, self).__init__(param_name, node)
    
    def apply_stored_data(self, data):
        super(CaseParamValue, self).set(data)
        
    def set(self, data): #@ReservedAssignment
        super(CaseParamValue, self).set(data)
        self.node._case[self.param_name] = data
        
        # Tell the relation that the list of ids changed:
        relation = self.node.get_param(self.param_name)._many_relation_ids_param
        if relation is not None:
            relation.sync_cases(self.node)

class CaseParam(Param):
    '''
    A CaseParam is able to set the ParamValue accordingly to
    the data in the node case.
    '''
    _VALUE_CLASS = CaseParamValue

    def __init__(self, default=None):
        super(CaseParam, self).__init__(default)
        self.default = default
        # When the case param is used as list of case ids in a Many
        # relation, the relation sets this attribute to itself:
        self._many_relation_ids_param = None 

    def set_ids_for_many(self, relation):
        self._many_relation_ids_param = relation

    def ui_infos(self, node=None):
        '''
        Overrides the ui_infos to include the 'ids_for_many' key.
        It will contain the name of Many the relation using this param to
        store the related ids, or None.
        '''
        infos = super(CaseParam, self).ui_infos(node)
        if self._many_relation_ids_param is not None:
            infos['ids_for_many'] = self._many_relation_ids_param.name
        return infos
    
    def apply_case(self, node):
        '''
        Called when the node owning this Param loads a
        case.
        Sets the ParamValue accordingly to the data in 
        the node's case.
        '''
        pv = self.get_value(node)
        try:
            pv.apply_stored_data(node._case[self.name])
        except KeyError:
            if self.default is None:
                raise
            value = callable(self.default) and self.default() or self.default
            pv.apply_stored_data(value)
            #do not store default: node._case[self.name] = value
                
    def create_case(self):
        '''
        Called when the node owning this Param is building
        a case.
        Return the ParmaValue's default data.
        '''
        default = callable(self.default) and self.default() or self.default
        return {self.name: default}
