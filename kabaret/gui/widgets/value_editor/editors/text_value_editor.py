'''




'''

from ... import QtCore, QtGui
from .. import ValueEditorMixin


class VSizeGrip(QtGui.QWidget):
    def __init__(self, parent, target_widget):
        super(VSizeGrip, self).__init__(parent)
        self._target = target_widget
        self._press_pos = None
        self._press_height = None
                
    def mousePressEvent(self, e):
        self._press_pos = e.pos()
        self._press_height = self._target.height()
        
    def mouseMoveEvent(self, e):
        delta = e.pos() - self._press_pos;
        target = self._target
        target.setMinimumHeight(
            self._press_height + delta.y()
        )
        target.updateGeometry()
    

class TextValueEditor(QtGui.QWidget, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QWidget.__init__(self, parent)
        
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        self._textedit = QtGui.QTextEdit(self)
        self._textedit.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn # Needed to always see corner widget
        )
        resizer = VSizeGrip(self, self._textedit)
        self._textedit.setCornerWidget(resizer)
        self.layout().addWidget(self._textedit)
        
        self._apply_button = QtGui.QPushButton('Apply', self)
        self.layout().addWidget(self._apply_button)
        
        ValueEditorMixin.__init__(self, controller, options)
        
    def _ui_widgets(self):
        return [self._textedit]

    def edit_started(self):
        self._apply_button.setEnabled(True)
        return super(TextValueEditor, self).edit_started()
        
    def edit_finished(self):
        self._apply_button.setEnabled(False)
        return super(TextValueEditor, self).edit_finished()

    def get_value(self):
        return str(self._textedit.toPlainText())
            
    def set_value(self, value):
        ValueEditorMixin.set_value(self, value)
        self._textedit.setPlainText(value or '')
    
    def _set_edit_connections(self):
        self._textedit.textChanged.connect(self.edit_started)
        self._apply_button.clicked.connect(self.edit_finished)

