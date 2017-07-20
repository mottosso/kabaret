'''



'''

from ... import QtCore, QtGui
from .. import ValueEditorMixin


class ChoiceEditor(QtGui.QComboBox, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QComboBox.__init__(self, parent)
        
        self.choices = list(options.get('choices'))
        self.addItems([ str(i) for i in self.choices ])
 
        ValueEditorMixin.__init__(self, controller, options)
        
    def get_value(self):
        return self.choices[self.currentIndex()]
    
    def set_value(self, value):
        ValueEditorMixin.set_value(self, value)
        try:
            index = self.choices.index(str(value))
        except ValueError:
            self.addItem(str(value))
            self.choices.append(value)
            index = len(self.choices)
        self.setCurrentIndex(index)

    def _set_edit_connections(self):
        #self.currentIndexChanged.connect(self.edit_finished)
        self.currentIndexChanged.connect(self._on_change)

    def _set_read_only(self, b):
        self.setEnabled(not b)

    def _on_change(self):
        print 'CB ON CHANGE'
        self.edit_finished()
        