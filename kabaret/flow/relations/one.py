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

    The kabaret.flow.relations.one module.
    Defines the One class.
    This relation tells that a related Node exists for
    a given sub-case in the parent node case.
        
    This relation differs from the 'Child' relation in the 
    sense that it is directly in the focus of the final user.
    It produces a Node that has a case of its own.
    The related Node is not simply a grouping or encapsulating
    node, it represents something clearly identified by the 
    user (not just the programmer). 
    
    Also, the related node is lazily created.
    
'''

from ._base import Relation


class One(Relation):
    '''
    The One Relation ties a single node to its owner node.
    '''
    
    def get_related_node(self, parent):
        try:
            return parent._one_related[self.name]
        except KeyError:
            with parent._relations_lock:
                try:
                    # Try again, it might exists now:
                    return parent._one_related[self.name]
                except KeyError:
                    node = self.node_type(parent, self.name)
                    # Set the case before configuration since the config may set some CaseParam:
                    node._parent_relation_name = self.name
                    case = node._parent._case.get_one_case(
                            self.make_related_uid(node.node_id),
                            self.node_type.type_names()
                        )
                    case.load()
                    node.set_case(case)
                    # Store it AFTER set_case:
                    parent._one_related[self.name] = node
            node._init_relations()
            self._configure_node(node)
            return node

#    def _create_node(self, parent):
#        '''
#        Create the related node and stores it in the owner node's
#        '_one_related' dict under this relation name.
#        '''
#        node = self.node_type(parent, self.name)
#        parent._one_related[self.name] = node
#        return node
        
    def create_case(self):
        '''
        Returns a case created by the related node's 
        create_case() method.
        '''
        return {self.name: self.node_type.create_case()}

