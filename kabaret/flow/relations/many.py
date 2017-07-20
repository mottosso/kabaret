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

    The kabaret.flow.relations.many module.
    Defines the Many class.
    This relation tells that one related Node exists for 
    each sub-case in the parent node case.
        
    For example, a Film contains several Shots.
    You don't want to write a specific Node class for each film, you
    want to write a Film Node that contains several (one per case)
    Shots Nodes.

    The related nodes are lazily created.
    
'''

from ._base import Relation


class Many(Relation):
    '''
    The Many Relation ties several nodes to its owner node.
    '''
    def __init__(self, node_type, default_case_id=None, ids_param_name=None):
        '''
        The ids_param must be the name of the param storing the ids
        of the cases.
        
        The default_case_id is used when creating a case with
        the create_case() method.
        '''
        super(Many, self).__init__(node_type)
        self.ids_param_name = ids_param_name
        self.default_case_id = default_case_id

    def __get__(self, node, node_type=None):
        '''
        Returns the Many relation when called from the
        class.
        Returns a _CaseProducer when called from a Many
        relation instance.
        (See the _CaseProducer class.)
        '''
        if node is None:
            return self
        return _CaseProducer(self, node)

    def create_case(self):
        '''
        Creates default case for this relation.
        The returned case will contain a case created
        by the related node's type create_case() method
        stored under the name given in the constructor's
        default_case_id argument.
        '''
        case_id = self.default_case_id or self.name.title()
        cases = {
            case_id:self.node_type.create_case(),
        }
        return {self.name: cases}
    
    def make_related_uid(self, node_id):
        return ':'.join((self.name, node_id))

    def get_ids_param_name(self):
        '''
        Returns the name of the param holding the
        list of case ids.
        See also get_ids_param_value(node).
        '''
        return self.ids_param_name
    
    def get_ids_param_value(self, node):
        '''
        Returns the param value holding the list
        of case ids.
        '''
        return node.get_param_value(self.ids_param_name)
    
    def get_related_ids(self, node):
        '''
        Returns a tuple of node_id for each known
        case of this relation for the given node.
        
        The node_id list is read from the node's param
        that was specified in the relation constructor
        as 'id_param'.
        If no such param exists in the node, an AttributeError
        is raised.
        '''
        ret = self.get_ids_param_value(node).get()
        
        # Be sure it's iterable:
        if ret is None:
            ret = ()
        elif not isinstance(ret, (tuple, list)):
            ret = (ret,)
        # Convert each to string
        ret = [ str(i) for i in ret ]
        # Filter out bad values:
        ret = [ i for i in ret if i and i.replace('_', '').isalnum() and i[0].isalpha() ]
        
        return tuple(ret)

    def add_related_id(self, node, node_id, ensure_new=True):
        ids = self.get_related_ids(node)
        if node_id in ids:
            if ensure_new:
                raise Exception(
                    'Case %r already exists in %r of node: %r'%(
                        node_id, self.name, node.uid()
                    )
                )
            return 
        node.get_param_value(self.ids_param_name).set(ids+(node_id,))
    
    def drop_related_id(self, node, node_id):
        ids = self.get_related_ids(node)
        try:
            ids.remove(node_id)
        except ValueError:
            return
        node.get_param_value(self.ids_param_name).set(ids)
            
    def sync_cases(self, node):
        '''
        Create or disable cases to match the case ids
        set in the ids param.
        '''
        print '-->> SYNC CASES', node.uid(), self.name    
        related_ids = self.get_related_ids(node)
        type_names = self.node_type.type_names()
        for related_id in related_ids:
            case = node._case.get_many_case(self.make_related_uid(related_id), type_names)
            case.ensure_exists()
            
class _CaseProducer(object):
    '''
    A _CaseProducer is used by the Many Relation to specify
    the case id of the related node to retrieve:
        related_node = my_node.many_relation[case_id]
    
    '''
    def __init__(self, cases_relation, parent_node):
        super(_CaseProducer, self).__init__()
        self.parent_node = parent_node
        self.cases_relation = cases_relation

    def create_new_case(self, case_id):
        self.cases_relation.add_related_id(self.parent_node, case_id, ensure_new=True)
        return self[case_id]

# NOT USED:
#    def ensure_case(self, case_id):
#        self.cases_relation.add_related_id(self.parent_node, case_id, ensure_new=False)
#        return self[case_id]
#        
#    def drop_case(self, case_id):
#        self.cases_relation.drop_related_id(self.parent_node, case_id)
        
    def get_ids_param_name(self):
        '''
        Returns the name of the param holding the
        list of case ids.
        See also get_ids_param_value(node).
        '''
        return self.cases_relation.ids_param_name
    
    def get_ids_param_value(self, node):
        '''
        Returns the param value holding the list
        of case ids.
        '''
        return self.cases_relation.get_ids_param_value(node)
    
    def get_related_ids(self):
        '''
        Returns the list of node id available for this relation.
        '''
        return self.cases_relation.get_related_ids(self.parent_node)
    
    def __getitem__(self, name):
        '''
        Returns the node in this relation having the case id 'name'.
        '''
        key = (self.cases_relation.name, name)
        try:
            return self.parent_node._many_related[key]
        except KeyError:
            with self.parent_node._relations_lock:
                try:
                    # Try again, it might exists now:
                    return self.parent_node._many_related[key]
                except KeyError:
                    node = self.cases_relation.node_type(
                        self.parent_node, name
                    )
                    node._parent_relation_name = self.cases_relation.name
                    # Set the case before configuration since the config may set some CaseParam:
                    case = self.parent_node._case.get_many_case(
                        self.cases_relation.make_related_uid(name),
                        self.cases_relation.node_type.type_names()
                    )
                    case.load()
                    node.set_case(case)
                    self.parent_node._many_related[key] = node
            node._init_relations()
            # Now configure:
            self.cases_relation._configure_node(node)
            return node
