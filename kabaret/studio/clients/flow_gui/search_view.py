'''




'''
import os
import datetime

from kabaret.core.events.event import Event
from kabaret.core.utils import get_user_name

from kabaret.gui.widgets.async_selector import Selector
from kabaret.gui.widgets.views import AbstractGuiView, QtGui, QtCore, resources

from . import node_picker


class WhereField(QtGui.QWidget):
    VARS = (
        ('$me', '"USER" in os.environ and os.environ["USER"] or os.environ["USERNAME"]'),
        ('$today', 'datetime.date.today()'),
        ('$now', 'datetime.datetime.now()'),
    )
    
    def op_eq(self):
        return self._get_value()
    
    def op_neq(self):
        return ('$!', self._get_value())
    
    def op_in(self):
        return ('$in', self._get_tuple_value())
    
    def op_nin(self):
        return ('$!in', self._get_tuple_value())
    
    def op_has(self):
        return ('$has', self._get_value())
    
    def op_hasnt(self):
        return ('$!has', self._get_value())
    
    def op_sup(self):
        return ('$>', self._get_value())
    
    def op_inf(self):
        return ('$<', self._get_value())
    
    def op_is_user(self):
        return self._get_user_value()
    
    def op_isnt_user(self):
        return ('$!', self._get_user_value())

    def op_has_user(self):
        return ('$has', self._get_user_value())

    def op_hasnt_user(self):
        return ('$!has', self._get_user_value())

    def op_is_None(self):
        return None
    
    OPS = (
        ('is', op_eq), 
        ('is not', op_neq), 
        ('is in', op_in), 
        ('is not in', op_nin), 
        (None, None),
        ('is user', op_is_user),
        ('is not user', op_isnt_user),
        ('contains user', op_has_user),
        ('does not contain user', op_hasnt_user),
        ('is not set', op_is_None),
        (None, None),
        ('contains', op_has),
        ('does not contain', op_hasnt),
        (None, None),
        ('is >', op_sup), 
        ('is <', op_inf),
        
    )
    def __init__(self, parent, attr, on_remove):
        super(WhereField, self).__init__(parent)
        
        self.setLayout(QtGui.QHBoxLayout())
        self.layout().setContentsMargins(16,0,0,0)
        
        self.label = QtGui.QLabel(attr, self)
        self.layout().addWidget(self.label)
        
        self._op = self.op_eq
        self.op_butt = QtGui.QPushButton(self)
        got_default = False
        menu = QtGui.QMenu(self.op_butt)
        self.op_butt.setMenu(menu)
        for name, op in self.OPS:
            if name is None:
                menu.addSeparator()
                continue
            action = QtGui.QAction(name, self.op_butt)
            action.triggered.connect(lambda name=name, op=op: self.set_op(name, op))
            menu.addAction(action)
            if not got_default:
                self.set_op(name, op)
                got_default = True
        self.layout().addWidget(self.op_butt)
        
        self.le = QtGui.QLineEdit(self)
        self.le.setAcceptDrops(True)
        self.le.dragEnterEvent = self._le_dragEnterEvent
        self.le.dropEvent = self._le_dropEvent
        self.le.dragMoveEvent = self._le_dragMoveEvent
        self.layout().addWidget(self.le)

        self._on_remove_func = on_remove
        self.remove_butt = QtGui.QToolButton(self)
        self.remove_butt.setText('X')
        self.remove_butt.clicked.connect(self._on_remove)
        self.layout().addWidget(self.remove_butt)
    
    def _get_value(self):
        return self._to_python(str(self.le.text()))
    
    def _to_python(self, text):
        v = text
        for alias, value in self.VARS:
            v = v.replace(alias, value)
        try:
            v = eval(v)
        except (NameError, SyntaxError):
            if '/' in v:
                #TODO: this sucks.
                v = tuple(v.split('/'))
        return v
        
    def _get_tuple_value(self):
        return tuple([ self._to_python(i.strip()) for i in str(self.le.text()).split(',') if i.strip() ])
    
    def _get_user_value(self):
        user = self._get_value()
        try:
            if not user[0:1] == ('Project', 'resources'):
                user = ('Project', 'resources', 'users:'+user)
        except:
            user = ('Project', 'resources', 'users:'+self.le.text())
        return user
        
    def _on_remove(self):
        self._on_remove_func(self)
        self.deleteLater()

    def drop(self):
        self._on_remove()

    def set_op(self, name, op):
        self._op = op
        self.op_butt.setText(name)

    def get_attr(self):
        return self.label.text()
    
    def get_clause(self):
        return {str(self.label.text()): self._op(self)}

    def _le_dragEnterEvent(self, e):
        if e.mimeData().hasFormat('kabaret/ids'):
            e.accept()
        else:
            e.ignore() 

    def _le_dragMoveEvent(self, e):
        if e.dropAction() == QtCore.Qt.LinkAction:
            e.accept()
            
    def _le_dropEvent(self, e):
        md = e.mimeData()
        if md.hasFormat('kabaret/ids'):
            value = str(md.data('kabaret/ids')).split('\n')
            self.le.setText(value[0])

    def to_preset(self):
        return {
            'param': self.label.text(),
            'op_name': self.op_butt.text(),
            'op_value': self.le.text(),
        }
    
    def apply_preset(self, preset):
        self.label.setText(preset['param'])
        op_name = preset['op_name']
        self.set_op(op_name, dict(self.OPS)[op_name])
        self.le.setText(preset['op_value'])
        
class SubPath(QtGui.QWidget):
    def __init__(self, parent, sup_path, on_remove):
        super(SubPath, self).__init__(parent)

        self.setLayout(QtGui.QHBoxLayout())
        self.layout().setContentsMargins(16,0,0,0)

        self.label = QtGui.QLabel(sup_path, self)
        self.layout().addWidget(self.label)

        self._on_remove_func = on_remove
        self.remove_butt = QtGui.QToolButton(self)
        self.remove_butt.setText('X')
        self.remove_butt.clicked.connect(self._on_remove)
        self.layout().addWidget(self.remove_butt)

        self.layout().addStretch(100)
    
    def get_label(self):
        return str(self.label.text())
    
    def get(self):
        return tuple(str(self.label.text()).split('.'))
    
    def _on_remove(self):
        self._on_remove_func(self)
        self.deleteLater()
    
    def drop(self):
        self._on_remove()
        
class NodeQueryBuilder(QtGui.QWidget):
    def __init__(self, parent, client):
        super(NodeQueryBuilder, self).__init__(parent)
        self.client = client
    
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        under_lo = QtGui.QHBoxLayout()
        
        lb = QtGui.QLabel('Under:', self)
        under_lo.addWidget(lb)
        
        self.under_id_le = QtGui.QLineEdit(self)
        self.under_id_le.setToolTip('Specify the path like:\n Project/work/films:FILM/seqs:S01\nor None')
        self.under_id_le.returnPressed.connect(self._on_under_changed)
        self.under_id_le.setAcceptDrops(True)
        self.under_id_le.dragEnterEvent = self._under_id_le_dragEnterEvent
        self.under_id_le.dropEvent = self._under_id_le_dropEvent
        self.under_id_le.dragMoveEvent = self._under_id_le_dragMoveEvent
        under_lo.addWidget(self.under_id_le)
        tb = QtGui.QToolButton(self)
        tb.setText('...')
        tb.setIcon(resources.get_icon(('flow.icons.nodes', 'casting')))
        tb.pressed.connect(self._on_under_dialog)
        under_lo.addWidget(tb)
        self.layout().addLayout(under_lo)
        
        find_lo = QtGui.QHBoxLayout()
        
        lb = QtGui.QLabel('Find:', self)
        find_lo.addWidget(lb)
        
        self._type_name = None
        self.type_name_select = Selector('Select Node Type', self)
        self.type_name_select.setEditable(False)
        self.type_name_select.selected.connect(self._on_select_type_name)
        find_lo.addWidget(self.type_name_select)
        self.layout().addLayout(find_lo)
        
        self.where_bt = QtGui.QToolButton(self)
        self.where_bt.setText('Where    ')
        self.where_bt.setPopupMode(self.where_bt.InstantPopup)
        self._attr_menu = QtGui.QMenu(self.where_bt)
        self.where_bt.setMenu(self._attr_menu)
        self.layout().addWidget(self.where_bt)
        
        self.where_lo = QtGui.QVBoxLayout()
        self._wheres = []
        self.layout().addLayout(self.where_lo)

        self.sub_path_bt = QtGui.QToolButton(self)
        self.sub_path_bt.setText('Select    ')
        self.sub_path_bt.setPopupMode(self.sub_path_bt.InstantPopup)
        self._sub_path_menu = QtGui.QMenu(self.sub_path_bt)
        self.sub_path_bt.setMenu(self._sub_path_menu)
        self.layout().addWidget(self.sub_path_bt)

        self.sub_path_lo = QtGui.QVBoxLayout()
        self._sub_path_ws = []
        self.layout().addLayout(self.sub_path_lo)

        self.waitter = None
    
    def set_waitter(self, waiter_widget):
        self.waitter = waiter_widget
        
    def _on_under_dialog(self):
        np = node_picker.NodePicker(
            self,
            self.client,
            'Select the Node to search in',
        )
        np.allow_multiple_selection(False)
        under_id = self.get_under_id()
        if under_id:
            np.set_selected_ids([under_id])
        result = np.exec_()
        if result == np.Accepted:
            picked_ids = np.get_picked_ids()
            if not picked_ids:
                id_str = ''
            else:
                id_str = '/'.join(picked_ids[0])
            self.under_id_le.setText(id_str)
            self._on_under_changed()
        np.deleteLater()
        
    def _on_under_changed(self):
        self.load_type_names()
        
    def _on_select_type_name(self, label, type_name):
        self._type_name = str(label)
        self.load_attribute_names()
    
    def show_wait(self):
        self.waitter.show()
        self.type_name_select.setEnabled(False)
        self.under_id_le.setEnabled(False)
        self.where_bt.setEnabled(False)
        self.sub_path_bt.setEnabled(False)
        
    def hide_wait(self):
        self.waitter.hide()
        self.type_name_select.setEnabled(True)
        self.under_id_le.setEnabled(True)
        self.where_bt.setEnabled(True)
        self.sub_path_bt.setEnabled(True)
        
    def load_type_names(self):
        self.type_name_select.show_wait()
        with self.client.result_to(self._fill_type_names_selector):
            self.client.apps.FLOW.cmds.GetNodeTypeNames(case_nodes_only=True, under=self.get_under_id())

    def load_attribute_names(self):
        self.show_wait()
        with self.client.result_to(self._update_attrs_menu):
            self.client.apps.FLOW.cmds.GetCaseAttributes(self.get_type_name())

    def _update_attrs_menu(self, attrs):
        self._attr_menu.clear()
        menus = {}
        self._sub_path_menu.clear()
        sp_menus = set()
        for attr in ['node_id']+attrs:
            if '.' in attr:
                path, param  = attr.rsplit('.', 1)
                if path not in sp_menus:
                    self._sub_path_menu.addAction(
                        path, lambda path=path: self.add_sub_path(path)
                    )
                    sp_menus.add(path)
                menu = menus.get(path)
                if menu is None:
                    menu_path = []
                    parent_menu = self._attr_menu
                    for name in path.split('.'):
                        menu_path += name
                        menu = menus.get('.'.join(menu_path))
                        if menu is None:
                            menu = QtGui.QMenu(name, parent_menu) 
                            parent_menu.addMenu(menu)
                            menus['.'.join(menu_path)] = menu
                        parent_menu = menu
                label = param.replace('_', ' ')
            else:
                menu = self._attr_menu
                label = attr.replace('_', ' ')
            menu.addAction(label, lambda attr=attr: self.add_where(attr))
        
        for where in list(self._wheres): # copy the list so it can be altered by where.drop()!
            if not where.get_attr() in attrs:
                where.drop()
            
        for sp in list(self._sub_path_ws): # copy the list so it can be altered by where.drop()!
            if sp.get_label() not in sp_menus:
                sp.drop()
                
        self.hide_wait()
        
    def _fill_type_names_selector(self, type_names):
        self.type_name_select.set_items_with_icon(
            [ (i[0], i[1], i[0]) for i in type_names ],
            'flow.icons.nodes'
        )
    
    def add_where(self, attr):
        lo = self.where_lo
        where = WhereField(self, attr, self._on_remove_where)
        self._wheres.append(where)
        lo.addWidget(where)
        return where
    
    def _on_remove_where(self, where):
        self._wheres.remove(where)
        
    def add_sub_path(self, path):
        lo = self.sub_path_lo
        sp = SubPath(self, path, self._on_remove_sub_path)
        self._sub_path_ws.append(sp)
        lo.addWidget(sp)

    def _on_remove_sub_path(self, sp):
        self._sub_path_ws.remove(sp)
                
    def get_type_name(self):
        return self._type_name
    
    def set_type_name(self, type_name):
        if type_name is not None:
            self.type_name_select.select_value(type_name)
        
    def get_under_id(self):
        idStr = str(self.under_id_le.text()).strip()
        if not idStr:
            return None
        return idStr.split('/')
    
    def get_where(self):
        all = {}
        for where in self._wheres:
            all.update(where.get_clause())
            
        return all
            
    def get_sub_paths(self):
        return [ sp.get() for sp in self._sub_path_ws ]
    
    def get_results(self, to_func, on_error):
        self.show_wait()
        print 'Searching:'
        print '  type_name', self.get_type_name()
        print '  under', self.get_under_id()
        print '  where', self.get_where()
        print '  sub_paths', self.get_sub_paths()
        with self.client.result_to(to_func, on_error):
            self.client.apps.FLOW.cmds.FindCases(
                type_name=self.get_type_name(),
                under=self.get_under_id(),
                where=self.get_where(),
                sub_paths=self.get_sub_paths()
            )

    def to_preset(self):
        '''
        Returns a dict that can be later used with set_preset()
        to set all the fields the the current value.
        '''
        preset = {
            'type_name': self.get_type_name(),
            'under': self.get_under_id(),
            'where': [ w.to_preset() for w in self._wheres ],
            'sub_paths': self.get_sub_paths()
        }
        return preset
    
    def load_preset(self, preset):
        '''
        Configure the query builder to match the state it was
        in when this preset was created by the to_preset()
        method.
        '''
        self.under_id_le.setText('/'.join(preset.get('under', []) or []))
        self.set_type_name(preset.get('type_name', None))
        
        for where in list(self._wheres): # copy the list so it can be altered by where.drop()!
            where.drop()
        for where_preset in preset.get('where', []):
            where = self.add_where('???')
            where.apply_preset(where_preset)
        
        for sp in list(self._sub_path_ws): # copy the list so it can be altered by where.drop()!
            sp.drop()
        for p in preset.get('sub_paths', []):
            self.add_sub_path('.'.join(p))
            
    def _under_id_le_dragEnterEvent(self, e):
        if e.mimeData().hasFormat('kabaret/ids'):
            e.accept()
        else:
            e.ignore() 

    def _under_id_le_dragMoveEvent(self, e):
        if e.dropAction() == QtCore.Qt.LinkAction:
            e.accept()
            
    def _under_id_le_dropEvent(self, e):
        md = e.mimeData()
        if md.hasFormat('kabaret/ids'):
            value = str(md.data('kabaret/ids')).split('\n')
            self.under_id_le.setText(value[0])
            self._on_under_changed()


class ResultList(QtGui.QListWidget):
    def __init__(self, parent):
        super(ResultList, self).__init__(parent)

        self.setSelectionMode(self.ExtendedSelection)
        self.setDragEnabled(True)
        self.setDragDropMode(self.DragOnly)

    def mimeData(self, items):
        # I store the created mime data because of a pyside bug:
            #commit 59c882566be0d58c256f715ce675f10f3181ccc3
            #Author: Hugo Parente Lima <hugo.pl@gmail.com>
            #Date:   Fri Feb 4 17:42:38 2011 -0200
            #
            #    Fix bug 660 - "QMimeData type deleted prematurely when overriding mime-type in QStandardItemModel drag and drop"

        # Also, giving a string in second param of setData() result
        # in a QtCore.QByteArray('') !?!
        # After lots of empiric tries, constructing a QtCore.QByteArray seem to work.
        
        if not items:
            return None
        self._md = QtCore.QMimeData()
        self._md.setData(
            'kabaret/ids', 
            QtCore.QByteArray(
                '\n'.join( i.text() for i in items )
            )
        )
        return self._md

    def mimeTypes(self):
        return ['kabaret/ids']

class ToggleBox(QtGui.QGroupBox):
    _SS = 'QGroupBox{}'
    def __init__(self, parent, title, open=True):
        super(ToggleBox, self).__init__(parent)
        self.setStyleSheet(self._SS)
        
        self.setTitle(title)
            
        lo = QtGui.QVBoxLayout()
        self.setLayout(lo)
        
        self.setCheckable(True)
        self.toggled.connect(self._on_toggled)
        self.setChecked(open)

    def _set_closed(self, b):
        lo = self.layout()
        for i in range(lo.count()):
            lo.itemAt(i).widget().setHidden(b)
        self.setFlat(b)
        self.setStyleSheet(self._SS) # force update of property dependent style
    
    def _on_toggled(self, b):
        self._set_closed(not b)
        
    def addWidget(self, widget):
        self.layout().addWidget(widget)
        widget.setHidden(not self.isChecked())

class SearchView(AbstractGuiView):
    def __init__(self, parent, client, app_name):
        super(SearchView, self).__init__(parent, client, app_name)

        self.setLayout(QtGui.QVBoxLayout())

        menubar = QtGui.QMenuBar(self)
        self.layout().addWidget(menubar)
        
        self.presets = {}
        self.preset_menu = menubar.addMenu('Presets')
        
        toggleBox = ToggleBox(self, 'Parameters', open=False)
        self.layout().addWidget(toggleBox)
        
        self.qb = NodeQueryBuilder(self, self.client)
        toggleBox.addWidget(self.qb)

        waitter = QtGui.QLabel('Loading')
        wait_movie = QtGui.QMovie(resources.get('gui.icons', 'throbber.gif'))
        waitter.setMovie(wait_movie)
        wait_movie.start()
        waitter.hide()
        self.layout().addWidget(waitter, alignment=QtCore.Qt.AlignHCenter)
        self.qb.set_waitter(waitter)
        
        self.search_button = QtGui.QPushButton('Search', self)
        self.search_button.clicked.connect(self.on_search)
        self.layout().addWidget(self.search_button)
        
        self.list = ResultList(self)
        self.list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.layout().addWidget(self.list)
        
        # EVENTS
        self.client.add_event_handler(
            self._on_nav_current_changed, 'GUI', ['FLOW', 'Nav', 'current']
        )

        self.set_error(None)
        
        # default is not connected:
        self.on_disconnect()
        
    def on_connect(self):
        self.load_preset_menu()
        self.qb.hide_wait()
        self.qb.load_type_names()
        self.list.clear()
        self.search_button.setEnabled(True)
    
    def on_disconnect(self):
        self.qb.show_wait()
        self.clear_preset_menu()
        self.list.clear()
        self.search_button.setEnabled(False)

    def refresh_preset_menu(self):
        self.clear_preset_menu()
        self.load_preset_menu()
        
    def clear_preset_menu(self):
        self.preset_menu.clear()
        
    def load_preset_menu(self):
        self.preset_menu.addAction('Save Preset...', self._on_save_preset_dialog)
        self.preset_menu.addAction('Delete a Preset...', self._on_delete_preset_dialog)
        self.preset_menu.addSeparator()
        self.preset_menu.addAction('Reset', lambda: self.qb.load_preset({}))
        self.preset_menu.addSeparator()            
        with self.client.result_to(self._receive_presets):
            self.client.apps.USERS.cmds.GetUserData(
                login=get_user_name(),
                data_id='search_presets'
            )

    def _receive_presets(self, search_presets):
        self.presets = dict(search_presets)
        for name in sorted(self.presets.keys()):
            self.preset_menu.addAction(
                name, lambda name=name: self._on_load_preset(name) or self.on_search()
            )
    
    def _on_load_preset(self, preset_name):
        preset = self.presets[preset_name]
        self.qb.load_preset(preset)
        
    def save_to_preset(self, preset_name):
        preset_data = self.qb.to_preset()
        with self.client.result_to(self._preset_saved):
            self.client.apps.USERS.cmds.SetUserData(
                login=get_user_name(),
                data_id='search_presets',
                key=preset_name,
                value=preset_data
            )
    
    def _preset_saved(self, _):
        self.refresh_preset_menu()

    def delete_preset(self, preset_name):
        with self.client.result_to(self._preset_deleted):
            self.client.apps.USERS.cmds.SetUserData(
                login=get_user_name(),
                data_id='search_presets',
                key=preset_name,
                value=None
            )

    def _preset_deleted(self, _):
        self.refresh_preset_menu()

    def on_search(self):
        self._show_button_on_result = self.search_button.isVisible()
        self.search_button.hide()
        self.list.clear()
        self.qb.get_results(self.on_search_result, self.on_search_error)
    
    def on_search_result(self, results):
        self.set_error(None)
        self.qb.hide_wait()
        if self._show_button_on_result:
            self.search_button.show()
        self.list.addItems(
            [ '/'.join(i) for i in sorted(results) ]
        )
#        flags = (
#            QtCore.Qt.ItemIsEnabled
#            | QtCore.Qt.ItemIsDragEnabled
#            | QtCore.Qt.ItemIsSelectable
#        )
#        for i in range(self.list.count()):
#            self.list.item(i).setFlags(flags)
        
    def on_search_error(self, futur, err):
        self.qb.hide_wait()
        if self._show_button_on_result:
            self.search_button.show()
        self.set_error(err)
        raise err
    
    def set_error(self, error):
        if error:
            self.search_button.setStyleSheet('QWidget {border-color: red;}')
            self.search_button.setToolTip(str(error))
        else:
            self.search_button.setStyleSheet('')
            self.search_button.setToolTip('Click to search for nodes')
            
    def goto(self, node_id):
        self.client.send_event(
            Event('GUI', ['FLOW', 'Nav', 'current'], Event.TYPE.UPDATED, node_id)
        )

    def _on_item_double_clicked(self, item):
        self.goto(tuple(str(item.text()).split('/')))
        
    def _on_nav_current_changed(self, event):
        node_id = event.data

        self.list.selectionModel().clearSelection()
        if not self._is_active:
            return

        for i in range(self.list.count()):
            item_id = tuple(str(self.list.item(i).text()).split('/'))
            if item_id == node_id:
                self.list.item(i).setSelected(True)
                return

    def _on_save_preset_dialog(self):
        preset_name, ok = QtGui.QInputDialog.getItem(
            self, 'New Preset', 'Preset Name:',
            sorted(self.presets.keys())
        )
        if not ok:
            return
        
        if preset_name in self.presets:
            if not QtGui.QMessageBox.question(
                    self, 'Overwrite Preset', 'Overwrite preset %r?'%(preset_name,),
                ) == QtGui.QMessageBox.Ok:
                return
        
        self.save_to_preset(preset_name)

    def _on_delete_preset_dialog(self):
        preset_name, ok = QtGui.QInputDialog.getItem(
            self, 'Delete Preset', 'Preset Name:',
            sorted(self.presets.keys()),
            editable=False
        )
        if not ok:
            return
        
        self.delete_preset(preset_name)
        
        