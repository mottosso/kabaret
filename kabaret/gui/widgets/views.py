'''


'''

import sys

from . import QtCore, QtGui
from . import log_panel

from kabaret.core.events.event import Event
from kabaret.core.utils import resources
from kabaret.core.ro.client import ClientView

class AbstractGuiView(QtGui.QWidget, ClientView):
    def __init__(self, parent, client, app_name):
        ClientView.__init__(self, client, app_name)
        QtGui.QWidget.__init__(self, parent)

class AbstractGuiScrollView(QtGui.QScrollArea, ClientView):
    def __init__(self, parent, client, app_name):
        ClientView.__init__(self, client, app_name)
        QtGui.QScrollArea.__init__(self, parent)
        self.setWidgetResizable(True)
        self.setWidget(QtGui.QWidget(self))
        self.setFrameStyle(self.NoFrame)
        
class AbstractGuiGraphicsView(QtGui.QGraphicsView, ClientView):
    def __init__(self, parent, client, app_name):
        ClientView.__init__(self, client, app_name)
        QtGui.QGraphicsView.__init__(self, parent)
        self.setFrameStyle(self.NoFrame)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

class AbstractGuiToolBarView(QtGui.QToolBar, ClientView):
    def __init__(self, parent, client, app_name):
        ClientView.__init__(self, client, app_name)
        QtGui.QToolBar.__init__(self, parent)

class AppView(AbstractGuiView):
    class CommandInfos(object):
        def __init__(self, name=None, topics=[], blocks_topics=[], label=None, menus=[], icon=None):
            self.name = name
            self.topics = topics
            self.blocks_topics = blocks_topics
            self.label = label
            self.menus = menus
            self.icon = icon

    def __init__(self, parent, client, app_name):
        super(AppView, self).__init__(parent, client, app_name)

        self.setLayout(QtGui.QVBoxLayout())
        
        self._build_waiter()
        
    def on_disconnect(self):
        self._build_waiter()
        
    def on_connect(self):
        self._build_waiter()
        self.fetch_commands()
    
    def fetch_commands(self):
        with self.client.result_to(self._receive_commands):
            self.client.get_commands(self.app_name)
    
    def _receive_commands(self, commands):
        self.commands = [ self.CommandInfos(**infos) for infos in commands[self.app_name] ]
        self._build_ui()
        
    def _build_ui(self):
        self._clear_ui()
        for c in self.commands:
            b = QtGui.QPushButton(c.label, self)
            b.connect(b, QtCore.SIGNAL('clicked()'), lambda c=c:self.on_command(c))
            if c.icon is not None:
                b.setIcon(c.icon)
            self.layout().addWidget(b)
        self.layout().addStretch()
        self.waitter.hide()
    
    def _clear_ui(self):
        lo = self.layout()
        item = lo.takeAt(0)
        while item:
            w = item.widget()
            w and w.deleteLater()
            item = lo.takeAt(0)
    
    def _build_waiter(self):
        self._clear_ui()
        self.waitter = QtGui.QLabel('Loading')
        wait_movie = QtGui.QMovie(resources.get('gui.icons', 'throbber.gif'))
        self.waitter.setMovie(wait_movie)
        self.layout().addWidget(self.waitter)
        wait_movie.start()
        self.layout().addStretch()
        
    def on_command(self, command):
        with self.client.result_to(self.on_result):
            print '----------------', command.name
            self.client.apps[self.app_name].cmds.get_command(command.name)()

    def on_result(self, result):
        self.client.send_event(
            Event('GUI', [self.__class__.__name__]+['result'], Event.TYPE.MESSAGE, result)
        )

    def on_timeout(self):
        print '--------- COMMAND TIMED OUT!!!!'


class _StdListener(object):
    def __init__(self, cb):
        self._cb = cb
        self._orig = None
        self.fallback = True
        
    def apply(self):
        raise NotImplementedError
    
    def remove(self):
        raise NotImplementedError
    
    def write(self, text):
        self._cb(text)
        if self.fallback and self._orig:
            self._orig.write(text)
        
class StdOutListener(_StdListener):
    def apply(self):
        if self._orig:
            return
        self._orig = sys.stdout
        sys.stdout = self

    def remove(self):
        if self._orig:
            sys.stdout = self._orig
            self._orig = None
        
class StdErrListener(_StdListener):
    def apply(self):
        if self._orig:
            return
        self._orig = sys.stderr
        sys.stderr = self
         
    def remove(self):
        if self._orig:
            sys.stderr = self._orig
            self._orig = None

class ConsoleView(AbstractGuiView):
    '''
    This view displays the stdout and stderr streams
    when the client is connected.
    
    '''
    def __init__(self, parent, client, app_name):
        super(ConsoleView, self).__init__(parent, client, app_name)
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        
        self.log_panel = log_panel.LogPanel(self)
        self.layout().addWidget(self.log_panel)
        
        # Say Hello
        self.log_panel.raw_append('Console Started.\n\n')

        self.my_stdout = StdOutListener(self._on_stdout)
        self.my_stdout.apply()
        
        self.my_stderr = StdErrListener(self._on_stderr)
        self.my_stderr.apply()
        
    def _on_stdout(self, text):
        self.log_panel.raw_append(text)

    def _on_stderr(self, text):
        self.log_panel.raw_append(text, '#DD0000')
    
    def start_redirection(self):
        self.my_stdout.apply()
        self.my_stderr.apply()
    
    def stop_redirection(self):
        self.my_stdout.remove()
        self.my_stderr.remove()

    def on_connect(self):
        self.start_redirection()

    def on_disconnect(self):
        # we need to stop redirecting when the client
        # is disconnected because the de-connection might come
        # from the GUI being destroyed in which case the 
        # log_panel cannot display anymore and Qt crashes if we try.
        self.stop_redirection()

class ListenerViewLogFilter(log_panel.Filter):
    def __init__(self, name, app_key, filter_path, active=True, group=None):
        super(ListenerViewLogFilter, self).__init__(name, active, group)
        self.app_key = app_key
        self.filter_path = filter_path
        self.filter_path_str = '^'.join([str(e) for e in filter_path])
            
    def allow(self, event_app_key, event_path_str):
        if not self.active:
            return True
        if not self.app_key or self.app_key == event_app_key:
            if event_path_str.startswith(self.filter_path_str):
                return False
        return True

class ListenerView(AbstractGuiView): 
    def __init__(self, parent, client, app_name):
        super(ListenerView, self).__init__(parent, client, app_name)
        
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        
        self.log_panel = log_panel.LogPanel(self)
        self._activate_toggle_action = self.log_panel.add_action('Activated', self._on_active_toggle)
        self._activate_toggle_action.setCheckable(True)
        self._activate_toggle_action.setChecked(False)
        self.layout().addWidget(self.log_panel)
        
        # Say Hello
        self.log_panel.append('Listener is not Activated, use the Log menu to toggle.')

    def _on_active_toggle(self, b=None):
        if b is None:
            # PySide does not send the 'checked' on triggered signal :/
            b = self._activate_toggle_action.isChecked()
            
        if b:
            self.client.add_event_handler(self.on_event, None, [], None) # match all events
            self.log_panel.append('Listener was activated.')
        else:
            self.client.remove_event_handler(self.on_event)
            self.log_panel.append('Listener was deactivated.')
            
    def _update_filters(self):
        # clear all filters
        self.log_panel.clear_filters()
        
        # Default Filters
        self.log_panel.add_filter(
            ListenerViewLogFilter(
                name='Show Command History events',
                active=False,
                app_key='HOST',
                filter_path=['CommandHistory']
            ),
            update_menu=False
        )
        self.log_panel.add_filter(
            ListenerViewLogFilter(
                name='Show GUI events',
                active=True, 
                app_key='GUI',
                filter_path=[]
            ),
            update_menu=False
        )
        self.log_panel.add_filter(
            ListenerViewLogFilter(
                name='Echo Commands',
                active=True, 
                app_key='HOST',
                filter_path=['CommandEcho']
            ),
            update_menu=False
        )
        
        # Apps Filters
        label_template = 'Show %s events'
        for name in sorted(self.client.apps.keys()):
            log_filter = ListenerViewLogFilter(
                name=label_template%(name,),
                active=True, 
                app_key=name,
                filter_path=[],
                group='Local Apps'
            )
            self.log_panel.add_filter(log_filter, update_menu=False)
            
        for name in sorted(self.client.project_apps.keys()):
            log_filter = ListenerViewLogFilter(
                name=label_template%(name,),
                active=True,
                app_key=name,
                filter_path=[],
                group='Project Apps'
            )
            self.log_panel.add_filter(log_filter, update_menu=False)
        
        # Update the Filter menu
        self.log_panel.update_filter_menu()
        
    def on_disconnect(self):
        self.log_panel.clear_filters()
        self.log_panel.update_filter_menu()
        
    def on_connect(self):
        self._update_filters()

    def on_event(self, event):
        event_path_str = '^'.join([str(e) for e in event.path])
        if self.log_panel.filter(event.app_key, event_path_str):
            return
        txt = '%s %s %r: %r'%(event.app_key, event.etype, event.path, event.data)        
        self.log_panel.append(txt)

class ConnectionView(AbstractGuiView):
    def __init__(self, parent, client, app_name):
        super(ConnectionView, self).__init__(parent, client, app_name)

        self.setLayout(QtGui.QVBoxLayout())
        
        for tool in (
            'ping_apphost', 'ping_project', 
            None,
            'kill_apphost', 'disconnect', 'reconnect', 
            ):
            if not tool:
                self._add_space()
            else:
                self._add_button(tool)
        self.layout().addStretch()

    def _add_space(self):
        self.layout().addSpacing(16)
        
    def _add_button(self, tool_name):
        b = QtGui.QPushButton(tool_name, self)
        b.connect(b, QtCore.SIGNAL('clicked()'), getattr(self, tool_name))
        self.layout().addWidget(b)

    def send_message(self, msg, path=[]):
        self.client.send_event(
            Event('GUI', [self.__class__.__name__]+path, Event.TYPE.MESSAGE, msg)
        )
        
    def ping_apphost(self):
        pong = self.client.apphost.ping()
        self.send_message(pong, ['ping_apphost'])
        
    def ping_project(self):
        pong = self.client.apphost.ping_project()
        self.send_message(pong, ['ping_project'])
        
    def kill_apphost(self):
        self.client.kill_apphost()
        self.send_message('Done', ['kill_apphost'])

    def disconnect(self):
        pong = self.client.disconnect()
        self.send_message('Done', ['disconnect', pong])

    def reconnect(self):
        pong = self.client.connect()
        self.send_message('Done', ['reconnect', pong])

    def on_result(self, result):
        self.send_message('  RESULT: %r'%(result,))
        

class CommandHistoryModel(QtCore.QAbstractTableModel):
    COLUMN_NAMES = ['App', 'Label', 'Command', 'Status']
    
    class Entry(object):
        def __init__(self, entry_data):
            super(CommandHistoryModel.Entry, self).__init__()
            self._entry_data = entry_data
        
        def update(self, entry_data):
            self._entry_data = entry_data
            
        def __getitem__(self, column_name):
            '''Returns text for this column'''
            keys = {
                'App': ['app'],
                'Label': ['ui_infos', 'label'],
                'Command': ['script'],
                'Status': ['status_str']
            }[column_name]
            d = self._entry_data
            for k in keys:
                d = d[k]
            return d
        
        def foreground(self):
            try:
                color = {
                    0: '#008888', # INIT
                    1: '#0000FF', # RUNNING
                    2: '#FF0000', # ERROR
                    3: '#aaaacc', # CANCEL
                    4: None,      # DONE
                }[self._entry_data['status']]
            except KeyError:
                color = '#FF0000'
            if color is None:
                return None
            return QtGui.QBrush(QtGui.QColor(color))
            return None
        
        def decoration(self, column_name):
            '''Returns color, icon or pixmap for this column'''
            if column_name == 'Status':
                status = self._entry_data['status']
                if status == 1:
                    return QtGui.QColor('#008800')
                if status < 1:
                    return QtGui.QColor('#000088')
                return QtGui.QColor('#880000')
            return None
        
        def tool_tip(self):
            return self._entry_data['usage']
        
    def __init__(self):
        super(CommandHistoryModel, self).__init__()
        self._data = []

    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self._data)
    
    def columnCount(self, index=QtCore.QModelIndex()):
        return len(self.COLUMN_NAMES)
    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        
        try:
            row = index.row()
            column = index.column()
            
            if role == QtCore.Qt.DisplayRole:
                return self._data[row][1][self.COLUMN_NAMES[column]]
            
            elif role == QtCore.Qt.ForegroundRole:
                return self._data[row][1].foreground()
            
            elif role == QtCore.Qt.DecorationRole:
                return self._data[row][1].decoration([self.COLUMN_NAMES[column]])
        except:
            return None
        return None
    
    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return self.COLUMN_NAMES[section]

        try:
            return str(self._data[section][0])
        except:
            return '???'
        
    def _append(self, entry_id, entry_data):
        entry = self.Entry(entry_data)
        position = len(self._data)
        self.beginInsertRows(QtCore.QModelIndex(), position, position + 1 - 1)
        self._data.append((entry_id, entry))
        self.endInsertRows()
    
    def _update(self, entry_id, entry_data):
        if not self._data:
            #print "W A R N I N G: CommandHistoryModel._update on EMPTY data!"
            return 
        
        for position, row in enumerate(self._data):
            if row[0] == entry_id:
                row[1].update(entry_data)
                break
                
        top_left_index = self.index(position, 0)
        bottom_righ_index = self.index(position, self.columnCount()-1)
        self.dataChanged.emit(top_left_index, bottom_righ_index)
        
    def _remove(self, entry_id):        
        for position, row in enumerate(self._data):
            if row[0] == entry_id:
                break
            
        self.beginRemoveRows(QtCore.QModelIndex(), position, position + 1 - 1)
        self._data.pop(position)
        self.endRemoveRows()
    
    def _get_ids(self):
        return [ entry[0] for entry in self._data ]
    
    def _clear(self):
        self.beginResetModel()
        self._data = []
        self.endResetModel()
    
    def _reset(self, entry_ids_and_data):
        self.beginResetModel()
        self._data = []
        for entry_id, entry_data in entry_ids_and_data:
            entry = self.Entry(entry_data)
            self._data.append((entry_id, entry))
        self.endResetModel()
        
class CommandHistoryView(AbstractGuiView):
    #TODO: the view receives the events that drive the (qt) model. This sucks.
    # Multiple View should be able to watch the same model, events
    # should be received by something common to those views (the model?)
    def __init__(self, parent, client, app_name):
        super(CommandHistoryView, self).__init__(parent, client, app_name)

        self.model = CommandHistoryModel()
        
        self.setLayout(QtGui.QVBoxLayout())

        self.table = QtGui.QTableView(self)
        self.layout().addWidget(self.table)
        self.table.setHorizontalScrollMode(self.table.ScrollPerPixel)
        self.table.setVerticalScrollMode(self.table.ScrollPerPixel)
        self.table.setSortingEnabled(False)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.table.setSelectionBehavior(self.table.SelectRows)

        self.table.setModel(self.model)
        
        self.client.add_event_handler(
            self.on_history_event,
            'HOST', ['CommandHistory'] 
        )

#        self.client.add_event_handler(
#            self.on_update_request,
#            'GUI', ['HistoryView', 'UPDATE']
#        )
        
    def on_disconnect(self):
        self.model._clear()

    def on_connect(self):
        with self.client.result_to(self._all_data_ready):
            self.client.get_command_history()
    
    def _all_data_ready(self, data):
        self.model._reset(data)

    def on_history_event(self, event):
        '''
        Receives all events related to the apphost CommandHistory.
        Syncs the CommandHistoryModel shown in our table.

        '''
        
        if event.etype == event.TYPE.CREATED:
            # A new entry was created.
            # The event data are: (entry_id, entry)
            # Each entry looks like:
            #    {'status_str': 'Running', 'status': 1, 'doc': None, 'app': 'DATA', 'ui_infos': {'name': '(=.=)', 'blocks_topics': [], 'topics': [], 'label': 'PFormat', 'menus': [], 'icon': None}, 'usage': 'mystudio.kabaret.apps.PFormat(app, )'}
            # See kabaret.core.apps.command.CommandHistory.Entry.to_dict()
            # for details about the entry
            entry_id, entry_data = event.data
            self.model._append(entry_id, entry_data)
            
        elif event.etype == event.TYPE.DELETED:
            row_id = event.data
            self.model._remove(row_id)
            

        elif event.etype == event.TYPE.UPDATED:
            entry_id, entry_data = event.data
            self.model._update(entry_id, entry_data)


#    def on_update_request(self, event):
#        print '#__________ UPDATING HISTORY MODEL'
#        import random
#        st = random.choice(range(4))
#        ids = self.model._get_ids()
#        for entry_id in ids:
#            print '   ', entry_id
#            self.client.apphost.on_command_changed(entry_id, st)
            

class _ScriptTextEdit(QtGui.QTextEdit):
    try:
        execute_request = QtCore.pyqtSignal(str)
    except AttributeError:
        # PySide style
        execute_request = QtCore.Signal(str)
        
    def get_execute_code(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            code = str(cursor.selectedText().replace(u'\u2029', '\n').replace(u'\u2028', '\n'))
        else:
            code = str(self.toPlainText())
        return code
    
    def keyPressEvent(self, key_event):
        if key_event.modifiers() & QtCore.Qt.CTRL:
            if key_event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.execute_request.emit(self.get_execute_code())
                key_event.accept()
                return
        super(_ScriptTextEdit, self).keyPressEvent(key_event)

class ScriptView(AbstractGuiView):
    def __init__(self, parent, client, app_name):
        super(ScriptView, self).__init__(parent, client, app_name)
        self.exec_scope = {'client':self.client, 'view': self}

        self.setLayout(QtGui.QVBoxLayout())
        
        splitter = QtGui.QSplitter(QtCore.Qt.Vertical, self)
        self.layout().addWidget(splitter)
        
        self.output = QtGui.QTextEdit(splitter)
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(self.output.NoWrap)
        splitter.addWidget(self.output)

        self.input = _ScriptTextEdit(splitter)
        self.input.setReadOnly(False)
        self.input.setLineWrapMode(self.input.NoWrap)
        splitter.addWidget(self.input)

        self.output.append('Script View Ready')
        
        self.input.execute_request.connect(self.execute)

    def echo(self, *stuffs):
        self.output.append(' '.join([ str(i) for i in stuffs ]))
        
    def execute(self, code):
        code = str(code).strip()
        
        self.echo(code)
        
        try:
            result = eval(code, self.exec_scope)
        except SyntaxError:
            exec(code, self.exec_scope)
        except:
            import traceback 
            trace = traceback.format_exc()
            self.echo(trace)
        else:
            if result is not None:
                self.exec_scope['_'] = result
                self.echo('>', result)
        
class WorkersModel(QtCore.QAbstractTableModel):    
    class Entry(object):
        def __init__(self, type, status, station_class, features, document, user, host, paused):
            super(WorkersModel.Entry, self).__init__()
            self.type = type
            self.features = features
            self.document = document
            self.status = status
            self.station_class = station_class
            self.host = host
            self.user = user
            self.paused = paused
            
        def __getitem__(self, column_index):
            if column_index == 0:
                return self.type
            
            if column_index == 1:
                return self.paused and '%s (paused)'%(self.status,) or self.status
            
            if column_index == 2:
                return self.station_class

            if column_index == 3:
                return ', '.join(self.features)
            
            if column_index == 4:
                return self.document or ''
            
            if column_index == 5:
                return self.user
            
            if column_index == 6:
                return self.host
            
            return None
                
    def __init__(self):
        super(WorkersModel, self).__init__()
        self._data = []
        self.column_names = ['Type', 'Status', 'Station Class', 'Features', 'Document', 'User', 'Host']
        
    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self._data)
    
    def columnCount(self, index=QtCore.QModelIndex()):
        return len(self.column_names)
    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        
        try:
            row = index.row()
            column = index.column()
            if role == QtCore.Qt.DisplayRole:
                return self._data[row][1][column]
        except:
            return None
        return None
    
    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return self.column_names[section]

        try:
            return str(self._data[section][0])
        except:
            return '???'
        
    def _clear(self):
        self.beginResetModel()
        self._data = []
        self.endResetModel()
    
    def _reset(self, client_ids_and_data):
        self.beginResetModel()
            
        self._data = []
        for entry_id, entry_data in client_ids_and_data:
            entry = self.Entry(**entry_data)
            self._data.append((entry_id, entry))
        
        self.endResetModel()

    def get_worker_id(self, index):
        return self._data[index.row()][0]
    
    def get_features(self, index):
        return self._data[index.row()][1].features

    def get_document(self, index):
        return self._data[index.row()][1].document
    
    def get_status(self, index):
        return self._data[index.row()][1].status
    
class WorkersTable(QtGui.QTableView):
    try:
        refresh_done = QtCore.pyqtSignal()
    except AttributeError:
        # PySide style
        refresh_done = QtCore.Signal()
    
    def __init__(self, client, parent):
        super(WorkersTable, self).__init__(parent)
        
        self.client = client
    
        self._show_mine_only = True

        self._model = WorkersModel()
        
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        #self.setSortingEnabled(False)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)

        self.setModel(self._model)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_table_menu)
        self.start_listening()
        
    def start_listening(self):
        self.client.add_event_handler(
            self.on_worker_event,
            'HOST', ['Workers'] 
        )

    def stop_listening(self):
        self.client.remove_event_handler(self.on_worker_event)
        
    def _on_table_menu(self, pos):
        menu = QtGui.QMenu(self)
        menu.addAction('Refresh', self.refresh)        
        menu.addAction('Drop Disconnected Workers', self.drop_disconnected_workers)
        menu.exec_(self.mapToGlobal(pos))
        
    def on_disconnect(self):
        self._model._clear()

    def on_connect(self):
        self.refresh()
    
    def on_worker_event(self, event):
        '''
        Resets the model in order to update the displayed infos
        '''
        self.refresh()

    def show_mine_only(self, b):
        if b == self._show_mine_only:
            return
        self._show_mine_only = b
        self.refresh()

    def refresh(self):
        if not self.client.connected():
            return
        with self.client.result_to(self._all_data_ready):
            self.client.get_workers_infos(
                this_user_only=self._show_mine_only,
                this_host_only=self._show_mine_only,
            )
                
    def _all_data_ready(self, data):
        self._model._reset(data)
        self.refresh_done.emit()

    def drop_disconnected_workers(self):
        if not self.client.connected():
            return
        self.client.drop_apphost_disconnected_workers()
        # (a refresh will be triggered by update event)
    
    def get_current_id(self):
        index = self.currentIndex()
        if not index.isValid():
            return None
        return self.model().get_worker_id(index)
    
    def get_current_features(self):
        index = self.currentIndex()
        if not index.isValid():
            return []
        return self.model().get_features(index)

    def get_current_document(self):
        index = self.currentIndex()
        if not index.isValid():
            return None
        return self.model().get_document(index)
        
    def get_current_status(self):
        index = self.currentIndex()
        if not index.isValid():
            return None
        return self.model().get_status(index)
        
class WorkerToolBar(QtGui.QToolBar):
    def __init__(self, parent, worker_table):
        super(WorkerToolBar, self).__init__(parent)
        self.worker_table = worker_table
        self.client = worker_table.client
        
        mine_only_cb = QtGui.QCheckBox(
            'Show only my local workers',
            self
        )
        mine_only_cb.setChecked(self.worker_table._show_mine_only)
        mine_only_cb.stateChanged.connect(self._on_mine_only_cb_change)
        self.addWidget(mine_only_cb)
        
        self.addSeparator()
        
        self.addAction(
            'Refresh', self.on_refresh
        )
        self.addAction(
            'Drop Disconnected Workers',
            self.on_drop_disconnected_workers
        )

        self.addSeparator()

        self._worker_cmds = []
        run_tb = QtGui.QPushButton(self)
        run_tb.setText('New Worker')
        self._run_menu = QtGui.QMenu()
        self._run_menu.addAction('<not loaded>')
        run_tb.setMenu(self._run_menu)
        self.addWidget(run_tb)
        
    def on_disconnect(self):
        self.setEnabled(False)
        
    def on_connect(self):
        self.setEnabled(True)
        self.refresh_workers()
    
    def on_refresh(self):
        self.worker_table.refresh()

    def refresh_workers(self):
        with self.client.result_to(self._workers_cmds_ready):
            self.client.apps.CMDS.cmds.GetWorkerCmdInfos(self.client.station_class)
    
    def _workers_cmds_ready(self, data):
        self._worker_cmds = data
        self._worker_cmds.sort(
            cmp=lambda a, b: cmp(a['label'], b['label'])
        )
        
        self._run_menu.clear()
        for cmd_info in self._worker_cmds:
            action = self._run_menu.addAction(cmd_info['label'], lambda cmd_id=cmd_info['id']: self.run_worker(cmd_id))
            try:
                icon = resources.get_icon(('system_cmds.icons', cmd_info['icon']))
            except resources.NotFoundError:
                pass
            else:
                action.setIcon(icon)

    def _on_mine_only_cb_change(self, state):
        checked = False
        if state == QtCore.Qt.Checked:
            checked = True
        self.worker_table.show_mine_only(checked)
            
    def on_drop_disconnected_workers(self):
        self.worker_table.drop_disconnected_workers()
    
    def run_worker(self, cmd_id):
        with self.client.result_to(self._receive_cmd_infos_to_launch):
            self.client.apps['CMDS'].cmds.GetClientCmd(
                cmd_id=cmd_id, station_class=self.client.station_class
            )

    def _receive_cmd_infos_to_launch(self, cmd_infos):
        print 'Received WORKER CMD:', cmd_infos
        import kabaret.core.syscmd
        cmd = kabaret.core.syscmd.SysCmd(
            executable=cmd_infos['executable'], 
            args=[], 
            env=cmd_infos['env'], 
            additional_env=cmd_infos['additional_env']
        )
        cmd.execute()

class WorkersView(AbstractGuiView):
    def __init__(self, parent, client, app_name, show_mine_only=False):
        super(WorkersView, self).__init__(parent, client, app_name)
        
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        self.table = WorkersTable(self.client, self)
        self.table.show_mine_only(show_mine_only)
        self.tb = WorkerToolBar(self, self.table)
        
        self.layout().addWidget(self.tb)
        self.layout().addWidget(self.table)

        if self.client.connected():
            self.on_connect()

    def on_disconnect(self):
        self.tb.on_disconnect()
        self.table.on_disconnect()

    def on_connect(self):
        self.tb.on_connect()
        self.table.on_connect()

class WorkQueueView(AbstractGuiView):
    def __init__(self, parent, client, app_name):
        super(WorkQueueView, self).__init__(parent, client, app_name)
        
        self.setLayout(QtGui.QVBoxLayout())
        #self.layout().setContentsMargins(0,0,0,0)

        refresh_button = QtGui.QPushButton('Refresh', self)
        refresh_button.clicked.connect(self._on_refresh_button)
        self.layout().addWidget(refresh_button)
        
        self.pause_button = QtGui.QPushButton('Running', self)
        self.pause_button.setCheckable(True)
        self.pause_button.setChecked(False)
        self.pause_button.toggled.connect(self._on_pause_button_toggle)
        self.layout().addWidget(self.pause_button)
        
        self.l = QtGui.QTextEdit(self)
        self.layout().addWidget(self.l)
        
        self.client.add_event_handler(
            self._on_work_queue_update_event,
            'GUI', ['WorkQueue']
        )
        
        self.refresh()
    
    def _on_work_queue_update_event(self, event):
        self.refresh()
        
    def _on_refresh_button(self):
        self.refresh()
    
    def _on_pause_button_toggle(self, checked):
        self.client.set_embedded_worker_paused(checked)
        
        if checked:
            self.pause_button.setText('Paused')
        else:
            self.pause_button.setText('Running')
        self.refresh()
        
    def refresh(self):
        worker_infos = self.client.get_embedded_worker_infos()
        import pprint
        self.l.setPlainText(pprint.pformat(worker_infos))
        


