'''




'''

from kabaret.core.utils import get_user_name

from ... import QtCore, QtGui
from .. import ValueEditorMixin

class LoginListValueEditor(QtGui.QWidget, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QWidget.__init__(self, parent)
        
        self.setLayout(QtGui.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        self._label = QtGui.QLabel(self)
        self.layout().addWidget(self._label)
        
        self._original_tooltip = ''
        
        self._display_mode = options.get('display_mode', 'count') 
        self._currency = options.get('currency', 'user(s)')
        self._add_text = options.get('add', 'Add Me')
        self._remove_text = options.get('remove', 'Remove Me')
        self._is_in = None
        self._current_login = get_user_name()
        self._edited = None
        
        self._toggle_button = QtGui.QPushButton('Toggle', self)
        self._toggle_button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._toggle_button.customContextMenuRequested.connect(self._on_button_menu)
        self.layout().addWidget(self._toggle_button)
        
        ValueEditorMixin.__init__(self, controller, options)
        
    def _ui_widgets(self):
        return [self._label, self._toggle_button]

    def _set_read_only(self, b):
        self._toggle_button.setEnabled(not b)

    def get_value(self):
        if self._edited is None:
            return self._last_value_set
        return self._edited
    
    def set_value(self, value):
        ValueEditorMixin.set_value(self, value)
        self._update_tooltip()
        self._edited = None
        try:
            self._is_in = self._current_login in value
        except TypeError:
            self._is_in = False
        
        if self._display_mode == 'count':
            self._label.setText(self._get_display_count())
        else:
            self._label.setText(self._get_display_all())
        
        self._toggle_button.setText(self._is_in and self._remove_text or self._add_text)
    
    def _get_display_all(self):
        try:
            return ', '.join([ str(i) for i in (self._last_value_set or []) ])
        except:
            import traceback
            traceback.print_exc()
            return repr(self._last_value_set)
    
    def _get_display_count(self):
        try:
            return str(len(self._last_value_set or []))+' '+self._currency
        except:
            import traceback
            traceback.print_exc()
            return self._currency+': '+repr(self._last_value_set)
        
    def update_value(self, new_value):
        ValueEditorMixin.update_value(self, new_value)
        
    def _set_edit_connections(self):
        self._toggle_button.clicked.connect(self._do_toggle)

    def set_tooltip(self, text):
        self._original_tooltip = text
        self._update_tooltip()
    
    def _update_tooltip(self):
        ValueEditorMixin.set_tooltip(
            self, 
            self._original_tooltip+'<br><br>'+self._get_display_all()
        )
        
    def _do_toggle(self):
        try:
            self._edited = list(self._last_value_set)
        except TypeError:
            self._edited = []
        
        if self._is_in:
            try:
                self._edited.remove(self._current_login)
            except:
                import traceback
                print 'ERROR REMOVING USER FROM LIST:'
                traceback.print_exc()
                pass
        else:
            try:
                self._edited.append(self._current_login)
            except:
                import traceback
                print 'ERROR ADDING USER TO LIST:'
                traceback.print_exc()
                pass
            
        self.edit_finished()
    
    def _on_button_menu(self, pos):
        menu = QtGui.QMenu(self)
        menu.addAction('Add...', self._on_add_dialog)
        for i in self._last_value_set:
            if i != self._current_login:
                menu.addAction('Remove '+str(i), lambda v=i: self._on_remove(v))
        menu.exec_(self.mapToGlobal(pos))


    def _on_add_dialog(self):
        items, ok = QtGui.QInputDialog.getText(
            self, 'Add %s(s):'%(self._currency,), 'New %s:'%(self._currency,),
        )
        if not ok:
            return
        new_items = list(set([ i.strip() for i in items.split(' ') ]))

        try:
            self._edited = list(self._last_value_set)
        except TypeError:
            self._edited = []
        self._edited.extend(new_items)
        self.edit_finished()

    def _on_remove(self, item):
        try:
            self._edited = list(self._last_value_set)
        except TypeError:
            return # cannot remove from empty list :p
        
        try:
            self._edited.remove(item)
        except:
            import traceback
            print 'ERROR REMOVING USER FROM LIST:'
            traceback.print_exc()
            pass
        else:
            self.edit_finished()
            