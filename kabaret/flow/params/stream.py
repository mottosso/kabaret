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

    The kabaret.flow.params.stream module.
    Defines the StreamParam and StreamParamValue.
    
    A StreamParam is used to chain nodes together, forming 
    a directed node stream.
    
    The StreamParamValue can only be connected to another
    StreamParamValue.
    Its data (retrieved with the get() method) is the node
    owning the StreamParamValue it is connected to, or None.
    
    When setting the value of the param, the data must be a list
    of nodes. Those nodes will be set as the sources and thus will 
    be the data returned by get().
    The not acceptable nodes passed to set() will be silently
    skipped.
    
'''

from .param import ParamValue, Param

class StreamTypeError(TypeError):
    pass

class StreamParamValue(ParamValue):

    def __init__(self, status_name, node):
        super(StreamParamValue, self).__init__(status_name, node)
        self._acceptable_node_types = None # None <=> accept all

    def touch(self):
        '''
        A StreamParamValue does not touches its
        downstreams when it gets touched.
        '''
        ds = self.downstreams
        self.downstreams = []
        super(StreamParamValue, self).touch()
        self.downstreams = ds
        
    def add_source(self, source_param_value):
        '''
        Adds the given source_param_value to this param sources
        only if it matches the types given in the constructor
        argument 'acceptable_node_types'
        '''
        if self._acceptable_node_types is not None:
            node = source_param_value.node
            if not isinstance(node, self._acceptable_node_types):
                raise StreamTypeError(
                    'The node of %r (%r) is not acceptable for this stream. '
                    'Acceptable types are %r'%(
                        source_param_value.uid(), node, self._acceptable_node_types
                    )
                )
        super(StreamParamValue, self).add_source(source_param_value)

    def get_from_sources(self):
        '''
        Return the node(s) of the source param value(s).
        '''
        if self._source_as_dict:
            # when in dict mode, event one source
            # produces a dict:
            return dict([ 
                (up_id, node) for up_id, node 
                in zip(self.upstreams_ids, self.upstream_nodes()) 
            ]) 
        else:
            # As opposed to Param, even a single upstream
            # returns a list of nodes (of lenght 1)
            return self.upstream_nodes()

    def upstream_nodes(self):
        return [ up.node for up in self.upstreams ]
    
    def downstream_nodes(self):
        return [ down.node for down in self.downstreams ]

    def change_acceptable_node_types(self, acceptable_node_types):
        ups = list(self.upstreams)
        self.disconnect()
        self._acceptable_node_types = acceptable_node_types
        for up in ups:
            try:
                self.add_source(up)
            except StreamTypeError:
                continue
    
    def set(self, nodes): #@ReservedAssignment
        self.disconnect()

        for n in nodes:
            try:
                self.add_source(n)
            except StreamTypeError:
                continue
            
        self._set_clean()

class StreamParam(Param):
    _VALUE_CLASS = StreamParamValue

    def __init__(self, acceptable_node_types=None, sources_as_dict=False):
        super(StreamParam, self).__init__(None, sources_as_dict)
        self._acceptable_node_types = acceptable_node_types

    def get_value(self, node):
        pv = Param.get_value(self, node)
        pv._acceptable_node_types = self._acceptable_node_types
        return pv
        
