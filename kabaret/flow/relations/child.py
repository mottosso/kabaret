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

    The kabaret.flow.relations.child module.
    Defines the Child class.
    This relation tells that the related Node is 'contained'.

    Child Nodes are created and configured as soon as their parent
    is created.
    
    This relation is used to package some behavior in specialized
    Node class so that it can be reused somewhere else.
    
    It can also be used to simply group things together.
    
    Chances are that user interfaces will hide the Child nodes since
    they exists for the programmer more than for the user.

'''

from ._base import Relation


class Child(Relation):
    '''
    The Child Relation defines a node a the relation owner's child.
    
    The difference with the One relation may seam subtle; it relates 
    to case data management and UI.
    
    When a child related node is created, it does not load any case
    data. The child node should be fully configured and should not
    contain any CaseParam. (The One related receives a case right
    after configuration.)    

    When a node is instantiated, all its Child related nodes are
    created. (The One related are created only if accessed.)
    
    One related nodes are in the final user focus whereas Child related
    nodes are used by the flow designer to achieve his goal.
    When choosing between One or Child relations, you should consider
    a Child node as an hidden part of the owning node.
    
    '''
    
    def get_related_node(self, parent):
        try:
            return parent._child_related[self.name]
        except KeyError:
            with parent._relations_lock:
                try:
                    # Try again, it might exists now:
                    return parent._child_related[self.name]
                except KeyError:
                    node = self.node_type(parent, self.name)
                    # Set the case before configuration since the config may set some CaseParam:
                    node.set_case(
                        parent._case.get_child_case(
                            self.make_related_uid(node.node_id),
                            self.node_type.type_names()
                        )
                    )
                    # store it AFTER set_case:
                    parent._child_related[self.name] = node
            node._init_relations()
            # Now configure:
            self._configure_node(node)
            return node

#    def _create_node(self, parent):
#        '''
#        Create the related node and stores it in the owner node's
#        '_child_related' dict under this relation name.
#        '''
#        node = self.node_type(parent, self.name)
#        parent._child_related[self.name] = node
#        return node

    def create_case(self):
        '''
        Returns a case created by the related node's 
        create_case() method.
        '''
        case = self.node_type.create_case()
        return case and {self.name: case} or {}

    def init_relation(self, node):
        '''
        Override default behavior to instantiate the related child node.
        '''
        self.__get__(node)

