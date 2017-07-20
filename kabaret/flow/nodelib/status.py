'''





'''

from ..nodes.node import Node

from ..params.param import Param
from ..params.computed import ComputedParam
from ..params.case import CaseParam
from ..params.stream import StreamParam
from ..params.trigger import TriggerParam

from ..relations.child import Child


class StatusValue(Node):
    '''
    The StatusValue is meant to be a Child of a StatusManager and
    streamed with other StatusValue using the before and after methods:
    
        class MyNodeStatusManager(StatusManager):
            waiting = StatusValue().set_progress(0)
            in_progress = StatusValue().after(waiting).set_progress(50)
            to_validate = StatusValue().after(in_progress).before(in_progress).set_progress(75)
            canceled = StatusValue().after(waiting).after(to_validate).set_progress(100)
            done = StatusValue().after(to_validate).set_progress(100)
            
    '''
    
    status_stream = StreamParam()
    progress = Param()
    select = TriggerParam()
    
    def after(self, status_value_node):
        self.status_stream.add_source(status_value_node.status_stream)
    
    def before(self, status_value_node):
        status_value_node.after(self)
        
    def get_choices(self):
        return (
            [ n.node_id for n in self.status_stream.downstream_nodes() ]
        )
        
    def set_progress(self, progress):
        self.progress.set(progress)
        
    def trigger(self, param_name):
        if param_name == 'select':
            self.parent().set_status(self.node_id)
            
class StatusManager(Node):
    '''
    The Status Manager can convert a progress int (0->100)
    to a status name and vis-versa.
    It can also provide a list of allowed value for the next
    status.
    
    It does so using its Child nodes which all must be 
    StatusValue nodes.
    /!\ The StatusValue must be defined in a incrementing
    progress value order. This is needed to convert status
    to progress and to summarize statuses.
     
    The Node using the StatusManager must use one of its
    param with the manager's affects() method
    in order to get it updated:
    
        # Using the relation proxy:
        class MyWorkNode(Node):
            status = CaseParam()
            
            _status_manager = Child(MyWorkStatus).affects(status)
    
        # Using the _configure() method:
        class MyWorkNode(Node):
            status = CaseParam()
            
            _status_manager = Child(MyWorkStatus)
            
            def _configure(self):
                self._status_manager.affects(self.status)
        
    The StatusManager can provide a progress value and a list
    of next allowed status values.
    The Node using the manager can easily use them:
        
        class MyWorkNode(Node):
            status = CaseParam()
            progress = ComputedParam()
            status_choices = ComputedParam().ui(editor='choices_for', editor_options={'target_param':'status'})
            
            def param_touched(self, param_name):
                # when status changes, the status choices 
                # and progress are not valid anymore:
                if param_name in ('status',):
                    self.status_choices.touch()
                    self.progress.touch()
                    return 
                else:
                    super(MyWorkNode, self).param_touched(param_name)
                    
            def compute(self, param_name):
                # we delegate the computation
                # to the status manager:
                if param_name == 'progress':
                    self.progress.set(
                        self._status_manager.get_progress(self.status.get())
                    )
                     
                elif param_name == 'status_choices':
                    self.status_choices.set(
                        self._status_manager.get_choices(self.status.get())
                    )
                else:
                    super(Task, self).compute(param_name)

    The StatusManager can also be used to summarize statuses
    in ComputedParam:
        class MyNode(Node):
            status = ComputedParam()
            progress = ComputedParam()
            
            def _get_progresses(self):
                # Do whatever you need to get a list
                # of progress values here...
                
            def param_touched(self, param_name):
                # Be sure that the status in invalidated
                # when the progress changes:
                if param_name == 'progress':
                    self.status.touch()
    
            def compute(self, param_name):
                # Use the manager to summarize progress
                # and translate it to a status
                if param_name == 'progress':
                    self.progress.set(
                        self._status_manager.get_average_progress(
                            self._get_progresses()
                        )
                    )
                        
                if param_name == 'status':
                    self.status.set(
                        self._status_manager.get_status(
                            self.progress.get()
                        )
                    )
    NB: You may use a param linked to all nodes having a status
    to summarize and touch progress when it is touched, or a trigger
    that runs the progress update.
    Note however that the Many and One related nodes are only created 
    when needed first accessed so you cannot summarize this kind of
    relation by linking to the related node status.
    
    '''
    def _configure(self):
        self._target_status = None
        super(StatusManager, self)._configure()
        
    def affects(self, param):
        self._target_status = param
        
    def set_status(self, status_name):
        print '----------> set_status', status_name
        if self._target_status is not None:
            print '       ->', self._target_status
            self._target_status.set(status_name)
        
    def get_status(self, progress):
        #print '--->', self.uid(), 'GET STATUS FROM Pr:', progress
        ordered_relations = sorted(
            self.iterchildrelations(),
            cmp=lambda a,b: cmp(a.index, b.index)
        )
        last_name = None
        for relation in ordered_relations:
            status_value = self.get_child(relation.name)
            if last_name is None:
                last_name = relation.name
                #print '   -> default:', last_name
            if status_value.progress.get() <= progress:
                last_name = relation.name
                #print '   -> passing:', last_name
                continue
            #print '  !!-> not passed:', relation.name, status_value.progress.get()
            break
        if last_name is None:
            # No child!?!
            return 'NO_STATUS'
        #print '    => last passed', last_name
        return last_name
            
    def get_progress(self, status_name):
        if status_name is None:
            return 0
        try:
            status = self.get_child(status_name)
        except KeyError:
            return 0
        else: 
            return status.progress.get()
        
    def get_choices(self, status_name):
        if status_name is None:
            status_name = self.get_status(0)
        try:
            status_value_node = self.get_child(status_name)
        except KeyError:
            choices = [self._child_relations[0].name]
        else:
            choices = status_value_node.get_choices()
        return choices

    @classmethod
    def get_average_progress(cls, progresses=[]):
        '''
        Returns the average progress of all given
        progresses.
        If progresses is empty, 100 is returned.
        '''    
        if progresses:
            return sum(progresses)/len(progresses)
        else:
            return 100
        
#
# ------------- EXAMPLE MANAGER DEFINITION:
#
#class TaskGroupStatus(StatusManager):
#    NYS = Child(StatusValue).set_progress(0)
#    INV = Child(StatusValue).after(NYS).set_progress(1)
#    WIP = Child(StatusValue).after(INV).set_progress(11)
#    FIN = Child(StatusValue).after(WIP).set_progress(100)
#    
#class BatchTaskStatus(StatusManager):
#    WAIT_INPUT = Child(StatusValue).set_progress(0)
#    IN_PROGRESS = Child(StatusValue).after(WAIT_INPUT).set_progress(50)
#    DONE = Child(StatusValue).after(IN_PROGRESS).after(WAIT_INPUT).set_progress(100)
#    
#class HumanTaskStatus(StatusManager):
#    NYS = Child(StatusValue).set_progress(0)
#    
#    INV = Child(StatusValue).after(NYS).set_progress(10)
#    WIP = Child(StatusValue).after(INV).set_progress(50)
#    RVW = Child(StatusValue).after(WIP).set_progress(60)
#    RTK = Child(StatusValue).after(RVW).before(RVW).set_progress(80)
#    APP = Child(StatusValue).after(RVW).set_progress(100)
#    
#    OOP = Child(StatusValue).set_progress(100)
    
    