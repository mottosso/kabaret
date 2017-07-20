'''



'''

import datetime

from kabaret.core.events.event import Event
from kabaret.core.utils import get_user_name

from kabaret.gui.styles import get_style_value
from kabaret.gui.widgets.async_selector import Selector
from kabaret.gui.widgets.views import AbstractGuiView, QtGui, QtCore, resources

from .utils import make_relative_id

class VersionsModel(QtCore.QAbstractTableModel):
    
    class Entry(object):
        def __init__(self, data):
            super(VersionsModel.Entry, self).__init__()
            self.data = data
            
            self.is_mine = self.data.get('owner') == get_user_name()
            
            rev_time = self.data.get('time')
            self.date_label = rev_time.ctime()
            if rev_time.date() == datetime.date.today():
                self.date_label = rev_time.strftime('%H:%M')
                
            if self.data['rev_type'] == 'w' and 'WORK' in self.data.get('versions'):
                color_name = self.is_mine and 'my_pending' or 'pending'
            else:
                color_name = self.data['rev_type']
            self.bg_color = get_style_value(
                'revision_colors', color_name,
                '#FF0000'
            )
            
        def label(self, column_index):
            if column_index == 0:
                return self.data.get('name')
            
            if column_index == 1:
                return self.date_label
            
            if column_index == 2:
                if self.is_mine:
                    return self.data.get('owner')+' (You)'
                return self.data.get('owner')
            
            if column_index == 3:
                return ', '.join([ str(i) for i in self.data.get('versions') ])
            
            if column_index == 4:
                return self.data.get('message')
            
            return None
        
        def tooltip(self, column_index):
            if column_index == 1:
                return self.data.get('time').ctime()
            if column_index == 4:
                return self.data.get('message')
            return self.label(column_index)
        
    def __init__(self):
        super(VersionsModel, self).__init__()
        self._data = []
        self.column_names = ['Time', 'Owner', 'Versions', 'Message']
        
    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self._data)
    
    def columnCount(self, index=QtCore.QModelIndex()):
        return len(self.column_names)
    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        column = index.column()
        
        if role == QtCore.Qt.DisplayRole:
            return self._data[row].label(column+1)
        
        elif role == QtCore.Qt.BackgroundRole:
            color = self._data[row].bg_color
            return color and QtGui.QColor(color) or None
        
        elif role == QtCore.Qt.ToolTipRole:
            return self._data[row].tooltip(column+1)
        
        return None
    
    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return self.column_names[section]

        if 0: # vertical header is hidden anyway...
            try:
                return str(self._data[section][0])
            except:
                return '???'
        else:
            return None
        
    def _clear(self):
        self.beginResetModel()
        self._data = []
        self.endResetModel()
    
    def _reset(self, data):
        self.beginResetModel()
            
        self._data = []
        for entry_data in data:
            entry = self.Entry(entry_data)
            self._data.append(entry)
        
        self.endResetModel()

    
class VersionsTable(QtGui.QTableView):
    try:
        status_changed = QtCore.pyqtSignal(str)
        load_finished = QtCore.pyqtSignal()
    except AttributeError:
        # PySide style
        status_changed = QtCore.Signal(str)
        load_finished = QtCore.Signal()
        
        
    def __init__(self, client, parent):
        super(VersionsTable, self).__init__(parent)
        
        self.filename = None
        self.client = client
        self._text_status = 'Initializing'
        
        self._show_versions_only = True

        self._model = VersionsModel()
        
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        #self.setVerticalScrollMode(self.ScrollPerPixel)
        #self.setSortingEnabled(False)
        self.verticalHeader().setVisible(False)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)

        self.setModel(self._model)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_table_menu)

    def _on_table_menu(self, pos):
        menu = QtGui.QMenu(self)
        menu.addAction('Refresh', self.refresh)        
        menu.exec_(self.mapToGlobal(pos))
        
    def on_disconnect(self):
        self._model._clear()
        self.resizeColumnsToContents()

    def on_connect(self):
        self.refresh()
    
    def set_filename(self, filename):
        if filename == self.filename:
            self.load_finished.emit()
            return
        self.filename = filename
        self.refresh()
        
    def show_versions_only(self, b):
        if b == self._show_versions_only:
            return
        self._show_versions_only = b
        self.refresh()

    def refresh(self):
        if not self.client.connected():
            self.set_status('Not Connected.')
            self.load_finished.emit()
            return
        
        if self.filename is None:
            self._model._clear()
            self.resizeColumnsToContents()
            self.set_status('No filename.')
            self.load_finished.emit()
            return
        
        with self.client.result_to(self._history_data_ready):
            self.set_status('Loading...')
            self.client.apps.VERSIONS.cmds.GetHistory(
                self.filename,
                get_user_name(),
                self._show_versions_only
            )
                
    def _history_data_ready(self, data):
        if data is None:
            self._model._clear()
            self.resizeColumnsToContents()
            self.set_status('Not under version control.')
            return
        self.set_status('')
        self._model._reset(data)
        self.resizeColumnsToContents()
        self.load_finished.emit()
        
    def set_status(self, message):
        self._text_status = message
        self.status_changed.emit(self._text_status)
        
    def text_status(self):
        return self._text_status
        
class VersionsView(AbstractGuiView):
    def __init__(self, parent, client, app_name):
        super(VersionsView, self).__init__(parent, client, app_name)
        self._tags = ['filename']
        self._current_node_id = None
        self._last_param_name = None
        
        self.setLayout(QtGui.QVBoxLayout())

        top_lo = QtGui.QHBoxLayout()
        self.layout().addLayout(top_lo)

        self.param_selector = Selector('Select a file...', self)
        self.param_selector.setEditable(False)
        self.param_selector.selected.connect(self._on_select_param)
        top_lo.addWidget(self.param_selector)

        butt = QtGui.QPushButton('Show Versions Only', self)
        butt.setCheckable(True)
        butt.setChecked(True)
        top_lo.addWidget(butt)
        
        self.status_label = QtGui.QLabel(self)
        self.layout().addWidget(self.status_label)
        
        self.table = VersionsTable(self.client, self)
        self.table.load_finished.connect(self._on_table_loaded)
        self.layout().addWidget(self.table)
        
        self.table.status_changed.connect(self.status_label.setText)
        butt.toggled.connect(self.table.show_versions_only)
        
        self.client.add_event_handler(
            self._on_nav_current_changed, 'GUI', ['FLOW', 'Nav', 'current']
        )

        self.layout().addStretch(10)

    def on_view_toggled(self, visible):
        super(VersionsView, self).on_view_toggled(visible)
        if visible:
            if self._current_node_id:
                self.load_node_id(self._current_node_id)
            else:
                self.clear()
                
    def on_connect(self):
        if self._current_node_id:
            self.load_node_id(self._current_node_id)
        
    def on_disconnect(self):
        self.clear()
        
    def _on_nav_current_changed(self, event):
        self._current_node_id = event.data
        if self._is_active:
            self.load_node_id(event.data)

    def clear(self):
        self.param_selector.clear()
    
    def load_node_id(self, node_id):
        self._current_node_id = node_id
        self.clear()
        self.table.setEnabled(False)
        self.param_selector.show_wait()
        with self.client.result_to(self._set_param_selector_items):
            self.client.apps.FLOW.cmds.CollectParams(self._current_node_id, self._tags)

    def _set_param_selector_items(self, param_ids):
        self.param_selector.set_items(
            [ 
                (
                    '/'.join(make_relative_id(self._current_node_id, param_id)),
                    param_id
                )
                for param_id in param_ids
            ]
        )
        
        if not param_ids:
            self.table.set_filename(None)
            return
            
        auto_select = None
        for param_id in param_ids:
            if param_id[-1] == self._last_param_name:
                auto_select = param_id
                break
        if auto_select is None:
            if param_ids:
                auto_select = param_ids[0]
            
        if auto_select is not None:
            self.param_selector.select_value(auto_select)

            
    def _on_select_param(self, label, param_id):
        self._last_param_name = param_id[-1]
        with self.client.result_to(self._filename_ready):
            self.client.apps.FLOW.cmds.GetParamValue(param_id)
    
    def _filename_ready(self, filename):
        self.table.set_filename(filename)
        self.status_label.setText(self.table.text_status())
    
    def _on_table_loaded(self):
        self.table.setEnabled(True)
        