'''


'''

from ... import QtCore, QtGui
from .. import ValueEditorMixin

class IntValueEditor(QtGui.QSpinBox, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QSpinBox.__init__(self, parent)
        ValueEditorMixin.__init__(self, controller, options)

    def get_value(self):
        return self.value()
    
    def set_value(self, value):
        ValueEditorMixin.set_value(self, value)

        if value is None:
            value = 0
        try:
            self.setValue(value)
        except TypeError:
            import traceback
            traceback.print_exc()
            print '#-----> value was', value, 'in', self.value_id
            self.setValue(0)
            self.set_error('GUI ERROR: cannot display value %r'%(value,))
            
    def _set_edit_connections(self):
        self.valueChanged.connect(self.edit_started)
        self.editingFinished.connect(self.edit_finished)
