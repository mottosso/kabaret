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

    The kabaret.flow.params.param module.
    Defines the Param and ParamValue classes.
    Nodes uses Param to hold values.
    Those value can be a references to another node's param value.
    
'''
import datetime
import contextlib

class ParamValue(object):
    '''
    The ParamValue contains the data associated to a node's Param.
    You access it with the get() method and modify it with the set() method.

    A ParamValue has a unique identifier in the flow, available by a call
    to the uid() method.
    
    A ParamValue can be connected to one or more other ParamValue with the
    add_source() method.
    Sources are ordered and may occur several times.
    When a single source is connected, the get() method will return the data of
    this source. If several sources are connected, a list of data is returned by
    the get() method.

    When a ParamValue has one or more sources, a call to the set(data) method will
    disconnect all sources and set the data.

    When a ParamValue is the source of some ParamValue, a call to the set() method
    will trigger a touch() on each of those ParamValue.

    After a touch(), the ParamValue is dirty and all ParamValue using this one as
    source is touched too. The Node owning the ParamValue is notified by a call
    to its param_touched() method.
    The ParamValue remains dirty until a set() is performed.

    A ParamValue can provide UI information with its ui_infos() method.
    (See Param.ui_infos() for more on this.)
    
    '''
    _PICKLED_TYPES = (
        int, basestring, type(None), float, long,
        datetime.date, datetime.datetime,
    )
    
    def __init__(self, param_name, node):
        '''
        Instantiates a ParamValue for the Param named 'param_name' in
        the node 'node'.
        
        You should not need to create ParamValues yourself: Param
        instances in the node class will do it for you.
        '''
        
        super(ParamValue, self).__init__()
        self.param_name = param_name
        self.node = node
        self.data = None
        self._dirty = True
        self.error = None
        
        self._disconnect_on_set = True
        self._source_as_dict = False
        self.downstreams = ()   # tuple of downstream param values
        self.upstreams = ()     # tuple of upstream param values
        self.upstreams_ids = () # tuple of upstream param's node.node_id
    
    def has_source(self):
        '''
        Returns True if this value has one or more connected
        source.
        '''
        return self.upstreams and True or False
    
    def add_source(self, source_param_value):
        '''
        Adds a source (upstream) ParamValue to this ParamValue.
        
        When a ParamValue has a single source, a call to get()
        will return the data returned by the source's get() method.
        
        If several sources were added, a list of all get() method
        returned values will be returned by this ParamValue's get()
        method.
        
        When the ParamValue's set() method is called, all sources
        are removed from the ParamValue.
        
        When a source's touch() method is called, the ParamValue's
        touch() method is called too.
        '''
        
        source_param_value._add_downstream(self)
        self._add_upstream(source_param_value)
        self.touch()

    def _add_downstream(self, param_value):
        '''
        Called by another ParamValue when it added this one
        to its sources.
        '''
        self.downstreams = self.downstreams+(param_value,)

    def _remove_downstream(self, param_value):
        '''
        Called by another ParamValue when it removed this one
        from its sources.
        '''
        dl = list(self.downstreams)
        try:
            dl.remove(param_value)
        except ValueError:
            raise ValueError('This is not in my downstreams %r (cannot remove it)'%(param_value,))
        else:
            self.downstreams = tuple(dl)
                    
    def _add_upstream(self, param_value):
        '''
        Called when another ParamValue is added to the sources
        ParamValue.
        '''
        self.upstreams = self.upstreams+(param_value,)
        if self._source_as_dict:
            self.upstreams_ids = self.upstreams_ids+(param_value.node.node_id,)

    def disconnect(self):
        '''
        Remove all source ParamValues.
        '''
        if 0:
            print 'DISCO', self.path()
            print 'ups'
            for up in self.upstreams:
                print '  ', up.path()
                print '    ', [ v.path() for v in up.downstreams ]
            print 'downs'
            for d in self.downstreams:
                print '  ', d.path()
                print '    ', [ v.path() for v in d.upstreams ]

        for up in self.upstreams:
            up._remove_downstream(self)
        self.upstreams = ()
        self.upstreams_ids = ()
        
    def rank(self):
        '''
        Returns an integer depicting the length of the longest
        dependency path in the parent.
        '''
        if not self.upstreams:
            return 0
        ranks = [
            pv.node.rank() 
            for pv in self.upstreams
            # Skeep local connections, and skip when same node or leaving parent: 
            if pv.node != self.node and pv.node._parent == self.node._parent
        ]
        return ranks and max(ranks)+1 or 0

    def set(self, data): #@ReservedAssignment
        '''
        Change the data held by this ParamValue.
        
        All sources ParamValue will be removed and further
        get() calls will return the given data.
        
        Every ParamValue using this one as source will be touched.
        
        This ParamValue will be touched inside this call but will
        not be dirty after this call.
        (So the flow is notified by a call to on_param_touched()
        right before the new value is set)
        
        '''
        if self._disconnect_on_set:
            self.disconnect()

        self.touch()        
        
        self.data = data
        self._set_clean()
            
    def set_error(self, err):        
        self.touch()
        self.error = err # do this after touch!
    
    def get_source_nodes(self):
        return [ up.node for up in self.upstreams ]
    
    def get_from_sources(self):
        '''
        Return the value from the sources.
        '''
        if self._source_as_dict:
            # when in dict mode, event one source
            # produces a dict:
            return dict([ 
                (up_id, up.get()) for up_id, up 
                in zip(self.upstreams_ids, self.upstreams) 
            ]) 
        else:
            # when not in dict mode, a single source
            # does not produce a list:
            try:
                self.upstreams[1]
            except:
                return self.upstreams[0].get()
            else:
                return [ up.get() for up in self.upstreams ]

    def get(self):
        '''
        Returns the data for this ParamValue.
        
        If no source were added with add_source(), the data
        attribute is returned.
        If a single source was added, it's get() return value
        is returned.
        If more than one source were added, a list of all their
        get() return value is returned.
        
        '''
        if self.has_source() or self._source_as_dict:
            ret = self.get_from_sources()
        else:
            ret = self.data
        if self._dirty:
            self._set_clean()
        return ret

    def get_display_value(self):
        value = self.get()
        return self._to_display(value)
    
    @classmethod
    def _to_display(cls, value):
        if not isinstance(value, cls._PICKLED_TYPES):
            if isinstance(value, (list, tuple)):
                value = type(value)([ cls._to_display(v) for v in value ])
            elif isinstance(value, dict):
                value = dict([ (k, cls._to_display(v)) for k, v in value.iteritems() ])
            elif hasattr(value, 'uid') and callable(value.uid):
                value = value.uid()
            else:
                value = repr(value)
        return value
        
    def is_dirty(self):
        '''
        Returns True if this ParamValue is dirty.
        '''
        return self._dirty
    
    def _upstream_cleaned(self):
        '''
        Called by a source param when it gets cleaned.
        Default behavior is to call touch.
        '''
        self.touch()
        
    def _set_clean(self):
        '''
        Called when a call to set() was made.
        The ParamValue is not dirty after this call and the 
        node owning this ParamValue is notified by a call to 
        param_cleaned().
        '''
        self._dirty = False
        self.error = None

    def touch(self):
        '''
        Sets this ParamValue dirty.
        The node owning this ParamValue is notified by
        a call to param_touched() and each ParamValue using
        this one as source is touched too.
        '''
        changed = not self._dirty
        self._dirty = True
        self.error = None
        self.node.param_touched(self.param_name)
            
        changed and self.node.flow().on_param_touched(self)
        [ pv.touch() for pv in self.downstreams ]
    
    def uid(self):
        '''
        Returns a unique identifier for this ParamValue in the
        flow containing it.
        The uid of the node owning this ParamValue can be obtained
        with this uid:
            node_uid = param_value_uid[:-1]
        '''
        return self.node.uid() + ('.'+self.param_name,)
    
    def path(self):
        '''
        Returns a file like path unique in the flow
        that designate this ParamValue.
        This is only for display purpose and cannot
        be used to later retrieve this ParamValue (use uid()
        for that).
        '''
        return '/'.join(self.uid())

    def ui_infos(self):
        '''
        Returns all the UI information for this ParamValue.
        See Param.ui_infos for more details.
        '''
        return self.node.get_param(self.param_name).ui_infos(self.node)

class ParamUiInfosBuilder(object):
    _INIT_INDEX = 10 # dont start at 0 so that subclass have space...
    
    def __init__(self):
        self.group = ''
        self.group_index = self._INIT_INDEX
        self.index = self._INIT_INDEX
    
    def reset(self):
        self.clear_group()
        self.group_index = self._INIT_INDEX
        
    def set_group(self, group, group_index=None):
        if self.group:
            raise Exception('Sorry, cannot nest Param ui groups')
        self.group = group
        if group_index is None:
            self.group_index += 1
        else:
            self.group_index = group_index
    
    def clear_group(self):
        self.group = ''
        self.index = self._INIT_INDEX
        
    def next_ui_infos(self):
        self.index += 1
        return {
            'label': None, 
            'editor': None,
            'group': self.group,
            'group_index': self.group_index,
            'index': self.index,
            'tags': [],
        }
        
@contextlib.contextmanager
def param_group(group, group_index=None):
    Param._UI_DEFAULTS.set_group(group, group_index)
    yield
    Param._UI_DEFAULTS.clear_group()

class Param(object):
    '''
    A Param is used to declare ParamValue in Node classes:
    
    class MyNode(Node):
        color = Param()
        size = Param()
        
    '''
    _VALUE_CLASS = ParamValue

    _UI_DEFAULTS = ParamUiInfosBuilder()

    @classmethod
    def _reset_ui_defaults(cls):
        cls._UI_DEFAULTS.reset()
        
    def __init__(self, default=None, sources_as_dict=False):
        '''
        The default argument may contain a callable that will
        be called upon value initialization.
        '''
        super(Param, self).__init__()
        self.name = None
        self.default = None
        self._sources_as_dict = sources_as_dict
        self._ui_infos = self.__class__._UI_DEFAULTS.next_ui_infos()
    
    def ui(self, label=None, editor=None, editor_options=None, group=None, group_index=None, index=None):
        if label is not None:
            self._ui_infos['label'] = label
        if editor is not None:
            self._ui_infos['editor'] = editor
        if editor_options is not None:
            self._ui_infos['editor_options'] = editor_options
        if group is not None:
            self._ui_infos['group'] = group
        if group_index is not None:
            self._ui_infos['group_index'] = group_index
        if index is not None:
            self._ui_infos['index'] = index
        return self
    
    def ui_infos(self, node=None):
        '''
        Returns a dict with all ui infos for this Param.
        (Modifying this dict will not afect the Param)
        You can use the ui() method to alter values returned
        by this method.
        
        If 'node' is not None, those additional informations
        are included:
            value: the ParamValue's data for this node.
            error: the ParamValue's error as string or None
            id: the ParamValue's uid for this node.
            path: the ParamValue's path for this node.
            upstreams: the list of ParmaValue uids connected to the ParamValue for this node.
            downstreams: the list of ParamValue uids connected to the ParamValue for this node.
        (If you hold the ParamValue, calling ui_infos() on it is easier.)
        
        '''
        ret = dict(self._ui_infos)
        ret['label'] = ret['label'] or self.name.title().replace('_', ' ')
        ret['name'] = self.name
        ret['param_type'] = self.__class__.__name__
        if node is not None:
            pv = self.get_value(node)
            ret['value'] = pv.get_display_value()
            ret['error'] = pv.error and str(pv.error) or None
            ret['id'] = pv.uid()
            ret['path'] = pv.path()
            ret['dirty'] = pv.is_dirty()
            ret['upstreams'] = [ d.uid() for d in pv.upstreams ]
            ret['downstreams'] = [ d.uid() for d in pv.downstreams ]
        return ret

    def tag(self, *tags):
        self._ui_infos['tags'] = tags
        return self
    
    def has_tag(self, *tags):
        '''
        Returns True if at least one of the given
        tags are set on this param.
        '''
        my_tags = self._ui_infos['tags']
        try:
            [ 1/0 for tag in tags if tag in my_tags ]
        except ZeroDivisionError:
            return True
        return False
    
    def auto_connect(self, node):
        '''
        Called when a node with this Param has been created.
        Subclasses may override this to implement default connections
        of the ParamValue.
        
        Default implementation does nothing.
        '''
        pass
    
    def get_value(self, node):
        '''
        Return the ParamValue for the given node.
        
        If the node does not already have a ParamValue for this
        Param, one is created using the '_VALUE_CLASS' class attribute.
        '''
        try:
            return node._param_values[self.name]
        except KeyError:
            pv = node._param_values[self.name] = self._VALUE_CLASS(self.name, node)
            pv.data = (callable(self.default) and (self.default() or 1) or self.default)
            pv._source_as_dict = self._sources_as_dict
        return pv
        
    def __get__(self, node, node_type=None):
        '''
        The Param being a descriptor, this method is called when
        accessing a Param instance from a node containing it:    
            pv = my_node.my_param  # pv is the ParamValue.
            
        also when called on the node's class:
            p = MyNode.my_param    # p is the Param instance.
         
        '''
        if node is None:
            return self
        return self.get_value(node)
    
    def __set__(self, node, value):
        '''
        This raises an AttributeError.
        If you want to set the data of a ParamValue, do it like this:
            my_node.my_param.set(data)
        '''
        raise AttributeError('Cannot override %s, you should use my_node.%s.set(<value>)'%(self.__class__.__name__,self.name))
    
    def apply_case(self, node):
        '''
        Called when the node owning this Param loads a
        case.
        This is used by the CaseParam subclass to set the
        ParamValue accordingly to the data in the case.
        
        Default implementation does nothing.
        '''
        pass
    
    def create_case(self):
        '''
        Called when the node owning this Param is building
        a case.
        This is used by the CaseParam subclass to add its 
        ParmaValue's data to the case.
        
        Default implementation does nothing.
        '''
        return {}


class ParentParam(Param):
    '''
    The ParentParam uses a Param in the node's parent as source.
    The connection is conveniently set on the node creation.
    '''
    
    class ParentAutoConnectError(AttributeError):
        def __init__(self, param, param_name, child_node):
            self.param = param
            self.param_name = param_name
            self.child_node = child_node
            super(ParentParam.ParentAutoConnectError, self).__init__(
                'Cannot find param %r in parent node of %r (%s) for ParentParam %r auto_connect'%(
                    param_name, child_node, child_node.path(), param.name
                )
            )

    def __init__(self, parent_param_name, default=None):
        super(ParentParam, self).__init__(default)
        self.parent_param_name = parent_param_name

    def auto_connect(self, node):
        if node._parent is None:
            #TODO: shouldn't we raise?
            return
        
        for param in node._parent.iterparams():
            if param.name == self.parent_param_name:
                parent_value = param.get_value(node._parent)
                self.get_value(node).add_source(parent_value)
                return
        
        #TODO: shouldn't we silently pass this?
        raise self.ParentAutoConnectError(self, self.parent_param_name, node)

