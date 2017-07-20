'''



'''

from kabaret.gui.widgets import QtGui, QtCore

from . import Widget

@Widget.user_widget
class Tree(QtGui.QTreeView):
    def __init__(self, parent, manager, config):
        super(Tree, self).__init__(parent)
        self.manager = manager
