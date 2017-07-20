'''




'''

from kabaret.core.events.event import Event

from kabaret.gui.widgets import QtGui, QtCore

# import the definition and then the widget so that everything is registered:
from . import definition #@UnusedImport
from . import widgets    #@UnusedImport

class UserPanel(QtGui.QScrollArea):
    def __init__(self, parent, client):
        super(UserPanel, self).__init__(parent)
        self.client = client

        self.setWidgetResizable(True)
        self.setWidget(QtGui.QWidget(self))
        self.setFrameStyle(self.NoFrame)

        self.widget().setLayout(QtGui.QVBoxLayout())
        #self.widget().layout().setContentsMargins(0,0,0,0)

        self.definition = None
        
    def set_view(self, view_definition):
        self.clear()
        self.definition = view_definition
        self.definition.build(self.widget())
    
    def clear(self):
        if self.definition is not None:
            self.definition.clear()
        
        lo = self.widget().layout()
        while lo.count():
            li = lo.takeAt(0)
            w = li.widget()
            if w is not None:
                w.deleteLater()
            del li

