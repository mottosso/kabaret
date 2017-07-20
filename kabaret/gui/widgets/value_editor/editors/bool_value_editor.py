'''




'''

from ... import QtCore, QtGui
from .. import ValueEditorMixin


class BoolValueEditor(QtGui.QCheckBox, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QCheckBox.__init__(self, parent)
        ValueEditorMixin.__init__(self, controller, options)
        
        self.setText(options.get('caption', ''))
            
    def get_value(self):
        return self.isChecked()
    
    def set_value(self, value):
        ValueEditorMixin.set_value(self, value)
        self.setChecked(value and True or False)
            
    def _set_edit_connections(self):
        self.toggled.connect(self.edit_finished)

    def _set_read_only(self, b):
        self.setEnabled(not b)
