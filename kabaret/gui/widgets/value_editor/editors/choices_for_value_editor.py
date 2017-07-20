'''



'''

from ... import QtCore, QtGui
from .. import ValueEditorMixin

#TODO: we should not talk about 'param' here, this is FLOW specific.

class ChoicesForEditor(QtGui.QWidget, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QWidget.__init__(self, parent)
        
        self._buttons = []    
        self.setLayout(QtGui.QVBoxLayout())
        
        self.target_param_name = options.get('target_param')
        if self.target_param_name is None:
            self.set_error('NO "target_param" value in the editor options!')
            target_value_id = None
        else:
            target_value_id = controller.value_id[:-1]+('.'+self.target_param_name,)
        controller.override_set_value_id(target_value_id)
        
        ValueEditorMixin.__init__(self, controller, options)
    
    def _ui_widgets(self):
        return self._buttons
    
    def get_value(self):
        return self._last_value_set
    
    def set_value(self, value):
        #print 'SET on CHOICE FOR, value:', repr(value)
        ValueEditorMixin.set_value(self, value)
        self.clear()
        self.build()
        
    def _set_edit_connections(self):
        pass
    
    def _set_read_only(self, b):
        for button in self._ui_widgets():
            button.setEnabled(b)
            
    def clear(self):
        lo = self.layout()
        while lo.count():
            li = lo.takeAt(0)
            w = li.widget()
            if w is not None:
                w.deleteLater()
            del li
        self._buttons = []

    def build(self):
        if not self._last_value_set:
            lb = QtGui.QLabel('No choice for '+self.target_param_name, self)
            self.layout().addWidget(lb)
            self._buttons.append(lb)
            return 
        
        for v in self._last_value_set:
            label = v
            if isinstance(label, tuple):
                #TODO: this sucks like dyson. find a cleaner way to handle uid choices
                label = '/'.join(label)
            elif not isinstance(label, basestring):
                label = repr(v)
            b = QtGui.QPushButton(label, self)
            self.layout().addWidget(b)
            b.clicked.connect(lambda checked=False, v=v: self.on_button_clicked(checked, v))
            self._buttons.append(b)
            
    def on_button_clicked(self, *args):
        if len(args) == 1:
            # pyside...
            value = args[0]
        else:
            # pyqt...
            value = args[-1]
        if self.target_param_name is None:
            return
        self._controller.set_value(value)
