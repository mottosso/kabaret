
from kabaret.gui.widgets.views import QtGui, QtCore

class History(object):
    def __init__(self, max_len):
        self._max_len = max_len
        self._prevs = []
        self._nexts = []
        self.current = None
    
    def set_current(self, v):
        if v == self.current:
            return
        if self.current is not None:
            self._prevs.append(self.current)
            if len(self._prevs) > self._max_len:
                self._prevs.pop(0)
        self.current = v
        self._nexts = []
    
    def prev(self):
        if not self._prevs:
            return self.current
        
        self._nexts.append(self.current)
        self.current = self._prevs.pop()
        
        return self.current
    
#    def get_prev(self):
#        if not self._prevs:
#            return self.current
#        return self._prevs[-1]
        
    def next(self):
        if not self._nexts:
            return self.current
        
        self._prevs.append(self.current)
        self.current = self._nexts.pop()
        
        return self.current

#    def get_next(self):
#        if not self._nexts:
#            return self.current
#        return self._nexts[-1]
            
    def can_prev(self):
        return self._prevs and True or False
    
    def can_next(self):
        return self._nexts and True or False
    
    
class PathLabel(QtGui.QWidget):
    HISTORY_LEN = 20
    
    try:
        node_id_clicked = QtCore.Signal(tuple)
    except AttributeError:
        node_id_clicked = QtCore.pyqtSignal(tuple)

    _button_ss = '''
    QPushButton {
        padding: 2px;
        margin: 0px;
        height: 1em;
        border: 0px;
        /*border: 3px solid red;*/
        border-radius: 0px;
        background: transparent;
    }
    QPushButton[is_leaf_sep="true"] {
        border: 1px outset palette(midlight);
    }
    QPushButton[is_leaf_sep="false"] {
        border: none;
    }
    QPushButton:hover {
        padding: 1px;
        border: 1px inset palette(midlight);
    }
    QPushButton:menu-indicator {
        image: none;
        width: 0px;
    }        
    '''
    

    def __init__(self, parent=None):
        super(PathLabel, self).__init__(parent)
        self.node_id = None
        
        self.setLayout(QtGui.QHBoxLayout())

        self._labels_layout = QtGui.QHBoxLayout()
        self._labels_layout.setSpacing(0)

        self._prev_butt = QtGui.QPushButton('<', self)
        self._prev_butt.clicked.connect(self._on_prev)
        self._next_butt = QtGui.QPushButton('>', self)
        self._next_butt.clicked.connect(self._on_next)
        button_lo = QtGui.QHBoxLayout()
        button_lo.setSpacing(0)
        button_lo.addWidget(self._prev_butt)
        button_lo.addWidget(self._next_butt)
        
        self.layout().addLayout(button_lo)
        self.layout().addLayout(self._labels_layout)
        self.layout().addStretch(100)
        
        self.parts = []
        self._history = History(self.HISTORY_LEN)

        self.clear() # update buttons state
        
    def _on_prev(self):
        self.node_id_clicked.emit(self._history.prev())
        
    def _on_next(self):
        self.node_id_clicked.emit(self._history.next())
        
    def clear(self):
        self.node_id = None
        lo = self._labels_layout
        while lo.count():
            w = lo.takeAt(0).widget()
            if w is not None: # might be a spacer
                w.deleteLater()
        
        self._prev_butt.setEnabled(self._history.can_prev())
        self._next_butt.setEnabled(self._history.can_next())
        
    def set_node_id(self, node_id):
        if self.node_id == node_id:
            return
        self._history.set_current(node_id)
        self._apply_node_id()
        
    def _apply_node_id(self):
        self.clear()
        
        self.node_id = self._history.current
        
        lo = self._labels_layout
        curr_id = []
        clickable_max_index = len(self.node_id)-2
        for i, part in enumerate(self.node_id):
            curr_id.append(part)
            if i > clickable_max_index:
                b = QtGui.QLabel(part, self)
            else:
                b = QtGui.QPushButton(part+'/', self)
                b.clicked.connect(lambda checked=False, nid=tuple(curr_id):self._clicked(checked, nid))
            b.setStyleSheet(self._button_ss)
            lo.addWidget(b)
    
        lo.addStretch(100)
        
    def _clicked(self, *args):
        if len(args) == 1:
            # pyside...
            node_id = args[0]
        else:
            # pyqt...
            node_id = args[-1]
 
        #print 50*'#', node_id
        self.node_id_clicked.emit(node_id)
        