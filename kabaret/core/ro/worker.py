

import Pyro4.utils.flame

from kabaret.core.project.station_config import get_station_class
from kabaret.core.utils import get_user_name

from . import this_host

class Worker(object):
    '''
    A Worker purpose is to execute code triggered 
    by the AppHost connected to it.
    '''
    
    class STATUS:
        INIT = 'Initializing'
        WAITING = 'Waiting'
        BUSY = 'Busy'
        ERROR = 'Error'
    
    def __init__(self, client):
        super(Worker, self).__init__()
        self._client = client
        self._id = None
        self._exec_context = None
        self.clear_namespace()
        
        self._type = 'unknown'
        self._features = ['python']
        self._status = self.STATUS.INIT
        self._paused = False
    
    def ping(self):
        return 'pong'

    def set_id(self, worker_id):
        self._id = worker_id
    
    def get_id(self):
        return self._id

    def get_type(self):
        return self._type

    def get_station_class(self):
        return get_station_class()
    
    def add_features(self, *features):
        self._features.extend(features)
        
    def has_features(self, features):
        return set(features).issubset(self.get_features())   

    def get_features(self):
        return set(self._features)
    
    def get_document_name(self):
        '''
        Subclasses must override this to return
        the path of the document accessible by this worker.
        If no document is accessible (free worker), None
        must be returned
        
        Default is to return None.
        '''
        return None
    
    def get_status(self):
        return self._status

    def get_host(self):
        return this_host()
        
    def get_user(self):
        return get_user_name()

    def get_infos(self):
        return {
            'type': self.get_type(),
            'features': self.get_features(),
            'document': self.get_document_name(),
            'status': self.get_status(),
            'station_class': self.get_station_class(),
            'host': self.get_host(),
            'user': self.get_user(),
            'paused': self.is_paused(),
        }
        
    def set_waiting(self):
        self._status = self.STATUS.WAITING
        
    def begin_busy(self):
        self._status = self.STATUS.BUSY
    
    def is_busy(self):
        return self._status == self.STATUS.BUSY
    
    def end_busy(self):
        self._status = self.STATUS.WAITING
    
    def set_paused(self, b):
        self._paused = b

    def is_paused(self):
        return self._paused
    
    def clear_namespace(self):
        self._exec_context = {'WORKER': self}
        
# DUPLICATE OF begin_busy & end_busy !?!
#    def start_process(self):
#        self._status = self.STATUS.BUSY
#    
#    def end_process(self):
#        self._status = self.STATUS.WAITING

    def set_focus_id(self, focus_id):
        self._client.set_focus_id(focus_id)

    def checkpoint(self, message='', step_number=0, nb_steps=0):
        print 'WORKER CHECKPOINT:', message, '(%s/%s)'%(step_number, nb_steps)
        self._client.on_worker_checkpoint(message, step_number, nb_steps)
        
    def receive_func(self, code):
        '''
        Add the function declared by the given
        code to the execution context.
        '''
        # NB: we use a different method than execute() because
        # some subclass may want to override execute() without
        # affecting this one (The MayaWorker actually does that)
        Pyro4.utils.flame.exec_function(code, "<remote-code>", self._exec_context)
        
    def execute(self, code):
        """execute a piece of code"""
        Pyro4.utils.flame.exec_function(code, "<remote-code>", self._exec_context)

    def evaluate(self, expression):
        """evaluate an expression and return its result"""
        return eval(expression, self._exec_context)
    