'''


'''

import sys
import os
import Queue

#import maya.cmds
#import maya.utils

import Pyro4

import kabaret.core.ro.client
import kabaret.core.ro.worker
#from kabaret.core.events.event import Event

import kabaret.gui
QtCore, QtGui = kabaret.gui.import_qt()
import kabaret.gui.styles

import kabaret.gui.icons       # install generic icons @UnusedImport

#from ..flow_gui import tree_view
#from ..flow_gui import params_view



class _StdListener(object):
    def __init__(self, cb):
        self._cb = cb
        self._orig = None
        self.fallback = False
        
    def apply(self):
        raise NotImplementedError
    
    def remove(self):
        raise NotImplementedError
    
    def write(self, text):
        self._cb(text)
        if self.fallback and self._orig:
            self._orig.write(text)
        
class StdOutListener(_StdListener):
    def apply(self):
        if self._orig:
            return
        self._orig = sys.stdout
        sys.stdout = self

    def remove(self):
        sys.stdout = self._orig
        self._orig = None
        
class StdErrListener(_StdListener):
    def apply(self):
        if self._orig:
            return
        self._orig = sys.stderr
        sys.stderr = self
         
    def remove(self):
        sys.stderr = self._orig
        self._orig = None

class WorkerProcess(QtCore.QThread):
    try:
        write_out = QtCore.Signal(object)
        write_err = QtCore.Signal(object)
    except AttributeError:
        write_out = QtCore.pyqtSignal(object)
        write_err = QtCore.pyqtSignal(object)

    def __init__(self, queue):
        super(WorkerProcess, self).__init__()
        self.queue = queue
        
    def run(self):
        def on_out(txt):
            self.write_out.emit(txt)
        def on_err(txt):
            self.write_err.emit(txt)
            
        self._stdout = StdOutListener(on_out)
        self._stdout.apply()
        self._stderr = StdErrListener(on_err)
        self._stderr.apply()

        try:
            print 'Contacting Project', self.project_name
            project_url = kabaret.core.ro.url.For.project(self.project_name)
            project = kabaret.core.ro.url.resolve(project_url, local=False)
    
            print 'Starting Worker AppHost'
            apphost = kabaret.core.apphost.AppHost(project)
    
            print '\nClient ready.\n\n'
            
            print 'Getting app', self.app_name
            app = apphost.app(self.app_name)
            
            print 'Getting app command', self.cmd_name
            cmd = getattr(app.cmds, self.cmd_name)
            
            print 'Calling cmd with args:', self.args, '\n\n'
            ret = cmd(*self.args)
        
            print 'Result:', repr(ret)

        except Exception, err:
            on_err('Process Aborted on Error: %s'%(err,))
            raise
        else:
            print 'Process finished SUCCESSFULY !!!'


class MayaBatchWorker(kabaret.core.ro.worker.Worker):
    '''
    Override the default worker to use the current scene path
    as document.
    '''
    def __init__(self):
        super(MayaBatchWorker, self).__init__()
        self._work_queue = Queue.Queue(0)

    def receive_func(self, code):
        return self.execute(code)
    
    def execute(self, code):
        """Queue a piece of code in main thread."""
        #print '++WORKER EXEC IN THREAD ID', threading.currentThread().ident, threading.currentThread().name
        if 0:
            import maya.utils
            return maya.utils.executeDeferred(
                lambda code, ctx=self._exec_context: Pyro4.utils.flame.exec_function(code, "<remote-code>", ctx),
                code
            )
        elif 0:
            Pyro4.utils.flame.exec_function(code, "<remote-code>", self._exec_context)
        else:
            self._work_queue.put(
                ('execute', code)
                #lambda code=code, ctx=self._exec_context: Pyro4.utils.flame.exec_function(code, "<remote-code>", ctx)
            )
            
    def evaluate(self, expression):
        """Queues the evaluation of an expression and store the result in the '_' name."""
        #print '++WORKER EVAL IN THREAD ID', threading.currentThread().ident, threading.currentThread().name
        if 0:
            import maya.utils
            return maya.utils.executeDeferred(
                lambda expression, ctx=self._exec_context: eval(expression, ctx),
                expression
            )
        elif 0:
            return eval(expression, self._exec_context)
        else:
            self._work_queue.put(
                ('evaluate', expression)
                #lambda expression=expression, ctx=self._exec_context: eval(expression, ctx)
            )
            
    def get_document_name(self):
        import maya.cmds
        doc_name = maya.cmds.file(query=True, sceneName=True)
        #doc_name = self.evaluate('maya.cmds.file(query=True, sceneName=True)')
        #print 'REQUEST WORKER DOCUMENT', doc_name
        return doc_name


class MayaBatchClient(kabaret.core.ro.client.Client):
    CURRENT = None
    _WORKER_CLASS = MayaBatchWorker
    
    def __init__(self, project_name='DefaultProject'):
        super(MayaBatchClient, self).__init__(project_name)
        self._console = None
        self._exec_context = {'check_setup_scene':check_setup_scene}
        
    def _configure_worker(self, worker):
        worker._type = 'Maya Batch'
        worker.add_features('kabaret', 'mayabatch')

    def set_console(self, console_widget):
        self._console = console_widget
        
    def tick(self):
        status = super(MayaBatchClient, self).tick()

        # Process some work:
        nb_work = 0
        max_work_per_tick = 1
        while nb_work<max_work_per_tick:
            try:
                work = self._worker._work_queue.get_nowait()
            except Queue.Empty:
                break
            nb_work += 1
            self.do_work(work[0], work[1])
        return 'W:'+str(nb_work)+' '+status
        
    def do_work(self, wtype, wdata):
        self._worker.begin_busy()
        try:
            print '>>EXEC WORK IN THREAD ID', threading.currentThread().ident, threading.currentThread().name
            print "Recieved Work", wtype, wdata 
            if wtype == 'execute':
                Pyro4.utils.flame.exec_function(wdata, "<remote-code>", self._exec_context)
            elif wtype == 'evaluate':
                eval(wdata, self._exec_context)
        finally:
            self._worker.end_busy()


def ui_main():
    from kabaret.gui.standalone import main_window

    client = MayaBatchClient(None)
    client.connect_from_env()

    app = QtGui.QApplication([])
    app.setApplicationName('MayaBatchWorker')
    main_window = main_window.MainWindow(client)
    
    kabaret.gui.styles.apply_default_style()

    from kabaret.gui.widgets.views import (
        ConsoleView, ListenerView, ConnectionView, ScriptView, WorkersView
    )
    
    console_dock = main_window.create_docked_view(
        u"\u20AD", 'Console', ConsoleView, QtCore.Qt.BottomDockWidgetArea, 
        True, None
    )
    main_window.create_docked_view(
        u"\u20AD", 'Listener', ListenerView, QtCore.Qt.BottomDockWidgetArea, 
        False, None
    )
    main_window.create_docked_view(
        u"\u20AD", 'Connection', ConnectionView, QtCore.Qt.RightDockWidgetArea, 
        False, None
    )
    main_window.create_docked_view(
        u"\u20AD", 'Script', ScriptView, QtCore.Qt.BottomDockWidgetArea, 
        False, None
    )
    main_window.create_docked_view(
        u"\u20AD", 'Workers', WorkersView, QtCore.Qt.BottomDockWidgetArea, 
        True, None
    )

    client.set_console(console_dock.widget())
    
    main_window.show()
    ret = 0
    try:
        ret = app.exec_()
    finally:
        client.shutdown()
    import sys
    sys.exit(ret)
    


if __name__ == '__main__':
    print 'Starting Kabaret Batch GUI' 
    build_gui()
    