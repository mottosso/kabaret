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

    The kabaret.flow.nodes.node module.
    Defines the Node class, base for all flow nodes.
    
'''

import threading
import contextlib

from ..params.param import Param
from ..params.case import CaseParam

from ..relations._base import Relation
from ..relations.child import Child
from ..relations.many import Many
from ..relations.proc import Proc


class NodeType(type):
    '''
    The NodeType is the Node meta class.
    
    It sets the name of all Relation and Param defined in the
    class definition.
    
    It collects Relation and Param in the base class(es) and build
    the new Node class' _child_relations, _proc_relations, _relations, and _params lists.
    
    '''
    
    def __new__(cls, class_name, bases, class_dict):
        is_base_class = bases == (object,)
        
        Relation._reset_new_index()
        Param._reset_ui_defaults()
        
        if not is_base_class:
            # Check name clashes:
            if '_params' in class_dict:
                raise ValueError('"_params" is a reserved name in a Node subclass.')
            if '_child_relations' in class_dict:
                raise ValueError('"_child_relations" is a reserved name in a Node subclass.')
            if '_proc_relations' in class_dict:
                raise ValueError('"_proc_relations" is a reserved name in a Node subclass.')
            if '_relations' in class_dict:
                raise ValueError('"_relations" is a reserved name in a Node subclass.')
        
            # Collect base classes descriptors:
            _params = {}
            _child_relations = {}
            _proc_relations = {}
            _relations = {}
            many_relations = []
            for base in bases:
                if issubclass(base, Node):
                    for param in base._params:
                        _params[param.name] = param
                    for relation in base._child_relations:
                        _child_relations[relation.name] = relation
                    for relation in base._proc_relations:
                        _proc_relations[relation.name] = relation
                    for relation in base._relations:
                        _relations[relation.name] = relation
        
            # Gather and Configure new descriptors, overriding base ones:
            for n, o in class_dict.iteritems():
                if isinstance(o, Param):
                    o.name = n
                    _params[n] = o
                elif isinstance(o, Proc):
                    o.name = n
                    _proc_relations[n] = o
                elif isinstance(o, Child):
                    o.name = n
                    _child_relations[n] = o
                elif isinstance(o, Relation):
                    o.name = n
                    _relations[n] = o
                    if isinstance(o, Many):
                        many_relations.append(o)
                    
            for relation in many_relations:
                # Auto declare case_ids param for Many relations:
                if relation.ids_param_name is None:
                    # Build and set default ids_param_name
                    ids_param_name = relation.name
                    if ids_param_name.endswith('s'):
                        ids_param_name = ids_param_name[:-1]
                    ids_param_name = ids_param_name+'_ids'
                    relation.ids_param_name = ids_param_name
                    # Declare the param if it does not exists yet:
                    if ids_param_name in _params.keys():
                        raise Exception(
                            'ids_param_name not specified for Many %r, '
                            'but the param %r is declared. You should either specify the '
                            'ids_param_name in the Many() constructor or be sure that '
                            'the default param name is available.'%(
                                relation.name, ids_param_name
                            )
                        )
                    ids_param = CaseParam(default=[])
                    ids_param.ui(editor='relation_ids', group='Relations', group_index=0)
                    ids_param.name = ids_param_name
                    class_dict[ids_param_name] = ids_param
                    _params[ids_param_name] = ids_param
                    
                # Bind case_ids param to the corresponding relation
                try:
                    param = _params[relation.ids_param_name]
                except KeyError:
                    raise Exception(
                        'The Many relation %r uses the %r as ids_param_name '
                        'but no param has this name in declaration of Node '
                        'subclass %r'%(
                            relation.name, relation.ids_param_name,
                            class_name
                        )
                    )
                try:
                    param.set_ids_for_many(relation)
                except:
                    raise Exception(
                        'The Many relation %r uses the %r as ids_param_name '
                        'but this param is not a CaseParam in declaration of '
                        'Node subclass %r'%(
                            relation.name, relation.ids_param_name,
                            class_name
                        )
                    )
                
            # Extend class definition:
            class_dict['_params'] = _params.values()
            class_dict['_child_relations'] = _child_relations.values()
            class_dict['_proc_relations'] = _proc_relations.values()
            class_dict['_relations'] = _relations.values()
            
            if 0:
                print 5*'###########\n'
                print 'SUBCLASS', class_name
                print 'SUPERS:', bases
                print '_params:', [ p.name for p in _params.values() ]
                print '_child_relations:', [ n.name for n in _child_relations.values() ]
                print '_proc_relations:', [ n.name for n in _proc_relations.values() ]
                print '_relations:', [ r.name for r in _relations.values() ]
            
        # Instantiate the class:
        return  super(NodeType, cls).__new__(cls, class_name, bases, class_dict)

class Node(object):
    '''
    The Node holds some Param and is tied to other nodes by some Relation.
    
    The connections between nodes' Param form a directed multigraph.
    The related nodes form a tree.
    
    A Node belongs to a Flow.
    The Flow provides functionalities specific to the purpose and context of
    the node graph.
    
    The ComputedParam will call the node's compute() method to update
    their data.
    The node's compute() method should call the ComputedParamValue's set() 
    method.

    The CaseParam will have their value read from the node's case.

    When a ParamValue gets dirty (some source value has changed), the node's 
    param_touched() is called.
    The node's param_touched is responsible of the propagation of the touch
    to its other Params.
    
    '''
    
    __metaclass__ = NodeType
    
    _params = []
    _child_relations = []
    _proc_relations = []
    _relations = []
    
    ICON_NAME = None
    
    @classmethod
    def create_case(cls):
        '''
        Return a dict with all default values for a case
        of this node class (all params and all child node's
        params).
        '''
        ret = {}
        for param in cls.iterparams():
            ret.update(param.create_case())
            
        for child_relation in cls._child_relations:
            ret.update(child_relation.create_case())
            
        for proc_relation in cls._proc_relations:
            ret.update(proc_relation.create_case())
            
        return ret
    
    def __init__(self, parent, node_id=None):
        '''
        Instantiates a new node.
        You should not need to create nodes yourself since
        the Flow.init_root() will create the root node and
        all related nodes will be accessible thru their owner
        node.
        
        All Child nodes are created when creating a Node.
        
        NOTE: subclasses must not override the constructor.
        If you need to setup your node instance right after 
        creation (set param or access children params) you must 
        override the _configure() method instead of the 
        constructor.
        '''
        
        super(Node, self).__init__()
        self._parent = parent
        self.node_id = node_id or self.__class__.__name__
        self._flow = None
        self._case = None
        self._parent_relation_name = None
        
        self._relations_lock = threading.Lock()
        self._one_related = {}    # One relation name: related node instance
        self._many_related = {}   # (Many relation name, case id) : related node instance
        self._child_related = {}   # Child relation name: related node instance
        self._proc_related = {}   # Proc relation name: related node instance
        self._param_values = {}      # Param name: ParamValue

        self._ticked = False
        
    def set_case(self, case):
        '''
        Sets the case used by this node.
        Each Param will get an apply_case() call.
        Each Child node will get a set_case() call with a
        corresponding sub-case.
        '''
        self._case = case
        for param in self.iterparams():
            param.apply_case(self)
         
    def _init_relations(self):
        '''
        Called by the relation building the node to initialize all 
        related nodes.
        '''
        for relation in self._child_relations+self._proc_relations+self._relations:
            relation.init_relation(self)
        
        try:
            self._configure()
        except:
            print 'Error while configuring node', self, self.uid()
            raise

    def _configure(self):
        '''
        Due to the way nodes are automatically created when 
        using node relations, one cannot subclass the constructor
        to provide default values to the node param of children
        params.
        
        This method is a placholder for that. It will be called
        right after all param and children are instanciated and
        right before the configuration declared on the relation.
        
        Beware though: setting CaseParams in here should not be
        done since it would constantly override the data coming from
        the case (and will generate an enormous data history!!!)
        You should first check for a bad value if this is what 
        you want.
        '''
        pass
    
    @classmethod
    def doc(cls):
        '''
        Returns the user doc for this node.
        The default is to return the node's docstring.
        '''
        return cls.__doc__
    
    @classmethod
    def ui_infos(cls, node=None):
        '''
        Returns a dict with all ui infos for this Node type.
        (Modifying this dict will not afect the Node type)
        
        If 'node' is not None, those additional informations
        are included:
            node_id: the ParamValue's data for this node.
            id: the Node's uid.
            path: the Node's path.
            rank: the node's rank.
        
        '''
        #TODO: doesn't this really looks like a descriptor??? 
        ret = {
            'type': cls.type_name(),
            'icon': cls.ICON_NAME,
        }
        if node is not None:
            ret.update({
                'node_id': node.node_id,
                'id': node.uid(), 
                'path': node.path(),
                'rank': node.rank(),
            })
        return ret
    
    def has_param(self, param_name):
        '''
        Returns True if the node has a Param with name
        'param_name'
        '''
        return (
            # try param values first:
            param_name in self._param_values 
            
            or 
            # If not found, check for the param descriptors
            param_name in [ p.name for p in self._params ]
        ) 

    def get_param(self, param_name):
        '''
        Returns the Param named 'param_name'
        (Not the ParamValue, you must use get_param_value
        or attribute access for that.)
        '''
        return getattr(self.__class__, param_name)
        
    def get_param_value(self, param_name):
        '''
        my_node.get_param_value('my_param') <=> my_node.my_param
        
        If you need to access the Param instead of the ParamValue,
        you must call get_param('my_param').
        '''
        return getattr(self.__class__, param_name).get_value(self)
    
    @classmethod
    def iterparams(cls):
        '''
        Returns an iterator on the list of Param in this Node class.
        '''
        return iter(cls._params)

    def has_child(self, child_id):
        return child_id in self._child_related
    
    def get_child(self, child_id):
        return self._child_related[child_id]
    
    def iterchildren(self):
        '''
        Returns an iterator of (relation_name, child_node) for
        all child related node in this node.
        '''
        return self._child_related.iteritems()
    
    @classmethod
    def iterchildrelations(cls):
        '''
        Returns an iterator on each child relation (not the
        child nodes) of this Node class.
        '''
        return iter(cls._child_relations)
    
    def has_proc(self, proc_id):
        return proc_id in self._proc_related
    
    def get_proc(self, proc_id):
        return self._proc_related[proc_id]
    
    def iterprocs(self):
        '''
        Returns an iterator of (proc_name, proc_node) for
        all proc related node in this node.
        '''
        return self._proc_related.iteritems()
    
    @classmethod
    def iterprocrelations(cls):
        '''
        Returns an iterator on each proc relation (not the
        proc nodes) of this Node class.
        '''
        return iter(cls._proc_relations)
    
    def has_related(self, relation_name):
        try:
            [ 1/0 for relation in self._relations if relation.name == relation_name ]
        except ZeroDivisionError:
            return True
        return False
    
    def get_relation(self, relation_name):
        '''
        Returns the Relation named 'relations_name'
        (Not the related node or node getter)
        '''
        return getattr(self.__class__, relation_name)

    @classmethod
    def iterrelations(cls):
        '''
        Returns an iterator on each relation (not including
        Child relations) of this Node class.
        '''
        return iter(cls._relations)

    def flow(self):
        '''
        Returns the flow managing this node.
        If this node is not the root node, its parent
        flow() method is used.
        
        If this node is not a flow root and not related
        to a node knowing its flow, None is returned.
        (Which is not likely to happen)
        '''
        if self._flow is not None:
            return self._flow
        if self._parent is not None:
            return self._parent.flow()
        return None

    def parent(self):
        '''
        Returns this node's parent node.
        
        The node parent is the one holding the relation
        that ties both node together.
        '''
        return self._parent

    def uid(self):
        '''
        Returns a unique identifier for this node in its flow.
        
        This uid can be used on the node's flow's get() method
        to later retrieve this node.
        
        The uid is a tuple of string.
        Popping the tail of this tuple give successive parents
        uid.
        '''
        nid = self.node_id
        if self._parent_relation_name:
            relation = self._parent.get_relation(self._parent_relation_name)
            nid = relation.make_related_uid(nid)
        uid = (nid,)
        if self._parent is not None:
            uid = self._parent.uid() + uid
        return uid
    
    @classmethod
    def get_type(cls, relative_uid):
        '''
        Returns the class of a node the related to this
        one using the given relative_uid.
        
        If the uid points to a Param, the Param instance
        is returned.
        '''
        #TODO: the relations should take care of the next_id decoding!
        klass = cls
        relative_uid = list(relative_uid)
        while relative_uid:
            next_id = relative_uid.pop(0)
            if next_id.startswith('.'):
                param_name = next_id[1:]
                for p in klass._params:
                    if p.name == param_name:
                        return p
                raise AttributeError('No %r param in node type %r'%(next_id, klass))
            elif ':' in next_id:
                # it is a relation:
                relation, _ = next_id.split(':')
                klass = getattr(klass, relation).node_type
            else:
                next_klass = None
                for relation in klass._relations:
                    if relation.name == next_id:
                        next_klass = relation.node_type
                        break
                if next_klass is None:
                    for relation in klass._child_relations:
                        if relation.name == next_id:
                            next_klass = relation.node_type
                            break
                if next_klass is None:
                    for relation in klass._proc_relations:
                        if relation.name == next_id:
                            next_klass = relation.node_type
                            break
                if next_klass is None:
                    raise AttributeError('No %r relation in node type %r'%(next_id, klass))
                klass = next_klass
        return klass

    def get(self, relative_uid):
        '''
        Returns a node related to this one using
        the given relative_uid.
        '''
        #TODO: the relations should take care of the next_id decoding!
        node = self
        relative_uid = list(relative_uid)
        while relative_uid:
            next_id = relative_uid.pop(0)
            if next_id.startswith('.'):
                return node.get_param_value(next_id[1:])
            elif ':' in next_id:
                # it is a relation:
                relation, case_id = next_id.split(':')
                node = getattr(node, relation)[case_id]
            else:
                # it is a ChildNode or a One:
                node = getattr(node, next_id)
        return node
                
    def path(self):
        '''
        Returns a file like path unique in the flow
        that designate this node.
        This is only for display purpose and cannot
        be used to later retrieve this node (use uid()
        for that).
        '''
        return '/'.join(self.uid())
    
    def rank(self):
        '''
        Returns an integer depicting the length of the longest
        dependency path in the parent.
        '''
        return max([ 
            param.get_value(self).rank() for param in self.iterparams() 
        ])
    
    def load_related(self, depth=False):
        '''
        Instantiates all the related node.
        If depth is True, each related node will also
        have their related node loaded, etc...
        '''
        print 'LR', self.uid()
        for relation in self.iterrelations():
            if isinstance(relation, Many):
                producer = getattr(self, relation.name)
                for case_id in relation.get_related_ids(self):
                    related = producer[case_id]
                    if depth:
                        related.load_related(depth=depth)
            else:
                related = relation.get_related_node(self)
                if depth:
                    related.load_related(depth=depth)
                
    def drop_related(self, related_uid):
        '''
        Forget the related node using the given uid.
        Next access to this related node will create a new
        instance.
        
        The related uid must lead to a Child, a One or a
        Many related Node.
        
        This is useful to free some memory when a lot of
        related nodes have been accessed but are not 
        needed anymore.
        '''
        #TODO: the relations should take care of the next_id decoding!
        #TODO: the relations should take care of the drop!
        if ':' in related_uid:
            # it is a many relation:
            relation, node_id = related_uid.split(':')
            key = (relation, node_id,)
            if key in self._many_related:
                with self._relations_lock:
                    del self._many_related[key]
                return
        else:
            # it is a ChildNode or a One:
            if related_uid in self._child_related:
                with self._relations_lock:
                    del self._child_related[related_uid]
                return
            if related_uid in self._one_related:
                with self._relations_lock:
                    del self._one_related[related_uid]
                return
                
    
    def set_ticked(self):
        if not self._ticked:
            self.flow().register_ticked(self)
            self._ticked = True
        
    def tick(self):
        '''
        Called if this node was configured to be periodically 
        ticked (with the set_ticked() method).
        
        This can be used to touch some parameters which value
        depends on data external to the flow (e.g. filesystem)
        
        NB: this makes should not be abused since it can 
        dramatically slow down the flow.
        Nodes using ticks should return from this method
        as fast as possible, i.e. touch but do not
        compute params. 
        '''
        if 1:
            print '/!\\ Unhandled Tick /!\\', self.uid()
            
            
    def param_touched(self, param_name):
        '''
        Called by a Param of this node when it got touched (goes
        to dirty because one of its source changed).
        
        Subclasses should re-implement this to propagate the 
        touch() to all ComputedParam which value depend on
        this one.
        '''
        if 0:
            print 'Touched', self.get_param_value(param_name).path()
            print '  UPS:', [ pv.path() for pv in self.get_param_value(param_name).upstreams ]
            print '  DOWNS:', [ pv.path() for pv in self.get_param_value(param_name).downstreams ]

    
    def compute(self, param_name):
        '''
        Computes and set the value of the node's Param named 'param_name'.
        If this method leaves w/o setting the param value, a
        kabaret.flow.params.computed.ComputError will be raised.
        
        Subclasses must implement this method if they hold some
        ComputedParam.
        '''
        print 'Compute', self.get_param_value(param_name).path()
        print '  UPS:', [ pv.path() for pv in self.get_param_value(param_name).upstreams ]
        print '  DOWNS:', [ pv.path() for pv in self.get_param_value(param_name).downstreams ]
        raise NotImplementedError

    def trigger(self, param_name):
        '''
        Called when a TriggerParamValue was set.
        Must return the data to use for this value.
        '''
        print 'Trigger', self.get_param_value(param_name).path()
        print '  UPS:', [ pv.path() for pv in self.get_param_value(param_name).upstreams ]
        print '  DOWNS:', [ pv.path() for pv in self.get_param_value(param_name).downstreams ]
        raise NotImplementedError
    
    def collect_params(self, *tags):
        '''
        Returns a list of param uids in this node and its
        child related nodes having at least one of the given tags.
        The max_relation_depth controls how deep the params
        are looked up.
        '''
        ret = []
        
        for param in self.iterparams():
            if param.has_tag(*tags):
                ret.append(param.get_value(self).uid())
        
        for _, related in self.iterchildren():
            ret.extend(related.collect_params(*tags))

        return ret

    def find(self, type_name, sub_paths=[], **where):
        return self._case.find_cases(type_name, under_uid=self.uid(), sub_paths=sub_paths, **where)
                    
    @classmethod
    def has_type(cls, type_name):
        '''
        Returns True if this node type can
        act as the type pointed by the given
        type_name
        '''
        return type_name == cls.type_name() or type_name in cls.type_names()
    
    @classmethod
    def node_types(cls):
        '''
        Returns a tuple of types returning True when used
        as node_type in a call to isinstance(cls, node_type).
        '''
        hidden_types = Node.mro()
        hidden_types.remove(Node)
        return tuple([ t for t in cls.mro() if t not in hidden_types ])

    @classmethod
    def type_names(cls):
        '''
        Returns a tuple of strings returning True when used
        as type_name in a call to cls.has_type(type_name).
        '''
        return tuple([ t.__name__ for t in cls.node_types() ])
    
    @classmethod
    def type_name(cls):
        '''
        Returns a string identifying this node higher type.
        '''
        return cls.__name__
    
    @classmethod
    def collect_types(cls, exclude_children=True, visit_children=True):
        '''
        Returns a set of node classes related to this node type.
        If exclude_children is True, the children type names will
        not be collected.
        If visit_children is True, the type names related to the
        children will be collected even if the children are not.
        '''
        ret = set()
        visited = []
        if visit_children:
            for relation in cls.iterchildrelations():
                ret = ret.union(
                    relation.node_type._collect_types(
                        exclude_children=exclude_children,
                        visited=visited
                    )
                )
                if exclude_children:
                    ret.remove(relation.node_type)
            for relation in cls.iterrelations():
                ret = ret.union(
                    relation.node_type._collect_types(
                        exclude_children=exclude_children,
                        visited=visited
                    )
                )
        else:
            ret = cls._collect_types(exclude_children, visited=visited)
        return ret

    @classmethod
    def _collect_types(cls, exclude_children, visited):
        ret = set(cls.node_types())
        visited.append(cls)
        
        if exclude_children:
            relations = cls.iterrelations()
        else:
            relations = list(cls.iterchildrelations())+list(cls.iterrelations())
        
        for relation in relations:
            if relation.node_type in visited:
                continue
            ret = ret.union(
                relation.node_type._collect_types(exclude_children, visited)
            )
        return ret

    @classmethod
    def collect_case_attributes(cls, type_name):
        '''
        Returns all the attribute names accessible
        for a case of the given type_name under this class.
        Case attributes are in the form:
            child[.child.child...].param
        '''
        node_types = cls._find_node_with_type(type_name, exclude_list=[])
        # We must use a set here because we may process
        # several classes with the same base and it would
        # duplicate some attribute names (the inherited ones)
        attrs = set()
        for node_type in node_types:
            attrs = attrs.union(node_type.get_case_attributes())
        return attrs
    
    @classmethod
    def get_case_attributes(cls):
        '''
        Returns all the attribute names accessible
        for a case of this node type.
        '''
        ret = [ param.name for param in cls.iterparams() if isinstance(param, CaseParam) ]
        for child_relation in cls.iterchildrelations():
            ret.extend([
                '%s.%s'%(child_relation.name, sub)
                for sub in child_relation.node_type.get_case_attributes()
            ])
        return ret

    @classmethod
    def _find_node_with_type(cls, type_name, exclude_list):
        '''
        Returns a list of node sublclasses having the given type_name.
        '''         
        ret = cls.has_type(type_name) and [cls] or []
            
        for relation in list(cls.iterchildrelations())+list(cls.iterrelations()):
            if relation.node_type in exclude_list:
                continue
            ret.extend(
                relation.node_type._find_node_with_type(
                    type_name, exclude_list
                )
            )
            
        if not ret:
            # Dont bother look thru this class again
            # even if it is used somewhere else in 
            # the node relations tree.
            exclude_list.append(cls)
            
        return ret
        