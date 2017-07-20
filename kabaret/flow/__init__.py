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
    The kabaret.flow package.
    
    This package is used to model and enact a graph that represent the workflow
    and the dataflow of a project.
    
    The flow is composed of nodes.
    
    A node contains some params with value that can be connected to other 
    node's param values, or computed by the node itself.
    
    Each created node exists for a given 'case'.
    The case drives the value of some of the node params.
    
    A Case can contain sub-case.
    
    The nodes are related to each other:
      - a node can contain child nodes that build up it behavior and functionalities.
      - a node can contain case nodes that exists depending of the parent case.

    The node tree describe the dataflow with the node params and the workflow
    with the cases, relations and status params.
    The root of this tree is known by a specialized Flow.
    This Flow can be passed along for querying, data manipulation and status 
    management (like interactive gantt chart, reporting tools, render farm, etc...)
    
    In a nutshell, what the developer needs to do is:
        - Subclass Node, adding some Param to implement logic
        and dependencies. Those nodes will provide tools, action
        and stuffs like that.
        - Subclass Node to represent the work entities. Those
        nodes will contain some tool node declared in previous step, 
        and relations that ties them together.
        - Subclass CaseData to bind some parameter value with a
        persistence thing (BDD, other python package, ...)
        - Subclass Flow to generate your root class.
        - Give an instance of your flow class (or the class itself)
        to the tools using it.
    Once done, several users will enjoy triggering actions based on 
    a common and official flow (with local cpu munching only :p) and
    automatic status update (thanks to the external case data storage).
    
'''

import time # for ticks
import weakref # for ticks

from .case import CaseData


class _Ticker(object):
    def __init__(self, min_sec_timelapse):
        super(_Ticker, self).__init__()
        self.min_sec_timelapse = min_sec_timelapse
        self._last_tick_time = None
        self._registry = []
        self._dirty = False
        
    def register(self, o):
        ticked_meth = getattr(o, 'tick', None)
        if not callable(ticked_meth):
            raise self.TickerRegisterError('The object %r does not have a callable "tick" attr.'%(o,))

        self._registry.append(weakref.ref(o, self._on_death))
        #print 'REGISTERING TICKED (got %s so far): %r'%(len(self._registry), o)
    
    def _on_death(self, ref):
        self._dirty = True
    
    def flush(self):
        self._registry = [ ref for ref in self._registry if ref() is not None ]
        self._dirty = False
        
    def tick(self):
        if self._last_tick_time:
            t = time.time()
            if t-self._last_tick_time < self.min_sec_timelapse:
                return
        else:
            t = time.time()
        
        self._last_tick_time = t
        if self._dirty:
            self.flush()
        [ ref().tick() for ref in self._registry ]
        print '>>> TICKED', len(self._registry), 'objects', 'in', time.time()-t, 'seconds'
        
class Flow(object):
    '''
    A Flow instances holds the root node and is 
    accessible from any node in the graph.
    
    You will want to subclass it to add functionalities
    that all nodes can use and implement the get_root_class() method.
    
    A Flow instance receives a call to on_param_touched() 
    whenever a Param of a Node related to the flow's root is
    touched (its value is invalidated).
    Subclass can override this method to exploit this information
    (for example to refresh a UI).
    
    The register_ticked() method can be used to make the flow
    call the tick() method of any object periodically.
    Additionally, one can call the tick() method to trigger a 
    tick() call on all the registered object.
    
    '''
    def __init__(self, project_name):
        super(Flow, self).__init__()
        self.project_name = project_name
        self._root = None
        self._root_class = None
        self._ticker = _Ticker(5)
        
    def set_root_class(self, root_class):
        self._root_class = root_class

    def get_root_class(self):
        '''
        Returns the flow root node class.
        Subclasses must implement this.
        '''
        if self._root_class is None:
            raise ValueError('No root class configured for the Flow %s'%(self,))
        return self._root_class
    
    def init_root(self, case, node_id=None):
        '''
        Initialize and returns the flow root with the given case.
        One must call this before any call to get(node_uid).
        Calling this more than once will raise an Exception.
        '''
        if self._root is not None:
            raise Exception('Root already created for this flow.')
        
        root_class = self.get_root_class()
        root = root_class(None, node_id)
        root._flow = self
        root.set_case(case)
        root._init_relations()
        self._root = root
        return self._root
    
    def register_ticked(self, o):
        '''
        Registers the object o to the ticked object list.
        Those objects will have their tick() method called
        on various occasions.
        
        The Param class has a set_ticked() method that will
        make the node owning the param receive a call to 
        param_ticked(param_name) on each tick.
        '''
        self._ticker.register(o)
    
    def tick(self):
        self._ticker.tick()
        
    def get_type(self, node_uid):
        '''
        Returns the type (class) of the node having the given uid
        in this flow.
        
        A call to init_root() must have been done before this one.
        '''
        if self._root is None:
            raise RuntimeError('Cannot get a Node from uid before a call to init_root(case)')

        try:
            root_id = node_uid[0]
        except IndexError:
            # empty uid is used to get the root type
            return self._root.__class__
        
        if root_id != self._root.node_id:
            raise ValueError(
                'The node uid %r does not point to a Node inside the root %r'%(
                    node_uid, self._root.uid()
                )
            )
        return self._root.get_type(node_uid[1:])

    def get(self, node_uid):
        '''
        Returns the node having the given uid in this flow.
        
        A call to init_root() must have been done before this one.
        '''        
        if self._root is None:
            raise RuntimeError('Cannot get a Node from uid before a call to init_root(case)')
        
        try:
            root_id = node_uid[0]
        except IndexError:
            # empty uid is used to get the root
            return self._root
        
        if root_id != self._root.node_id:
            raise ValueError(
                'The node uid %r does not point to a Node inside the root %r'%(
                    node_uid, self._root.uid()
                )
            )
        return self._root.get(node_uid[1:])
    
    def get_current_user(self):
        '''
        Utility function that returns the user login
        from the environment.
        '''
        import os
        try:
            return os.environ['USERNAME'] # windows
        except:
            return os.environ['USER']     # useful OS
        
    def on_param_touched(self, param_value):
        '''
        Called by a ParamValue when it is touched.
        '''
        self.tick()
        
    