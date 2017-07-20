'''


'''

from kabaret.flow.params.param import Param, param_group
from kabaret.flow.params.case import CaseParam
from kabaret.flow.params.computed import ComputedParam
from kabaret.flow.params.trigger import TriggerParam

from kabaret.flow.relations.child import Child

from kabaret.flow.nodelib.status import StatusValue, StatusManager

from .named import NamedNode, FileNode
from .notes import NoteThread

class TaskGroupStatus(StatusManager):
    NYS = Child(StatusValue).set_progress(0)
    INV = Child(StatusValue).after(NYS).set_progress(1)
    WIP = Child(StatusValue).after(INV).set_progress(11)
    FIN = Child(StatusValue).after(WIP).set_progress(100)

class TaskGroup(NamedNode):
    ICON_NAME = 'action'

    with param_group('Tasks'):
        tasks_statuses = Param({}, sources_as_dict=True).ui(editor='status_sumary')
        tasks_progresses = Param({}, sources_as_dict=True)
        status = ComputedParam()
        progress = ComputedParam().ui(editor='percent')

    _status_manager = Child(TaskGroupStatus) # NB: this is a status summary, it does not affect a param 
    notes = Child(NoteThread)

    def _configure(self):
        super(TaskGroup, self)._configure()
        for _, child in self.iterchildren():
            if child.has_param('status'):
                self.tasks_statuses.add_source(child.status)
            if child.has_param('progress'):
                self.tasks_progresses.add_source(child.progress)

    def param_touched(self, param_name):
        if param_name == 'tasks_progresses':
            self.progress.touch()
            
        elif param_name == 'progress':
            self.status.touch()
            
    def compute(self, param_name):
        if param_name == 'progress':
            self.progress.set(
                self._status_manager.get_average_progress(
                    (self.tasks_progresses.get() or {}).values()
                )
            )
                
        if param_name == 'status':
            self.status.set(
                self._status_manager.get_status(
                    self.progress.get()
                )
            )

                   
class AbstractTask(FileNode):
    ICON_NAME = 'task'

    with param_group('Task'):
        status = CaseParam('NYS')
        status_choices = ComputedParam().ui(editor='choices_for', editor_options={'target_param':'status'})
        progress = ComputedParam().ui(editor='percent')
        up_to_date = ComputedParam().ui('Is up to date?', editor='bool')

    #_status_manager = Child(SpecificStatusManager).affects(status) subclasses must define this!
                
    def param_touched(self, param_name):
        if param_name in ('status'):
            self.status_choices.touch()
            self.progress.touch()
            return 
        
        super(AbstractTask, self).param_touched(param_name)

    def _is_up_to_date(self):
        prev_mtime = self.prev_mtime.get()
        if prev_mtime is None:
            return self.exists.get()
        else:
            mtime = self.mtime.get()
            if not mtime:
                return False
            else:
                delta = 60 # allow 60 second of delay.
                return self.mtime.get()+delta>self.prev_mtime.get()

    def compute(self, param_name):
        if param_name == 'progress':
            self.progress.set(
                self._status_manager.get_progress(self.status.get())
            )
             
        elif param_name == 'status_choices':
            self.status_choices.set(
                self._status_manager.get_choices(self.status.get())
            )

        elif param_name == 'up_to_date':
            self.up_to_date.set(self._is_up_to_date())

        else:
            super(AbstractTask, self).compute(param_name)


class HumanTaskStatus(StatusManager):
    NYS = Child(StatusValue).set_progress(0)
    
    INV = Child(StatusValue).after(NYS).set_progress(10)
    WIP = Child(StatusValue).after(INV).set_progress(50)
    RVW = Child(StatusValue).after(WIP).set_progress(60)
    RTK = Child(StatusValue).after(RVW).before(RVW).set_progress(80)
    APP = Child(StatusValue).after(RVW).set_progress(100)
    
    OOP = Child(StatusValue).set_progress(100)

class HumanTask(AbstractTask):
    with param_group('Assigned'):
        candidats = ComputedParam().ui(editor='choices_for', editor_options={'target_param':'user'})
        user = CaseParam().ui(editor='node_ref', editor_options={'root_name':'resources'})
        
    _status_manager = Child(HumanTaskStatus).affects(AbstractTask.status)
    
    def _configure(self):
        super(HumanTask, self)._configure()
        self.candidats.add_source(self.parent().user_groups)
    
    def compute(self, param_name):
        if param_name == 'candidats':
            if not self.candidats.has_source():
                self.candidats.set([])
            else:
                uids = self.candidats.get_from_sources()
                if uids is None:
                    self.candidats.set([])
                else:
                    nodes = [ self.flow().get(uid) for uid in uids ]
                    groups = [ n for n in nodes if n.has_param('users') ]
                    users = [ n.uid() for n in nodes if n.has_param('login') ]
                    [ users.extend(group.users.get() or []) for group in groups ]
                    self.candidats.set(sorted(set(users)))
        else:
            super(HumanTask, self).compute(param_name)

class BatchTaskStatus(StatusManager):
    WAIT_INPUT = Child(StatusValue).set_progress(0)
    IN_PROGRESS = Child(StatusValue).after(WAIT_INPUT).set_progress(50)
    DONE = Child(StatusValue).after(IN_PROGRESS).after(WAIT_INPUT).set_progress(100)
    

class BatchTask(AbstractTask):

    _status_manager = Child(BatchTaskStatus).affects(AbstractTask.status)
