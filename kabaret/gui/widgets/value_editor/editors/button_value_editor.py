'''



'''

from ... import QtCore, QtGui
from .. import ValueEditorMixin


class ButtonValueEditor(QtGui.QPushButton, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QPushButton.__init__(self, parent)
        ValueEditorMixin.__init__(self, controller, options)

    def set_label(self, label=None):
        if label is None:
            label = 'Trigger' 
        self.setText(label)
        
    def get_value(self):
        #print 'TRIGGER GET', self.value_id
        return None
    
    def set_value(self, value):
        #print 'TRIGGER SET', value, self.value_id
        pass
    
    def _set_edit_connections(self):
        self.clicked.connect(self.on_clicked)
    
    def on_clicked(self):
        #print 'TRIGGER CLICK', self.value_id
        self._controller.set_value(None)
        self.set_busy()

    def _set_read_only(self, b):
        pass
    