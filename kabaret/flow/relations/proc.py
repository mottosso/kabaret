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

    The kabaret.flow.relations.proc module.
    Defines the Proc class.
    
    This relation tells that the related Node is 'contained' and 
    can be 'Executed'

    This relation act as the Child relation but only accepts subclasses 
    of kabaret.flow.nodes.proc.ProcNodes (or a compliant ones) as node_type.
    

'''

from .child import Child
    
class Proc(Child):
    '''
    The Proc Relation is a specialized Child relation.
    See kabaret.flow.relations.child.Child()
    
    The node_type of a child_relation must be a subclass
    of kabaret.flow.nodes.proc._ProcNodeBase or a compliant one
    (it must have 'prepare' and 'get_execute_cmd methods).
    
    This ensures the related node can be executed.
    
    '''
    @classmethod
    def _assert_has_required_interface(cls, node_type):
        for name in ('prepare', 'execute'):
            try:
                if not callable(getattr(node_type, name)):
                    raise TypeError
            except (AttributeError, TypeError):
                raise TypeError(
                'Cannot use %r for Proc relation: '
                'it does not seem to be a subclass of (or compliant with) %r'%(
                    node_type, 'kabaret.flow.nodes.proc.ProcNode'
                )
            )
            
    def __init__(self, node_type):
        self._assert_has_required_interface(node_type)
        super(Proc, self).__init__(node_type)

    def get_related_node(self, parent):
        '''
        Overrides the Child relation method to use '_proc_related' 
        attribute of the parent node instead of '_child_related'
        '''
        #TODO: all code using a node attribute should be delegated to
        # their own methods so that we can override them instead of
        # this whole stuff
        try:
            return parent._proc_related[self.name]
        except KeyError:
            with parent._relations_lock:
                try:
                    # Try again, it might exists now:
                    return parent._proc_related[self.name]
                except KeyError:
                    node = self.node_type(parent, self.name)
                    # Set the case before configuration since the config may set some CaseParam:
                    node.set_case(
                        parent._case.get_child_case(
                            self.make_related_uid(node.node_id),
                            self.node_type.type_names()
                        )
                    )
                    parent._proc_related[self.name] = node
            node._init_relations()
            # Now configure:
            self._configure_node(node)
            return node

#    def _create_node(self, parent):
#        '''
#        Overrides the Child relation method to use '_proc_related' 
#        attribute of the parent node instead of '_child_related'
#        '''
#        node = self.node_type(parent, self.name)
#        parent._proc_related[self.name] = node
#        return node
    
