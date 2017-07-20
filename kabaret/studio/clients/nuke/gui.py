'''

from nukescripts import panels

import kabaret.gui.widgets.views as kviews

class NukeTestWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QVBoxLayout())
        
        self.script_view = kviews.ScroiptView(self, None, 'XXX')

        self.layout().addWidget(self.script_view)
        

panels.registerWidgetAsPanel('NukeTestWindow', 'Test table panel', 'uk.co.thefoundry.NukeTestWindow')



pane = nuke.getPaneFor('Properties.1')
pnl = panels.registerWidgetAsPanel('NukeTestWindow', 'Test table panel', 'uk.co.thefoundry.NukeTestWindow', True)
pnl.addToPane(pane)


---------

QtGui.QApplication.activeWindow().windowTitle()



-- print widgets

def pw(w, i=0):
 print i*'  ', w
 for c in w.children():
   pw(c, i+1)
pw(QtGui.QApplication.activeWindow())

=================================




from PySide import QtGui
import nukescripts.panels



class KabaretWindow(QtGui.QWidget):
    LAST = None
    COUNT = 0

    def __init__(self, parent=None):
        self.__class__.LAST = self
        self.__class__.COUNT += 1
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QVBoxLayout())
        self.mw = QtGui.QMainWindow(parent)
        self.layout().addWidget(self.mw)

nukescripts.panels.registerWidgetAsPanel('KabaretWindow', 'Kabaret', 'zob')


import kabaret.studio.clients.nuke.gui as gui
from kabaret.gui.widgets.main_window_manager import MainWindowManager
import kabaret.core.ro.client

client = kabaret.core.ro.client.Client(None)
client.connect_from_env()

KabaretWindow.LAST.manager = MainWindowManager(KabaretWindow.LAST.mw, client)

KabaretWindow.LAST.manager.install_standalone()

'''

#from PyQt4 import QtGui, QtCore
import kabaret.core.ro.client

from kabaret.gui.widgets import QtCore, QtGui
from kabaret.gui.widgets.main_window_manager import MainWindowManager
#import kabaret.gui.styles

from ..flow_gui import tree_view
from ..flow_gui import params_view

#class NukeMainWindowManager(MainWindowManager):
#    
#    def _install_menu_bar(self):
#        self.menu_bar = self._main_window.findChild(QtGui.QMenuBar)
#
#    def _install_status_bar(self):
#        self.status_bar = QtGui.QStatusBar(self._main_window)
#        self._main_window.layout().addWidget(self.status_bar)
#        self.status_bar.showMessage("Initializing", 1000)
#
#
#def take_over():
#    app = QtGui.QApplication.instance()
#    if not isinstance(app, QtGui.QApplication):
#        app.setOverriceCursor = lambda *args, **kwargs: None
#    
#    toplevel_window = QtGui.QApplication.activeWindow()
#    mw = QtGui.QMainWindow(None)
#    mw.show()
#    mw.nuke_window = toplevel_window
#    mw.setCentralWidget(toplevel_window)
#    
#    return mw

class KabaretPanel(QtGui.QMainWindow):
    _CLIENT = None
    
    def __init__(self, parent=None):
        super(KabaretPanel, self).__init__(parent)
        self.setSizePolicy(
            QtGui.QSizePolicy(
                QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding
            )
        )

        client = kabaret.core.ro.client.Client(None)
        client.connect_from_env()
        self.__class__._CLIENT = client
        main_window_manager = MainWindowManager(self, client)
        
        # Fine tune for Nuke:
        main_window_manager.USE_VIEW_MENU = False
        main_window_manager.SHOW_VIEW_TOOLBAR = True
        main_window_manager.TITLE_HAS_APP_NAME = False
        
        main_window_manager.install_parented()
        
        # install tree view
        main_window_manager.create_docked_view(
            'FLOW', 'Tree', tree_view.TreeView,
            QtCore.Qt.LeftDockWidgetArea, True, None
        )
            
        # install params view 
        main_window_manager.create_docked_view(
            'FLOW', 'Params', params_view.ParamsView,
            QtCore.Qt.RightDockWidgetArea, True, None
        )
        
        from kabaret.gui.widgets import views
        listener = main_window_manager.create_docked_view(
            u"\u20AD", 'Listener', views.ListenerView,
            QtCore.Qt.BottomDockWidgetArea, False, None
        )    
        console = main_window_manager.create_docked_view(
            u"\u20AD", 'Console', views.ConsoleView,
            QtCore.Qt.BottomDockWidgetArea, False, None
        )    
        script = main_window_manager.create_docked_view(
            u"\u20AD", 'Script', views.ScriptView,
            QtCore.Qt.BottomDockWidgetArea, False, None
        )
        main_window_manager.tabify_docked_view(listener, console, script)
        
        # goto current node:
        main_window_manager.client.set_focus_id_from_env()
        
def install():
    import nuke
    import nukescripts.panels
    
    nukescripts.panels._kabaret_studio_widget = KabaretPanel
    
    pane_name = 'Kabaret Studio'
    pane_id = 'com.supamonks.kabaret.studio'
    class Panel(nukescripts.panels.PythonPanel):
        def __init__(self):
            super(Panel, self).__init__(pane_name, pane_id)
            self.customKnob = nuke.PyCustom_Knob(
                pane_name, '', 
                '__import__("nukescripts").panels.WidgetKnob('
                    '__import__("nukescripts").panels._kabaret_studio_widget'
                ')'
            )
            self.addKnob(self.customKnob)
    
    addPanel = lambda: Panel().addToPane()
    menu = nuke.menu('Pane')
    menu.addCommand(pane_name, addPanel)

    nukescripts.panels.registerPanel(pane_id, addPanel)
    
    pane = nuke.getPaneFor('DAG.1')
    Panel().addToPane(pane)

            
            




