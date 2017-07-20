'''




'''

from ... import QtCore, QtGui
from .. import ValueEditorMixin


class GenericValueEditor(QtGui.QLineEdit, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QLineEdit.__init__(self, parent)
        ValueEditorMixin.__init__(self, controller, options)

        self.setAcceptDrops(True)

    def get_value(self):
        text = str(self.text())
        #print 'GET PY FROM TEXT:', repr(text)
        try:
            value = eval(text)
        except (SyntaxError, NameError), err:
            #print '  eval error', err
            value = text
        #else:
            #print '  eval ok'
        #print '  =>', repr(value)
        return value
            
    def set_value(self, value):
        #print 'SET PY FROM TEXT, value:', repr(value)
        ValueEditorMixin.set_value(self, value)

        if isinstance(value, basestring):
            display_value = value
        else:
            display_value = repr(value)
        self.setText(display_value)
    
    def _set_edit_connections(self):
        self.textEdited.connect(self.edit_started)
        self.returnPressed.connect(self.edit_finished)

    def dragEnterEvent(self, e):
        #TODO: this should be handled by the controller:
        if e.mimeData().hasFormat('kabaret/ids') or e.mimeData().hasFormat('text/plain'):
            e.accept()
        else:
            e.ignore() 

    def dropEvent(self, e):
        md = e.mimeData()
        #TODO: this has nothing to do here :/ let the controller handle it?
        if md.hasFormat('kabaret/ids'):
            #print 'using kabaret/ids'
            value = str(md.data('kabaret/ids')).split('\n')
            if len(value) < 2:
                value = value[0]
            self.setText(value)
        elif md.hasFormat('text/plain'):
            #print 'using text/plain'
            self.setText(e.mimeData().text())
        #TODO: decide if we use edit_finished() or just edit_started()
        if 0:
            self.setFocus()
            self.edit_started()
        else:
            self.edit_finished()
