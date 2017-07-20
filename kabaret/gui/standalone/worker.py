'''



'''

import sys
import Queue
import threading
import Pyro4

import kabaret.core.ro.client
import kabaret.core.ro.worker

from kabaret.core.utils import resources

import kabaret.gui
QtCore, QtGui = kabaret.gui.import_qt()
import kabaret.gui.styles

import kabaret.gui.icons       # install generic icons @UnusedImport

from kabaret.gui.widgets.views import (
    ConsoleView, ListenerView, ConnectionView, ScriptView, 
    WorkQueueView
)
from kabaret.gui.widgets.main_window_manager import MainWindowManager

ENV_WORKER_TYPE = 'KABARET_WORKER_TYPE'
ENV_WORKER_FEATURES = 'KABARET_WORKER_FEATURES'


class BatchWorker(kabaret.core.ro.worker.Worker):
    '''
    Override the default worker to queue execution and evaluation.
    '''
    def __init__(self, client):
        super(BatchWorker, self).__init__(client)
        self._work_queue = Queue.Queue(0)
        
    def receive_func(self, code):
        return self.execute(code)
    
    def execute(self, code):
        """Queue a piece of code in main thread."""
        self._work_queue.put(
            ('execute', code)
        )
            
    def evaluate(self, expression):
        """Queues the evaluation of an expression and store the result in the '_' name."""
        self._work_queue.put(
            ('evaluate', expression)
        )
    
    def get_document_name(self):
        '''
        Returns None, a work queue does not have a specific
        document...
        '''
        return None

    def do_work(self, wtype, wdata):
        self.begin_busy()
        try:
            self.checkpoint()
            print '>>EXEC WORK IN THREAD ID', threading.currentThread().ident, threading.currentThread().name
            print "Recieved Work", wtype, wdata 
            if wtype == 'execute':
                Pyro4.utils.flame.exec_function(wdata, "<remote-code>", self._exec_context)
            elif wtype == 'evaluate':
                eval(wdata, self._exec_context)
        finally:
            self.end_busy()
        self.checkpoint()

class BatchClient(kabaret.core.ro.client.Client):
    CURRENT = None
    _WORKER_CLASS = BatchWorker
    
    def __init__(self, project_name='DefaultProject', worker_type='???', worker_features=[]):
        self.worker_type = worker_type
        self.worker_features = worker_features
        
        super(BatchClient, self).__init__(project_name)
        
    def _configure_worker(self, worker):
        worker._type = self.worker_type
        worker.add_features(*self.worker_features)

    def on_worker_checkpoint(self, message, step_number, nb_steps):
        QtGui.qApp.processEvents()
        super(BatchClient, self).on_worker_checkpoint(message, step_number, nb_steps)
        if self.is_embedded_worker_paused():
            self._wait_for_worker_to_unpause()
            
        # tick the client without pulling a new work from queue:
        super(BatchClient, self).tick()
        
        QtGui.qApp.processEvents()

    def _wait_for_worker_to_unpause(self):
        import time
        while self.is_embedded_worker_paused():
            QtGui.qApp.processEvents()
            time.sleep(0.1)
        
    def tick(self):
        status = super(BatchClient, self).tick()

        # Process one work if possible:
        try:
            work = self._worker._work_queue.get_nowait()
        except Queue.Empty:
            pass
        else:
            # This will not return until work is done, but
            # UI will be updated on each worker checkpoint...
            self._worker.do_work(work[0], work[1])
        return 'W:'+str(self._worker._work_queue.qsize())+' '+status
        
def show_ui(client, app_name=None, ui_setup=None, **options):    
    app_name = app_name or client.worker_type
    
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName(app_name)
    w = QtGui.QMainWindow()
    w.setWindowTitle(app_name)
    w.setWindowIcon(resources.get_icon(('gui.icons', 'kabaret_logo_32x32')))

    main_window_manager = MainWindowManager(w, client)
    main_window_manager.install_standalone()
    
    main_window_manager.create_docked_view(
        u"\u20AD", 'Console', ConsoleView, QtCore.Qt.LeftDockWidgetArea, 
        options.get('Console'), None
    )
    main_window_manager.create_docked_view(
        u"\u20AD", 'Listener', ListenerView, QtCore.Qt.BottomDockWidgetArea, 
        options.get('Listener'), None
    )
    main_window_manager.create_docked_view(
        u"\u20AD", 'Connection', ConnectionView, QtCore.Qt.RightDockWidgetArea, 
        options.get('Connection'), None
    )
    main_window_manager.create_docked_view(
        u"\u20AD", 'Script', ScriptView, QtCore.Qt.BottomDockWidgetArea, 
        options.get('Script'), None
    )
    main_window_manager.create_docked_view(
        u"\u20AD", 'Work Queue', WorkQueueView, QtCore.Qt.RightDockWidgetArea, 
        options.get('Work Queue'), None
    )
    
    if ui_setup is not None:
        ui_setup(main_window_manager)
    
    w.resize(600, 400)
    w.show()
    try:
        client.connect_from_env()
    except ValueError, err:
        print err, 'Showing Connection Dialog...'
        main_window_manager.show_connect_dialog()
    else:
        main_window_manager.update_window_title()
    
    return app.exec_()




def startup(
        app_name,
        project_name, 
        worker_type='Kabaret Worker', worker_features=['python','kabaret'], 
        ui_setup=None, 
        verbose=True, **options
    ):
    ui_options = {
        'verbose':True,
        'Connection':False,
        'Listener':False,
        'Script':False,
        'Console':True,
        'Work Queue':True,
    }
    ui_options.update(options)

    import traceback
    client = None
    
    try:
        print
        print 'Initializing Kabaret Client'
        client = BatchClient(project_name, worker_type, worker_features)
        print 'Ok.'
        
        try:
            ret_code = show_ui(client, app_name, ui_setup, **ui_options)
        except Exception, err:
            msg = 'There was an unhandled error in GUI: %s\nClosing GUI.'%(err,)
            if verbose:
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            print msg
            ret_code = 1
            
    except Exception, err:
        msg = 'There was an error while starting a service: %s'%(err,)
        if verbose:
            msg += '\n'+traceback.format_exc()
        else:
            msg += '\nUse -v or --verbose to see the traceback\n'
        print msg
        ret_code = 2
        
    finally:
        if client is not None:
            client.shutdown()
    
    return ret_code

if __name__ == '__main__':
    project_name = None
    print 'Launching Kabaret Worker.'
    sys.exit(startup(app_name='Kabaret Worker', project_name=None, ui_setup=None, verbose=True))
