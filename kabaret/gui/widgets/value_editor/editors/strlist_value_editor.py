'''



'''

from ... import QtCore, QtGui
from .. import ValueEditorMixin


class StrListValueEditor(QtGui.QWidget, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QWidget.__init__(self, parent)

        self.item_name = options.get('item_name') or 'Item'

        self.presets = options.get('presets') or []
        
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(0)
        
        self.list = QtGui.QListWidget(self)
        self.list.setSelectionMode(self.list.ExtendedSelection)
        self.list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._on_menu)
        self.layout().addWidget(self.list)

        ValueEditorMixin.__init__(self, controller, options)
    
    def set_item_name(self, name):
        '''
        The given string will be used in menu and stuff.
        Default is 'Item'.
        '''
        self.item_name = name or 'Item'
        
    def _ui_widgets(self):
        return [self.list]

    def get_value(self):
        return [ str(self.list.item(i).text()) for i in range(self.list.count()) ]
    
    def set_value(self, value):
        ValueEditorMixin.set_value(self, value)
        
        if value is None:
            value = []
        if not isinstance(value, (list, tuple)):
            self.set_error('GUI ERROR: Not a tuple or list: %r'%(value,))
            value = []
            
        self.list.clear()
        self.list.addItems(value)
            
    def _set_edit_connections(self):
        pass

    def _set_read_only(self, b):
        self.list.setEnabled(not b)

    def _fill_menu(self, menu, current_item):
        menu.addAction('Add '+self.item_name, self._on_add)
        if current_item is not None:
            menu.addAction('Remove '+current_item.text(), self._on_menu_remove_selected)
        if self.presets:
            menu.addSeparator()
            for preset in self.presets:
                menu.addAction('Add '+str(preset), lambda v=str(preset):self._on_add_preset(v))
        
    def _on_menu(self, pos):
        menu = QtGui.QMenu(self)
        current_item = self.list.currentItem()
        self._fill_menu(menu, current_item)
        menu.exec_(self.mapToGlobal(pos))
    
    def _on_add(self, _=None):
        ids, ok = QtGui.QInputDialog.getText(
            self, 'Add %s:'%(self.item_name,), 'New %s (separate with space):'%(self.item_name,),
        )
        if not ok:
            return
        new_ids = list(set(ids.replace('-', '_').split(' ')))
        self.list.addItems(new_ids)
        self.edit_finished()
    
    def _on_add_preset(self, preset):
        self.list.addItem(preset)
        self.edit_finished()
        
    def _on_menu_remove_selected(self):
        selected_indexes = self.list.selectedIndexes()
        nb = len(selected_indexes)
        button = QtGui.QMessageBox.warning(
            self, 'Delete %s:'%(self.item_name,), 'Confirm Delete %d %s'%(nb, self.item_name,),
            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel
            
        )
        if button != QtGui.QMessageBox.Ok:
            return
        selected_ids = [ self.list.itemFromIndex(i).text() for i in selected_indexes ]
        ids = [ 
            self.list.item(i).text() 
            for i in range(self.list.count()) 
            if self.list.item(i).text() not in selected_ids
        ]
        self.list.clear()
        self.list.addItems(ids)
        self.edit_finished()
        