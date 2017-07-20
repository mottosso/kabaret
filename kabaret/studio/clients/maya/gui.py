

import maya.cmds
import maya.utils

import Pyro4

import kabaret.core.ro.client
import kabaret.core.ro.worker
from kabaret.core.events.event import Event

import kabaret.gui
QtCore, QtGui = kabaret.gui.import_qt()
import kabaret.gui.styles

import kabaret.gui.icons       # install generic icons @UnusedImport

from ..flow_gui import tree_view
from ..flow_gui import params_view
from ..flow_gui import search_view
from kabaret.gui.widgets import views

#ENV_CURRENT_NODE = 'KABARET_CURRENT_NODE'

class Throbber(object):
    def __init__(self):
        self.steps = '_.oO*,_'
        self.steps = '/-|/-\\|'
        self.nb_steps = len(self.steps)
        self.step = self.nb_steps
        self.msg = None
        
    def advance(self):
        self.step += 1
    
    def set_message(self, msg):
        self.msg = msg
        
    def __str__(self):
        if self.msg:
            return '%s %s'%(self.steps[self.step%self.nb_steps], self.msg)
        else:
            return self.steps[self.step%self.nb_steps]

class MayaWorker(kabaret.core.ro.worker.Worker):
    '''
    Override the default worker to use the current scene path
    as document.
    '''

    def execute(self, code):
        """execute a piece of code when maya gets idle"""
        import maya.utils
        maya.utils.executeDeferred(
            lambda code, ctx=self._exec_context: Pyro4.utils.flame.exec_function(code, "<remote-code>", ctx),
            code
        )
        
    def evaluate(self, expression):
        """evaluate an expression and return None"""
        import maya.utils
        return maya.utils.executeDeferred(
            lambda expression, ctx=self._exec_context: eval(expression, ctx),
            expression
        )

    def get_document_name(self):
        import maya.cmds
        doc_name = maya.cmds.file(query=True, sceneName=True)
        #doc_name = self.evaluate('maya.cmds.file(query=True, sceneName=True)')
        print 'REQUEST WORKER DOCUMENT', doc_name
        return doc_name or None

class MayaClient(kabaret.core.ro.client.Client):
    CURRENT = None
    _WORKER_CLASS = MayaWorker
    
    def _configure_worker(self, worker):
        worker._type = 'Maya GUI'
        worker.add_features('kabaret', 'mayabatch', 'maya')
    
class MayaParamsView(params_view.ParamsView):
    def __init__(self, *args, **kwargs):
        super(MayaParamsView, self).__init__(*args, **kwargs)
        self.hide_path_label(False)


def install():
    tll = QtGui.QApplication.instance().topLevelWidgets()
    mwl = [ tl for tl in tll if tl.__class__.__name__ == 'QMainWindow' ]
    if not mwl:
        raise Exception('Could not find the Main Window. Kabaret Client installation aborted.')
    main_window = mwl[0]

    client = MayaClient(None)
    MayaClient.CURRENT = client
    client.connect_from_env()
    
    from kabaret.gui.widgets.main_window_manager import MainWindowManager
    main_window_manager = MainWindowManager(main_window, client)
    
    # Fine tune for maya:
    main_window_manager.USE_VIEW_MENU = True
    main_window_manager.SHOW_VIEW_TOOLBAR = True
    main_window_manager.TITLE_HAS_APP_NAME = True
    
    main_window_manager.install_embedded()
    
    # install tree views
    tree_dock = main_window_manager.create_docked_view(
        'FLOW', 'Tree', tree_view.TreeView,
        QtCore.Qt.LeftDockWidgetArea, True, None
    )
    
    # install tree views
    search_dock = main_window_manager.create_docked_view(
        'FLOW', 'Search', search_view.SearchView,
        QtCore.Qt.LeftDockWidgetArea, False, None
    )
    
    # install params views    
    params_dock = main_window_manager.create_docked_view(
        'FLOW', 'Params', MayaParamsView,
        QtCore.Qt.RightDockWidgetArea, False, None
    )
    
    # install work queue views    
    work_queue_dock = main_window_manager.create_docked_view(
        u"\u20AD", 'Work Queue', views.WorkQueueView, 
        QtCore.Qt.RightDockWidgetArea, False, None
    )
    
    # arrange the docks within maya docks:
    for dock in main_window.findChildren(QtGui.QDockWidget):
        if dock.widget() and dock.widget().objectName() == 'MainToolSettingsLayout':
            main_window_manager.tabify_docked_view(dock, tree_dock, search_dock)
        elif dock.widget() and dock.widget().objectName() == 'MainChannelsLayersLayout':
            main_window_manager.tabify_docked_view(dock, params_dock, work_queue_dock)
    
    # goto current node:
    main_window_manager.client.set_focus_id_from_env()

    