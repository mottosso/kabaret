'''



'''

import datetime

from kabaret.flow.params.param import Param, param_group
from kabaret.flow.params.case import CaseParam
from kabaret.flow.params.computed import ComputedParam
from kabaret.flow.relations.child import Child

from .task import TaskGroup


class Scheduled(TaskGroup):
    ICON_NAME = 'scheduled' 
    
    AFTER_PREV_END = 'After Previous End'
    AFTER_PREV_START = 'After Previous Start'
    FIXED_START = 'Fixed Start Date'
    SCHEDULE_MODES = (
        AFTER_PREV_END,
        AFTER_PREV_START, 
        FIXED_START,
    )
    
    with param_group('Planning'):
        schedule_mode = CaseParam().ui(editor='choice', editor_options={'choices':SCHEDULE_MODES})
        fixed_start_date = CaseParam().ui(editor='date')
        start_offset = CaseParam().ui(editor='int')
        start_date = ComputedParam().ui(editor='date')
        work_days = CaseParam().ui(editor='int')
        end_date = ComputedParam().ui(editor='date')
    
    with param_group('Planning Dependencies'):
        dep_start_dates = Param().ui(editor='date')
        dep_end_dates = Param().ui(editor='date')
    
    with param_group('Assigned'):
        manager = CaseParam().ui(editor='node_ref', editor_options={'root_name':'resources'})
        lead = CaseParam().ui(editor='node_ref', editor_options={'root_name':'resources'})
        user_groups = CaseParam().ui(editor='node_refs', editor_options={'root_name':'resources'})
    
    def add_dependency(self, scheduled):
        self.dep_start_dates.add_source(scheduled.start_date)
        self.dep_end_dates.add_source(scheduled.end_date)

    def param_touched(self, param_name):
        if param_name in (
                'schedule_mode', 'fixed_start_date', 'start_offset',
                'dep_start_dates', 'dep_end_dates'
            ):
            self.start_date.touch()
        elif param_name in ('start_date', 'work_days'):
            self.end_date.touch()
        else:
            return super(Scheduled, self).param_touched(param_name)
        
    def compute(self, param_name):
        if param_name == 'start_date':
            mode = self.schedule_mode.get()
            
            if mode == self.FIXED_START:
                self.start_date.set(
                    self.fixed_start_date.get()
                    +datetime.timedelta(self.start_offset.get() or 0)
                )
            
            elif not mode or mode == self.AFTER_PREV_END:
                prev_end = self.dep_end_dates.get()
                if prev_end is None:
                    raise Exception(
                        'Cannot use schedule mode %r without a dependency.'%(
                            mode,
                        )
                    
                    )
                self.start_date.set(
                    prev_end
                    +datetime.timedelta(self.start_offset.get() or 0)
                )
            
            elif mode == self.AFTER_PREV_START:
                prev_start = self.dep_start_dates.get()
                if prev_start is None:
                    raise Exception(
                        'Cannot use schedule mode %r without a dependency.'%(
                            mode,
                        )
                    
                    )
                self.start_date.set(
                    prev_start
                    +datetime.timedelta(self.start_offset.get() or 0)
                )
            
            else:
                raise Exception('Unknown Schedule Mode %r'%(mode,))
                
        elif param_name == 'end_date':
            start = self.start_date.get()
            if start is None:
                raise Exception('Cannot find end date without start date')
            self.end_date.set(
                start+datetime.timedelta(self.work_days.get() or 0)
            )
        
        else:
            return super(Scheduled, self).compute(param_name)
        