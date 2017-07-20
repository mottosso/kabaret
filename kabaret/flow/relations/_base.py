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

    The kabaret.flow.relations._base module.
    Defines the abstract Relation class.
    
'''

class _RecordedCall(object):
    def __init__(self, recorder, func_name):
        super(_RecordedCall, self).__init__()
        self.recorder = recorder
        self.func_name = func_name

    def __call__(self, *args, **kwargs):
        self.recorder._recorded_calls.append(
            (self.func_name, args, kwargs)
        )
        return self.recorder

class Relation(object):
    '''
    This is an abstract Relation.
    
    Subclasses must implement the create_case() method.
    
    A Relation is used to tie some nodes to another.
    A Relation is a descriptor and must be instantiated in the
    class definition:
        class MyNode(Node):
            node_name = MyRelation(MyOtherNode, some_parameters)
    
    When declaring a Relation in a Node class, you can provide
    some actions to perform upon node creation:
        class MyNode(Node):
            node_name = MyRelation(MyOtherNode).set_option(bob='Bill')
    In this example, an instance of MyOtherNode is in relation with each
    MyNode instance and is stored in the 'node_name' attribute.
    When node_name if first accessed, a MyOtherNode is created and its
    set_option() method is called with the keyword arguments bob='Bill'.
    
    For convenience, each argument used in creation calls is inspected 
    and replaced as this:
        - If the argument is a sibling Child relation of the Relation 
        creating a node, the related node replaces it.
        - If the argument is a Param of the node holding the Relation
        creating a node, the ParamValue replaces it.
     
    '''
    _LAST_INDEX = 0
    
    @classmethod
    def _get_new_index(cls):
        cls._LAST_INDEX += 1
        return cls._LAST_INDEX
    
    @classmethod
    def _reset_new_index(cls):
        cls._LAST_INDEX = 0
        
    def __init__(self, node_type):
        '''
        Creates a new unnamed Relation.
        The Relation name will be set by the Node meta class.
        '''
        super(Relation, self).__init__()
        self.index = self.__class__._get_new_index()
        self.name = None
        self.node_type = node_type
        self._recorded_calls = []

    def __getattr__(self, name):
        '''
        relation.recorded_creation_call(param).recorded_creation_call()...
        
        Use this to specify all the call that must be done on the
        related node when it is created by this relation.
        '''
        #TODO: support dotted calls?
        # the recorder would be easy but apply would be 
        # slower :/
        # + resolution of param arg to param value, parent etc...
        # would be a mess :/
        if name not in dir(self.node_type):
            raise AttributeError(
                'The node type %r does not seam to have a '
                '%r method. You can\'t use it as relation creation call.'%(
                    self.node_type, name
                )
            )
        return _RecordedCall(self, name)    

    def __get__(self, node, node_type=None):
        '''
        Access the related node from the relation owner node:
            my_relation.__get__(my_node) <=> my_node.my_related_node
        
        Subclass should implement get_related_node() instead of
        this.
        '''
        if node is None:
            return self
        return self.get_related_node(node)
    
    def get_related_node(self, parent):
        '''
        Return the related node for the given parent,
        instantiating it if needed.
        
        Subclasses must implement this.
        
        Note that subclasses must acquire the parent 
        _relations_lock context before instantiating and storing
        the related node, and then call _init_relations() and
        _configure_node() on the new node.
        '''
        raise NotImplementedError
    
#    def _create_node(self, parent):
#        '''
#        Instanciate and return a related node.
#        Subclasses must implement this.
#        
#        This should only be called in the parent
#        _relation_lock context, and the need to create
#        should be verified once the context is
#        acquired:
#            with parent._relation_lock:
#                try:
#                    # Try again, it might exists now:
#                    return parent._child_related[self.name]
#                except KeyError:
#                    self._create_node(parent)
#        '''
#        raise NotImplementedError

    def _configure_node(self, node):
        '''
        Configures the given node as a fresh
        related node.
        '''
        # Connect params to parent when requested:
        for param in node.iterparams():
            param.auto_connect(node)
            
        # Apply recorded calls
        parent = node._parent
        for func_name, args, kwargs in self._recorded_calls:
            #TODO: resolve kwargs too you lazy bastard!!! :)
            if parent is not None:
                resolved_args = []
                for arg in args:
                    if (
                        arg in parent._child_relations 
                        or 
                        arg in parent._proc_relations
                        or
                        arg in parent._relations
                        ):
                        # resolve to the node instance
                        # when the argument is a related node
                        # descriptor in the same parent:
                        arg = arg.__get__(parent)
                    elif arg in parent._params:
                        # resolve to the param_value
                        # when the argument is a param
                        # descriptor in the parent:
                        arg = arg.get_value(parent)
                    
                    resolved_args.append(arg)
            else:
                resolved_args = args
            try:
                getattr(node, func_name)(*resolved_args, **kwargs)
            except:
                print '/!\ ERROR APPLYING RELATED CONFIG ON %s (%r)'%(node.uid(), node) 
                print '   function:', func_name, 'args:', (resolved_args, kwargs)
                raise
            
    def create_case(self):
        '''
        Returns a case suitable for the related node.
        Subclasses must implement this.
        If the related node does not uses cases, {} should 
        be returned.
        '''
        raise NotImplementedError

    def make_related_uid(self, node_id):
        '''
        Return string to use in an uid for the given
        related node_id.
        '''
        return node_id
    
    def get_related_ids(self, node):
        '''
        Returns a tuple of node_id for each known
        case of this relation for the given node.
        '''
        return (self.name,)
    
    def init_relation(self, node):
        '''
        Called by the node right after its _configure() and
        the set_case() calls, before the configuration by the owning
        relation.
        The subclasses may override this to setup states depending
        on the relation type.
        
        Default behavior is to do nothing.
        '''
        pass
        
#    def get_related_nodes(self, node):
#        '''
#        Returns a tuple of node for each known
#        case of this relation for the given node.
#        '''
#        return (self.get_related_node(node),)
        