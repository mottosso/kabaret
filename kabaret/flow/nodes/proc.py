'''



'''

import sys

from .node import Node
from ..params.param import param_group
from ..params.stream import StreamParam
from ..params.computed import ComputedParam

class ExecutionError(Exception):
    def __init__(self, error):
        super(ExecutionError, self).__init__(str(error))
        self.original_error = error
        
class ExecutionContext(object):
    '''
    The ExecutionContext is a container for
    all informations needed by a ProcNode.execute()
    method.
    '''
    @classmethod
    def from_dict(cls, d):
        context = cls(d['proc_uid'])
        context.proc_doc = d.get('proc_doc', None)
        context.params = d['params']
        context.up_contexts = [ cls.from_dict(ud) for ud in d['up_contexts'] ]
        for ctx in context.up_contexts:
            ctx._set_down_context(context)
        context.allow_exec = d['allow_exec']
        context.why = d['why']
        context.needed_features = d['needed_features']
        context.document = d['document']
        context.needs_to_run = d['needs_to_run']
        context.why_needs_to_run = d['why_needs_to_run']
        context.run = d['run']
        return context
        
    def __init__(self, proc_uid):
        self.proc_uid = proc_uid
        self.proc_doc = None
        self.params = []
        self._down_context = None
        self.up_contexts = []
        self.allow_exec = True
        self.why = None
        self.needed_features = []
        self.document = None
        self.needs_to_run = False
        self.why_needs_to_run = None
        self.run = False
        
        self.visit_count = 0
        
    def to_dict(self):
        return {
            'proc_uid': self.proc_uid,
            'proc_doc': self.proc_doc,
            'params': self.params,
            'up_contexts': [ c.to_dict() for c in self.up_contexts ],
            'allow_exec': self.allow_exec,
            'depth_allow_exec': self.get_allow_exec(),
            'why': self.why,
            'needed_features': self.needed_features,
            'document': self.document,
            'depth_needed_features': self.get_needed_features(),
            'all_documents': self.get_all_documents(),
            'needs_to_run': self.needs_to_run,
            'why_needs_to_run': self.why_needs_to_run,
            'run': self.run,
        }
    
    def get_needed_features(self):
        return list(
            set(
                sum([ ctx.get_needed_features() for ctx in self.up_contexts ], self.needed_features)
            )
        )
    
    def get_allow_exec(self):
        if not self.allow_exec:
            return False
        for up_context in self.up_contexts:
            if not up_context.get_allow_exec():
                return False
        return True
    
    def get_all_documents(self):
        docs = set([self.document])
        for up_context in self.up_contexts:
            docs.update(up_context.get_all_documents())
        return docs
    
    def has_param(self, name):
        '''
        Returns True if a param with the given name exists in
        this context (up_contexts are not considered).
        '''
        for param in self.params:
            if param['name'] == name:
                return True
        return False
    
    def set_param(self, name, value, editor=None, editor_options=None, doc=None):
        '''
        Set a param with the given name and value to the context.
        If a param with the same name already exists, its value and other not-None 
        option are updated.
        ''' 
        # try editing an existing param first:
        for param in self.params:
            if param['name'] == name:
                param['value'] = value
                if editor is not None:
                    param['editor'] = editor
                    param['editor_options'] = editor_options
                    param['doc'] = doc
                return
        
        # param not found, create one:
        self.params.append({
            'name':name, 'value':value, 
            'editor':editor, 'editor_options':editor_options,
            'doc':doc
        })
    
    def get_value(self, name, default=None):
        '''
        Returns the value of the param 'name'.
        Returns 'default' if the param cannot be found.
        '''
        for param in self.params:
            if param['name'] == name:
                return param['value']
        return default

    def remove_param(self, param_name):
        new_params = [ p for p in self.params if p['name'] != param_name ]
        self.params = new_params
        
    def clear_params(self):
        self.params = []
    
    def find_up_context(self, proc_uid):
        for up_context in self.up_contexts:
            if up_context.proc_uid == proc_uid:
                return up_context
            uc = up_context.find_up_context(proc_uid)
            if uc is not None:
                return uc
        return None
    
    def _set_down_context(self, context):
        self._down_context = context
        
    def add_up_context(self, up_context):
        up_context._set_down_context(self)
        self.up_contexts.append(up_context)
    
    def get_up_context(self, proc_uid):
        for up_context in self.up_contexts:
            if up_context.proc_uid == proc_uid:
                return up_context
        return None
    
    def clear_up_contexts(self):
        self.up_contexts = []
    
    def get_root_context(self):
        if self._down_context is None:
            return self
        return self._down_context.get_root_context()
    
    def get_down_context(self):
        return self._down_context
    
    def is_root_context(self):
        return self._down_context is None
        
class ProcNode(Node):
    '''
    This ProcNode has no documentation... 
    It sucks and you should ask the Pipe Admin to fix it!
    '''
    ICON_NAME = 'proc' 
    
    NEEDED_FEATURES = []
    
    with param_group('Process Dependency'):
        proc_stream = StreamParam()
        needs_to_run = ComputedParam() # see _configure()
        why = ComputedParam()
    
    def _configure(self):
        super(ProcNode, self)._configure()
        # we can't use the ProcNode in its class definition
        # so we have to set this here instead of declaring
        # proc_stream = StreamParam(acceptable_node_types=(ProcNode,))
        self.proc_stream.change_acceptable_node_types((ProcNode,))
        
    def add_upstreams(self, *procs):
        '''
        Connect each ProcNode in 'procs' so that
        they will be executed prior to this one if 
        their "needs_to_run" param is True.
        '''
        for proc in procs:
            self.proc_stream.add_source(proc.proc_stream)
    
    def set_upstreams(self, *procs):
        self.proc_stream.disconnect()
        self.add_upstreams(*procs)
    
    def param_touched(self, param_name):
        if param_name == 'proc_stream':
            self.needs_to_run.touch()
            self.why.touch()
            
    def compute(self, param_name):
        if param_name in ('needs_to_run', 'why'):
            ups_needs_to_run = dict(
                [ 
                    (up.node_id, up.needs_to_run.get()) 
                    for up in self.get_up_procs()
                ]
            )
            needs_to_run, why = self._needs_to_run(ups_needs_to_run)
            self.needs_to_run.set(needs_to_run)
            self.why.set(why)
        else:
            return super(ProcNode, self).compute(param_name)
            
    def _needs_to_run(self, ups_needs_to_run):
        '''
        Returns a bool and a string.

        Called by compute('need_to_run') to get the computed value
        of the 'needs_to_run' and 'why' params.
        
        The ups_needs_to_run is a dict like {up_name (str): needs_to_run (bool), ...} 
        generated using the nodes returned by the get_up_procs() method. 
        '''
        for k, v in ups_needs_to_run.items():
            if v:
                return True, 'The dependency %r needs to run'%(k,)
        return False, 'No dependency needs to run'

    def _make_default_execution_context(self):
        '''
        Returns a default execution context.
        '''
        context = ExecutionContext(self.uid())
        context.proc_doc = self.__doc__
        context.needs_to_run = self.needs_to_run.get()
        context.why_needs_to_run = self.why.get()
        context.run = context.needs_to_run and True or False
        return context
    
    @classmethod
    def get_execution_context_from_dict(cls, d):
        return ExecutionContext.from_dict(d)
    
    def prepare(self, context=None):
        '''
        Prepare the execution of this ProcNode by
        generating (or updating) a execution context
        and returning it.
        
        If 'context' is not None, it must be a dict
        suitable for the ExecutionContext.from_dict()
        method and the returned context will be initialized
        from it.
        
        Subclasses should override the _prepare_execution_context
        method instead of this one.
        
        '''
        if context is None:
            context = self._make_default_execution_context()
        else:
            context = self.get_execution_context_from_dict(context)
        
        self._prepare_execution_context(context) # in-place edit of context
        
        return context
    
    def _prepare_execution_context(self, context):
        '''
        Prepares the context to be used by execute(context).
        Default implementation is to call validate_execution_context(context)
        and request_execution_features(context).
        
        '''
        if not context.run:
            context.clear_up_contexts()
            
        # When the context we prepare is the root context,
        # it means that the user requested the execution
        if not context.is_root_context() and not context.run:
            context.needed_features = []
            context.clear_params()
            context.allow_exec = True
            context.why = None
            return
        
        self.validate_execution_context(context)
        self.request_execution_features(context)
        self.request_execution_document(context)
        
        if context.run:
            self.collect_execution_contexts(context)
        
    def validate_execution_context(self, context):
        '''
        This method must set the context's 'allow_exec'
        attribute to True if the ProcNode authorizes 
        an execution using it.
        
        It must set is to False otherwise, and set its
        'why' attribute to a string explaining the reason 
        why the ProcNode cannot execute with this context.
        
        Default is to allow execution and clear the why
        attribute.
        
        Subclasses may use the context to request user input
        like this:
            if not context.has_param('confirm'):
                context.set_param(
                    'confirm', False, editor='bool', 
                    doc='You must confirm before execution!',
                )
                context.allow_exe = False
                context.why = 'Need confirmation'
                return
            else:
                if not context.get_value('confirm'):
                    context.allow_exec = False
                    context.why = 'Need confirmation'
                    return
                    
            context.allow_exec = True
            context.why = None
            return
        '''
        context.allow_exec = True
        context.why = None
    
    def request_execution_features(self, context):
        '''
        This method must set the context's 'needed_features'
        to a list of string that will let the execute()
        caller choose a suitable worker for it.
        
        Setting the 'needed_features' to an
        empty list should lead to a call to
        execute with None as worker argument.
        
        Default is to use a copy of the class'
        NEEDED_FEATURES attribute (which is
        an empty list here).
        '''
        context.needed_features = list(self.__class__.NEEDED_FEATURES)

    def request_execution_document(self, context):
        '''
        This method must set the context's 'document'
        to a string that will let the execute()
        caller choose a suitable worker for it.
        
        A document set to None means that any worker
        can be eligible.
        
        Default is to do nothing (So that if a value
        was set in _make_default_execution_context it
        will still apply).
        '''
        pass
    
    def get_up_procs(self, context=None):
        '''
        Returns a list of all up proc nodes.
        Default implementation is to return each
        node connected to the proc_stream param.
        
        Subclasses may want to override this to
        use other node param(s) or skip some
        upstream ProcNode depending on the given 
        execution context.
        
        The context argument is not always given
        and subclasses must handle a 'None' context 
        as the default.
        '''
        return self.proc_stream.get() or []
    
    def collect_execution_contexts(self, context):
        '''
        This method must add some execution contexts
        for each execution that needs to occur before
        this one.
        
        Default is to add each ProcNode returned by
        get_up_procs(context) if the needs_to_run 
        param is True
        
        Subclasses should not need to override this.
        (override get_up_procs method instead)
        ''' 
        for proc in self.get_up_procs(context):
            uid = proc.uid()
            up_context = context.get_root_context().find_up_context(uid)
            if up_context is None :
                up_context = proc._make_default_execution_context()
                context.add_up_context(up_context)
            else:
                up_context.visit_count += 1
                if up_context.visit_count > 1:
                    # already visited, continue
                    continue
            
            proc._prepare_execution_context(up_context)
            
    def execute(self, context, worker):
        '''
        Executes this ProcNode on the given worker 
        using an execution context build from the 'context'
        dict.
        
        The 'worker' object depends on the features
        requested by the context and must be provided
        by the caller.
        The bare minimum for an object to be a valid
        worker is an 'has_features' method accepting
        one argument: a list of string, and returning
        a boolean value.

        The 'context' argument must be a dict
        suitable for the ExecutionContext.from_dict()
        method and the returned context will be used to 
        call _execute(worker, context).

        This will call the preprocess, process
        and postprocess methods on all up context nodes
        and then on this one.
        
        If an error occurs in one of those methods, the 
        corresponding 'error' method will be called on all
        node that previously called the method:
            preprocess -> preprocess_error
            process -> process_error
            postprocess -> postprocess_error

        '''
        print 'EXECUTING PROC NODE', self.uid()
        print '   -> worker is', worker
        
        context = self.get_execution_context_from_dict(context)        
        if context.proc_uid != self.uid():
            raise ExecutionError(
                'This execution context is not meant for me but for %r. (I\'m %r)'%(
                    context.proc_uid,
                    self.uid()
                )
            )
        
        features = context.get_needed_features()
        if worker is None and features:
            raise ExecutionError(
                'No worker specified but the execution context needs some '
                'features.'
            )
        if worker is not None and not worker.has_features(features):
            raise ExecutionError(
                'Cannot execute on worker, features not fulfilled:\nworker: %r, context:%r'%(
                    worker.get_features(),
                    features
                )
            )
            
        self._visit_context_bottom_first(
            context, 'preprocess', args=(worker,), on_error='preprocess_error'
        )
        self._visit_context_bottom_first(
            context, 'process', args=(worker,), on_error='process_error'
        )
        self._visit_context_bottom_first(
            context, 'postprocess', args=(worker,), on_error='postprocess_error'
        )

    def _visit_context_top_first(self, context, to_call, args=(), on_error=None):
        '''
        Execute 'to_call' on each node in the execution context,
        from root to leaves. 
        
        If on_error is not None, it will be used as the 'to_call' argument
        of a _visit_context_bottom_first() call is case of exception, with
        the exception added to the arguments.
        If None, the exception will not be caught.
        
        (The 'to_call' and 'on_error' are the name of the method to call
        on the ProcNode in the context.)
        '''
        print 'VISITE TF', to_call, context.proc_uid, args
        try:
            getattr(self, to_call)(*(context,)+args)
        except Exception, err:
            if on_error is not None:
                (_type, _value, tb) = sys.exc_info()
                try:
                    self._visit_context_bottom_first(context, on_error, args=(args+(err,)))
                except Exception, err_err:
                    if err_err is err:
                        raise err, None, tb # raise with original traceback
                    else:
                        raise
            else:
                raise

        flow = self.flow()
        for up_context in context.up_contexts:
            up_proc = flow.get(up_context.proc_uid)
            up_proc._visit_context_top_first(up_context, to_call, args, on_error)

    def _visit_context_bottom_first(self, context, to_call, args=(), on_error=None):
        '''
        Execute 'to_call' on each node in the execution context,
        from leaves to root.

        If on_error is not None, it will be used as the 'to_call' argument
        of a _visit_context_bottom_first() call is case of exception, with
        the exception added to the arguments.
        If None, the exception will not be caught.
        
        (The 'to_call' and 'on_error' are the name of the method to call
        on the ProcNode in the context.)
        '''
        print 'VISITE BF', to_call, context.proc_uid, args
        flow = self.flow()
        for up_context in context.up_contexts:
            up_proc = flow.get(up_context.proc_uid)
            up_proc._visit_context_bottom_first(up_context, to_call, args, on_error)
                
        try:
            getattr(self, to_call)(*(context,)+args)
        except Exception, err:
            if on_error is not None:
                (_type, _value, tb) = sys.exc_info()
                try:
                    self._visit_context_top_first(context, on_error, args=(args+(err,)))
                except Exception, err_err:
                    if err_err is err:
                        raise err, None, tb # raise with original traceback
                    else:
                        raise
            else:
                raise
        
    def preprocess(self, context, worker):
        '''
        Do the ProcNode's preprocess.
        
        Default is to do nothing.
        '''
        pass
    
    def preprocess_error(self, context, worker, original_error):
        '''
        Called when an error occurred in the preprocess call of 
        this ProcNode or another ProcNode having an execution 
        context containing this one.
        
        Default is to raise the original error.
        
        Exception raised here are not caught and will stop
        the ProcNode execution.
        '''
        raise original_error
    
    def process(self, context, worker):
        '''
        Do the ProcNode's process.
        
        Default is to do nothing.
        '''
        pass
            
    def process_error(self, context, worker, original_error):
        '''
        Called when an error occurred in the process call of 
        this ProcNode or another ProcNode having an execution 
        context containing this one.
        
        Default is to raise original_error.
        
        Exception raised here are not caught and will stop
        the ProcNode execution.
        '''
        raise original_error
    
    def postprocess(self, context, worker):
        '''
        Do the ProcNode's postprocess.
        
        Default is to do nothing.
        '''
        pass

    def postprocess_error(self, context, worker, original_error):
        '''
        Called when an error occurred in the postprocess call of 
        this ProcNode or another ProcNode having an execution 
        context containing this one.
        
        Default is to raise original_error.
        
        Exception raised here are not caught and will stop
        the ProcNode execution.
        '''
        raise original_error
    

    
        