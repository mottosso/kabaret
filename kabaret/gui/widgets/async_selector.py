

from kabaret.core.utils import resources 
try:
    from . import QtCore, QtGui
except ValueError:
    # fucked relative import in non-package
    from kabaret.gui.widgets import QtCore, QtGui

    
class Selector(QtGui.QWidget):
    # NB: in the current state, this selector does not support several items
    # with the same label and different data :/
    try:
        selected = QtCore.Signal(str, object)
    except AttributeError:
        selected = QtCore.pyqtSignal(str, object)
    
    def __init__(self, help_text, parent):
        super(Selector, self).__init__(parent)
        
        self._label_to_data = {} # we don't use Qt's data because it returns a QVariant when queried :/
        
        self.setLayout(QtGui.QHBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        self._cb = QtGui.QComboBox(self)
        self.layout().addWidget(self._cb, stretch=10)
        self._cb.setEditable(True)
        
        self._help_text = help_text
    
        self.waitter = QtGui.QLabel('Loading')
        wait_movie = QtGui.QMovie(resources.get('gui.icons', 'throbber.gif'))
        self.waitter.setMovie(wait_movie)
        wait_movie.start()
        #self.waitter.hide()
        self.layout().addWidget(self.waitter)
        
        self.set_items([])
        
        self._cb.activated.connect(self._on_activated)
        
    def show_wait(self):
        self.waitter.show()
    
    def set_help_text(self, help_text):
        self._help_text = help_text
        self._cb.setItemText(0, self._help_text)

    def set_items_with_icon(self, items, icon_folder_name=None):
        self.clear()
        
        self._cb.addItem(self._help_text)
        help_text_index = self._cb.model().index(0, self._cb.modelColumn(), self._cb.rootModelIndex())
        help_text_item = self._cb.model().itemFromIndex(help_text_index)
        help_text_item.setSelectable(False)

        for label, icon_name, data in items:
            if icon_folder_name is not None and icon_name is not None:
                icon = resources.get_icon((icon_folder_name,icon_name), self._cb)
                self._cb.addItem(icon, label, data)
                self._label_to_data[label] = data
            else:
                self._cb.addItem(label, data)
                self._label_to_data[label] = data
            
        self.waitter.hide()

    def set_items(self, items):
        self.set_items_with_icon([ (i[0], None, i[1]) for i in items ])
        
    def _on_activated(self, index):
        try:
            # PySide version 1.1.1
            index = int(index)
        except ValueError:
            # PySide version 1.0.0
            label = str(index)
        else:
            label = str(self._cb.itemText(index))
        try:
            data = self._label_to_data[label]
        except KeyError:
            self._set_error('Not found: %r'%(label,))
        else:
            self._set_error(None)
            self.selected.emit(label, data)

    def _set_error(self, err_msg):
        if err_msg is None:
            self.setStyleSheet('')
            self.setToolTip('')
        else:
            self.setStyleSheet('QWidget { color: red; }')
            self.setToolTip(err_msg)
            
# what was this?!?:
#    def get_selected(self):
#        pass

    def clear(self):
        self._cb.clear()
        self._label_to_data = {}

    def setEditable(self, b):
        self._cb.setEditable(b)
    
    def select_value(self, value):
        '''
        Select the first item with the given value.
        The selected signal will be emitted.
        
        A ValueError is raised if no such item is found.
        '''
        label = None
        for l, v in self._label_to_data.items():
            if v == value:
                label = l
        if label is None:
            raise ValueError('Could not find an label for value %r'%(value,))
        
        for i in range(self._cb.count()):
            if self._cb.itemText(i) == label:
                self._cb.setCurrentIndex(i)
                self.selected.emit(label, value)
                return
        raise ValueError('Could not find an item with label %r'%(label,))
        
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    f = QtGui.QFrame(None)
    f.resize(500,500)
    f.setLayout(QtGui.QVBoxLayout())
    
    def on_select(label, data):
        print 'Selected:', label, data
        
    w = Selector('Select One of those...', f)
    w.selected.connect(on_select)
    f.layout().addWidget(w)

    def fill():
        items = [ ('Item '+str(i)+' hop', i) for i in range(50) ]
        w.set_items(items)
        
    def fetch():
        w.show_wait()
        QtCore.QTimer.singleShot(1000, fill)
        
    QtCore.QTimer.singleShot(1000, fetch)
            
    f.show()
    app.exec_()
    