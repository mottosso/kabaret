'''


'''


from .node_tree import NodeTreePanel

from kabaret.gui.widgets.views import QtGui, QtCore, resources

class NodePicker(QtGui.QDialog):
    def __init__(self, parent, client, caption, default_root_name=None, extra_root_names={}):
        super(NodePicker, self).__init__(parent)
        
        self._allow_multiple = True
        
        self.setLayout(QtGui.QVBoxLayout())
        
        header = QtGui.QLabel(caption, self)
        self.layout().addWidget(header)
        
        self.tp = NodeTreePanel(self, client, extra_root_names)
        self.allow_multiple_selection(self._allow_multiple)
        self.layout().addWidget(self.tp)
        
        self.accept_button = QtGui.QPushButton('Accept', self)
        self.accept_button.clicked.connect(self.accept)
        self.layout().addWidget(self.accept_button)
    
        if client.connected():
            self.set_connected()
            self.tp.set_named_root(default_root_name)
        else:
            self.accept_button.setEnabled(False)
            
    def set_connected(self):
        self.tp.set_connected()
        self.accept_button.setEnabled(True)
        
    def set_dicconnected(self):
        self.tp.set_disconnected()
        self.accept_button.setEnabled(False)
        
    def allow_multiple_selection(self, b):
        '''
        If b is False, user can only select one id.
        The get_picked_ids() method will however still
        return a list of ids (with a single element...)
        '''
        self._allow_multiple = b
        if self._allow_multiple:
            self.tp.tree.setSelectionMode(self.tp.tree.MultiSelection)
        else:
            self.tp.tree.setSelectionMode(self.tp.tree.SingleSelection)

    def set_selected_ids(self, node_ids):
        for node_id in reversed(node_ids):
            found, item = self.tp.model.root().find(node_id)
            if not found:
                continue
            index = self.tp.model.createIndex(item.row(), 0, item)
            self.tp.sel_model.select(index, self.tp.sel_model.Select)
            self.tp.tree.scrollTo(index, self.tp.tree.EnsureVisible)
                        
    def get_picked_ids(self):
        indexes = self.tp.sel_model.selectedIndexes()
        return sorted(set([
            index.internalPointer().node_id() for index in indexes
        ]))
        