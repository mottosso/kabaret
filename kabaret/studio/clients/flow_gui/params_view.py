

import datetime
import time
import collections
import pprint

from kabaret.core.events.event import Event
from kabaret.core.utils import resources

from kabaret.gui.widgets import log_panel, sweep_panel
from kabaret.gui.widgets.views import AbstractGuiScrollView, AbstractGuiGraphicsView, QtGui, QtCore, resources

from kabaret.gui.widgets.value_editor import get_global_factory, ValueEditorMixin, ValueController

from .path_label import PathLabel
from .utils import make_relative_id


#
#class PieChart(QtGui.QWidget):
#    def __init__(self, parent):
#        super(PieChart, self).__init__(parent)
#        
#        self._entries_details = {}
#        self.data = {}
#        self.total = 0
#        self._text_colors = {'None':'#F00', True: '#080', False: '#800'}
#        
#        # cached for draw speed:
#        self._color_names = QtGui.QColor.colorNames()
#        self._nb_color_name = len(self._color_names)
#        
#        self.setSizePolicy(
#            QtGui.QSizePolicy.MinimumExpanding,
#            QtGui.QSizePolicy.MinimumExpanding,
#        )
#        
#    def set_data(self, data):
#        self._entries_details = {}
#        self.data = data
#
#        try:
#            self.total = sum(self.data.values())
#        except TypeError:
#            self.data = {}
#            self.total = 0
#            
#        h = (len(self.data)+1)*self.fontMetrics().height() * 1.5
#        self.setMinimumHeight(h)
#    
#    def set_entries_details(self, details):
#        self._entries_details = dict(details)
#        
#    def paintEvent(self, ev):
#        p = QtGui.QPainter(self)
#        p.setRenderHint(p.Antialiasing, True)
#
#        colorPos = 13
#        height = self.rect().height()
#        pieRect = QtCore.QRect(0, 0, height, height)
#        
#        legendRect = self.rect()
#        legendRect.setLeft(pieRect.width())
#        legendRect.adjust(10,10,-10,-10)
#        lastAngleOffset = 0
#        currentPos = 0
#        
#        # bring to local for speed
#        total = self.total
#        get_color_for = self.get_color_for
#        get_detailed_text = self.get_detailed_text
#        light = QtGui.QColor(255, 255, 255, 200)#QtCore.Qt.white
#        
#        for text in sorted(self.data.keys()):
#            value = self.data[text]
#            angle = int(16*360*(value/(total*1.0)))
#            col = QtGui.QColor(get_color_for(text, colorPos))
#            colorPos += 1
#            
#            rg = QtGui.QRadialGradient(
#                QtCore.QPointF(pieRect.center()), pieRect.width()/2.0,
#                QtCore.QPointF(pieRect.topLeft())
#            )
#            rg.setColorAt(0, light)
#            rg.setColorAt(1, col)
#            p.setBrush(rg)
#            pen = p.pen()
#            p.setPen(QtCore.Qt.NoPen)
#            
#            p.drawPie(pieRect, lastAngleOffset, angle)
#            lastAngleOffset += angle
#            
#            fh = self.fontMetrics().height()
#            legendEntryRect = QtCore.QRect(0,(fh*1.5)*currentPos,fh,fh)
#            currentPos += 1
#            legendEntryRect.translate(legendRect.topLeft())
#            
#            lg = QtGui.QLinearGradient(
#                QtCore.QPointF(legendEntryRect.topLeft()),
#                QtCore.QPointF(legendEntryRect.bottomRight())
#            )
#            lg.setColorAt(0, col)
#            lg.setColorAt(1, light)
#            p.setBrush(lg)
#            p.drawRect(legendEntryRect)
#            
#            textStart = legendEntryRect.topRight()
#            textStart = textStart + QtCore.QPoint(self.fontMetrics().width('x'), 0)
#            
#            textEnd = QtCore.QPoint(legendRect.right(), legendEntryRect.bottom())
#            textEntryRect = QtCore.QRect(textStart, textEnd)
#            p.setPen(pen)
#            p.drawText(textEntryRect, QtCore.Qt.AlignVCenter, get_detailed_text(text))
#    
#    def get_detailed_text(self, text):
#        if text in self._entries_details:
#            text += '  '+self._entries_details[text]
#        return text
#    
#    def get_legend_text(self):
#        return '\n'.join(
#            '%s: %s'%(k,v) for k,v in self.data.items()
#        )
#
#    def set_text_color(self, **text_to_color):
#        self._text_colors.update(text_to_color)
#        
#    def get_color_for(self, text, index=None):
#        '''
#        Returns the name of the color to use for 
#        the given text at the given index.
#        '''
#        color_name = self._text_colors.get(text)
#        if color_name is None:
#            print 'Pie color not found', text
#            return self._color_names[index%self._nb_color_name]
#        return color_name
#
#class ValueEditorMixin(object):
#    class STYLE_SHEETS:
#        #TODO: use colors from something like kabaret.gui.style.current_style(topic)
#        COMPUTED = 'QWidget { border-color: #555511 }'
#        LINKED = 'QWidget { border-color: #222255 }'
#        EDITABLE = ''
#        VOLATILE = 'QWidget{ border-color: #555555 }'
#        EDITING = 'QWidget { border-color: #225555 }'
#        BUSY = 'QWidget { border-color: #225522 }'
#        ERROR = 'QWidget { color: #FF2222 }'
#
#    def __init__(self, param_editor, options):
#        super(ValueEditorMixin, self).__init__()
#        self._param_editor = param_editor
#        self._options = options
#        
#        self._init_style_sheet = self.STYLE_SHEETS.EDITABLE
#        self._init_read_only = True
#        self._last_value_set = None
#        self._error_msg = None
#
#    def _ui_widgets(self):
#        '''
#        Subclass must implement this and return 
#        a list of widget to style.
#        Default is to return [self].
#        '''
#        return [self]
#
#    def set_label(self, label=None):
#        '''
#        Sets the label of the editor.
#        Most of the value editors will ignore
#        this.
#        '''
#        return
#
#    def get_value(self):
#        '''
#        Subclass must implement this method.
#        '''
#        raise NotImplementedError
#
#    def set_value(self, value):
#        '''
#        Subclass must call this implementation 
#        when overriding this method.
#        '''
#        self._last_value_set = value
#
#    def update_value(self, new_value):
#        self.set_value(new_value)
#        self.set_clean()
#        
#    def edit_started(self):
#        for w in self._ui_widgets():
#            w.setStyleSheet(self.STYLE_SHEETS.EDITING)
#    
#    def edit_finished(self):
#        if self.get_value() == self._last_value_set:
#            self.set_clean()
#            return
#        
#        self._param_editor.value_editor_set(self.get_value())
#        self.set_busy()
#    
#    def set_linked(self):
#        self._init_read_only = True
#        self._set_read_only(True)
#        for w in self._ui_widgets():
#            w.setStyleSheet(self.STYLE_SHEETS.LINKED)
#        self._init_style_sheet = self.STYLE_SHEETS.LINKED
#    
#    def set_computed(self):
#        self._init_read_only = True
#        self._set_read_only(True)
#        for w in self._ui_widgets():
#            w.setStyleSheet(self.STYLE_SHEETS.COMPUTED)
#        self._init_style_sheet = self.STYLE_SHEETS.COMPUTED
#
#    def set_editable(self):
#        self._init_read_only = False
#        for w in self._ui_widgets():
#            w.setStyleSheet(self.STYLE_SHEETS.EDITABLE)
#        self._init_style_sheet = self.STYLE_SHEETS.EDITABLE
#        self._set_edit_connections()
#    
#    def set_volatile(self):
#        self._init_read_only = False
#        for w in self._ui_widgets():
#            w.setStyleSheet(self.STYLE_SHEETS.VOLATILE)
#        self._init_style_sheet = self.STYLE_SHEETS.VOLATILE
#        self._set_edit_connections()
#        
#    def _set_edit_connections(self):
#        '''
#        Subclasses must implemtent this method.
#        '''        
#        raise NotImplementedError
#    
#    def _set_read_only(self, b):
#        for w in self._ui_widgets():
#            w.setReadOnly(b)
#    
#    def set_busy(self):
#        self._set_read_only(True)
#        for w in self._ui_widgets():
#            w.setStyleSheet(self.STYLE_SHEETS.BUSY)
#
#    def set_clean(self):
#        self._set_read_only(self._init_read_only)
#        for w in self._ui_widgets():
#            w.setStyleSheet(self._init_style_sheet)
#
#    def set_error(self, error_msg=None):
#        self._error_msg = error_msg
#        if self._error_msg:
#            for w in self._ui_widgets():
#                w.setStyleSheet(self._init_style_sheet+'\n'+self.STYLE_SHEETS.ERROR)
#        else:
#            for w in self._ui_widgets():
#                w.setStyleSheet(self._init_style_sheet)
#            
#    def set_tooltip(self, text):
#        for w in self._ui_widgets():
#            w.setToolTip(text)
#    
#class IntValueEditor(QtGui.QSpinBox, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        QtGui.QSpinBox.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#
#    def get_value(self):
#        return self.value()
#    
#    def set_value(self, value):
#        ValueEditorMixin.set_value(self, value)
#
#        if value is None:
#            value = 0
#        try:
#            self.setValue(value)
#        except TypeError:
#            import traceback
#            traceback.print_exc()
#            print '#-----> value was', value, 'in', self._param_editor.param_infos['id']
#            self.setValue(0)
#            self.set_error('GUI ERROR: cannot display value %r'%(value,))
#            
#    def _set_edit_connections(self):
#        self.valueChanged.connect(self.edit_started)
#        self.editingFinished.connect(self.edit_finished)
#
#class PercentValueEditor(QtGui.QProgressBar, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        QtGui.QProgressBar.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#
#    def get_value(self):
#        return self.value()
#    
#    def set_value(self, value):
#        ValueEditorMixin.set_value(self, value)
#
#        if value is None:
#            value = 0
#        try:
#            self.setValue(value)
#        except TypeError:
#            import traceback
#            traceback.print_exc()
#            print '#-----> value was', value, 'in', self._param_editor.param_infos['id']
#            self.setValue(0)
#            self.set_error('GUI ERROR: cannot display value %r'%(value,))
#            
#    def _set_edit_connections(self):
#        self.valueChanged.connect(self.edit_started)
#
#    def _set_read_only(self, b):
#        return
#        
#class PieValueEditor(PieChart, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        PieChart.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#
#        self.set_text_color(
#            OOP='#555',
#            NYS='#AAA',
#            INV='#088',
#            WAIT_INPUT='#088',
#            WIP='#848',
#            IN_PROGRESS='#848',
#            RVW='#A80',
#            RTK='#808',
#            APP='#080',
#            DONE='#080',
#            FIN='#080',
#        )
#        
#    def get_value(self):
#        return self._last_value_set
#    
#    def set_value(self, value):
#        ValueEditorMixin.set_value(self, value)
#
#        if value is None:
#            value = {}
#            
#        try:
#            items = value.items()
#        except (AttributeError, TypeError):
#            import traceback
#            traceback.print_exc()
#            print '#---CANT PIE--> value was', value, 'in', self._param_editor.param_infos['id']
#            self.set_data({'All':'Error'})
#            self.set_error('GUI ERROR: cannot display value %r as Pie'%(value,))
#            return
#        
#        data = collections.defaultdict(int)
#        ids = collections.defaultdict(list)
#        for k, v in items:
#            if not isinstance(v, basestring):
#                v = repr(v)
#            data[v] += 1
#            ids[v].append(k)
#        ids = dict([ (k, '(%s)'%(', '.join(v),)) for k, v in ids.items() ])
#        self.set_data(dict(data))
#        self.set_entries_details(ids)
#        
#    def _set_edit_connections(self):
#        pass
#
#    def _set_read_only(self, b):
#        return
#
#    def set_tooltip(self, text):
#        super(PieValueEditor, self).set_tooltip(
#            text+'\n<br><pre>%s</pre>'%(self.get_legend_text(),)
#        )
#
#class BoolValueEditor(QtGui.QCheckBox, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        QtGui.QCheckBox.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#
#    def get_value(self):
#        return self.isChecked()
#    
#    def set_value(self, value):
#        ValueEditorMixin.set_value(self, value)
#        self.setChecked(value and True or False)
#            
#    def _set_edit_connections(self):
#        self.toggled.connect(self.edit_finished)
#
#    def _set_read_only(self, b):
#        for w in self._ui_widgets():
#            w.setEnabled(not b)
#
#class PythonValueEditor(QtGui.QLineEdit, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        QtGui.QLineEdit.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#
#        self.setAcceptDrops(True)
#
#    def get_value(self):
#        text = str(self.text())
#        #print 'GET PY FROM TEXT:', repr(text)
#        try:
#            value = eval(text)
#        except (SyntaxError, NameError), err:
#            #print '  eval error', err
#            value = text
#        #else:
#            #print '  eval ok'
#        #print '  =>', repr(value)
#        return value
#            
#    def set_value(self, value):
#        #print 'SET PY FROM TEXT, value:', repr(value)
#        ValueEditorMixin.set_value(self, value)
#
#        if isinstance(value, basestring):
#            display_value = value
#        else:
#            display_value = repr(value)
#        self.setText(display_value)
#    
#    def _set_edit_connections(self):
#        self.textEdited.connect(self.edit_started)
#        self.returnPressed.connect(self.edit_finished)
#
#    def dragEnterEvent(self, e):
#        if e.mimeData().hasFormat('kabaret/ids') or e.mimeData().hasFormat('text/plain'):
#            e.accept()
#        else:
#            e.ignore() 
#
#    def dropEvent(self, e):
#        md = e.mimeData()
#        if md.hasFormat('kabaret/ids'):
#            #print 'using kabaret/ids'
#            value = str(md.data('kabaret/ids')).split('\n')
#            if len(value) < 2:
#                value = value[0]
#            self.setText(value)
#        elif md.hasFormat('text/plain'):
#            #print 'using text/plain'
#            self.setText(e.mimeData().text())
#        #TODO: decide if we use edit_finished() or just edit_started()
#        if 0:
#            self.setFocus()
#            self.edit_started()
#        else:
#            self.edit_finished()
#
#class ChoiceEditor(QtGui.QComboBox, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        QtGui.QComboBox.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#        
#        self.choices = list(options.get('choices'))
#    
#        self.addItems(self.choices)
#        
#    def get_value(self):
#        return self.currentText()
#    
#    def set_value(self, value):
#        ValueEditorMixin.set_value(self, value)
#        try:
#            index = self.choices.index(value)
#        except ValueError:
#            self.addItem(value)
#            self.choices.append(value)
#            index = len(self.choices)
#        self.setCurrentIndex(index)
#
#    def _set_edit_connections(self):
#        self.currentIndexChanged.connect(self.edit_finished)
#
#    def _set_read_only(self, b):
#        self.setEnabled(not b)
#
#class ChoicesForEditor(QtGui.QWidget, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        QtGui.QWidget.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#        
#        self.target_param_name = options.get('target_param')
#        if self.target_param_name is None:
#            self.set_error('NO "target_param" value in the editor options!')
#        
#        self._buttons = []    
#        self.setLayout(QtGui.QVBoxLayout())
#    
#    def _ui_widgets(self):
#        return self._buttons
#    
#    def get_value(self):
#        return self._last_value_set
#    
#    def set_value(self, value):
#        #print 'SET on CHOICE FOR, value:', repr(value)
#        ValueEditorMixin.set_value(self, value)
#        self.clear()
#        self.build()
#        
#    def _set_edit_connections(self):
#        pass
#    
#    def _set_read_only(self, b):
#        for button in self._ui_widgets():
#            button.setEnabled(b)
#            
#    def clear(self):
#        lo = self.layout()
#        while lo.count():
#            li = lo.takeAt(0)
#            w = li.widget()
#            if w is not None:
#                w.deleteLater()
#            del li
#        self._buttons = []
#
#    def build(self):
#        if not self._last_value_set:
#            lb = QtGui.QLabel('No choice for '+self.target_param_name, self)
#            self.layout().addWidget(lb)
#            self._buttons.append(lb)
#            return 
#        
#        for v in self._last_value_set:
#            label = v
#            if isinstance(label, tuple):
#                #TODO: this sucks like dyson. find a cleaner way to handle uid choices
#                label = '/'.join(label)
#            elif not isinstance(label, basestring):
#                label = repr(v)
#            b = QtGui.QPushButton(label, self)
#            self.layout().addWidget(b)
#            b.clicked.connect(lambda checked=False, v=v: self.on_button_clicked(checked, v))
#            self._buttons.append(b)
#            
#    def on_button_clicked(self, *args):
#        if len(args) == 1:
#            # pyside...
#            value = args[0]
#        else:
#            # pyqt...
#            value = args[-1]
#        if self.target_param_name is None:
#            return
#        self._param_editor.value_editor_set(value, self.target_param_name)
#
#class DateValueEditor(QtGui.QWidget, ValueEditorMixin):
#    _SHOW_TIME = False
#    def __init__(self, parent, param_editor, options):
#        QtGui.QWidget.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#
#        layout = QtGui.QVBoxLayout()
#        layout.setContentsMargins(0,0,0,0)
#        layout.setSpacing(0)
#        self.setLayout(layout)
#        
#        top_layout = QtGui.QHBoxLayout()
#        top_layout.setContentsMargins(0,0,0,0)
#        layout.addLayout(top_layout)
#        
#        if self._SHOW_TIME:
#            self.date_edit = QtGui.QDateTimeEdit(self)
#        else:
#            self.date_edit = QtGui.QDateEdit(self)
#        top_layout.addWidget(self.date_edit)
#        
#        self.tb = QtGui.QToolButton(self)
#        self.tb.setText('...')
#        self.tb.setCheckable(True)
#        self.tb.setChecked(False)
#        self.tb.toggled.connect(self._on_toggle_calendar)
#        top_layout.addWidget(self.tb)
#        
#        self.calendar = QtGui.QCalendarWidget(self)
#        self.calendar.setGridVisible(True)
#        layout.addWidget(self.calendar)
#        
#        self.calendar.hide()
#        
#    def _ui_widgets(self):
#        return [self.date_edit]
#    
#    def _on_toggle_calendar(self, checked):
#        self.calendar.setVisible(checked)
#        
#    def get_value(self):
#        qdate = self.date_edit.dateTime().date()
#        if not self._SHOW_TIME:
#            return datetime.date(*qdate.getDate())
#        qtime = self.date_edit.dateTime().time()
#        params = list(qdate.getDate())
#        params += [qtime.hour(), qtime.minute(), qtime.second(), qtime.msec()]
#        return datetime.datetime(*params)
#    
#    def set_value(self, value):
#        ValueEditorMixin.set_value(self, value)
#        if not isinstance(value, (datetime.date, datetime.datetime)):
#            self.set_error('GUI ERROR: cannot display value %r (not a date or datetime)'%(value,))
#        else:
#            qdate = QtCore.QDate(value.year, value.month, value.day)
#            if self._SHOW_TIME:
#                qdatetime = QtCore.QDateTime(
#                    qdate,
#                    QtCore.QTime(value.hour, value.minute, value.second, value.microsecond)
#                )
#                self.date_edit.setDateTime(qdatetime)
#                self.calendar.setSelectedDate(qdate)
#            
#            else:
#                self.date_edit.setDate(qdate)
#                self.calendar.setSelectedDate(qdate)
#            
#    def _set_edit_connections(self):
#        self.date_edit.dateChanged.connect(self.edit_started)
#        self.date_edit.editingFinished.connect(self.edit_finished)
#        self.calendar.activated.connect(self.set_date_from_calendar)
#
#    def set_date_from_calendar(self, date):
#        self.date_edit.setFocus()
#        self.tb.toggle()
#        self.date_edit.setDate(date)
#        self.edit_finished()
#        
#    def _set_read_only(self, b):
#        self.tb.setVisible(not b)
#        self.calendar.setEnabled(not b)
#        ValueEditorMixin._set_read_only(self, b)
#
#class TimestampValueEditor(DateValueEditor):
#    _SHOW_TIME = True
#    def get_value(self):
#        v = super(TimestampValueEditor, self).get_value()
#        return time.mktime(v.timetuple())
#    
#    def set_value(self, value):
#        super(TimestampValueEditor, self).set_value(
#            datetime.datetime.fromtimestamp(value or 0)
#        )
#
#class RelationIdsEditor(QtGui.QWidget, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        QtGui.QWidget.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#
#        self.related_name = param_editor.param_infos['label'].split(' ', 1)[0]
#
#        self.setLayout(QtGui.QVBoxLayout())
#        self.layout().setContentsMargins(0,0,0,0)
#        self.layout().setSpacing(0)
#        
#        self.list = QtGui.QListWidget(self)
#        self.list.setSelectionMode(self.list.ExtendedSelection)
#        self.list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#        self.list.customContextMenuRequested.connect(self._on_menu)
#        self.layout().addWidget(self.list)
#
#    def _ui_widgets(self):
#        return [self.list]
#
#    def get_value(self):
#        return [ str(self.list.item(i).text()) for i in range(self.list.count()) ]
#    
#    def set_value(self, value):
#        ValueEditorMixin.set_value(self, value)
#        
#        if value is None:
#            value = []
#        if not isinstance(value, (list, tuple)):
#            self.set_error('GUI ERROR: Not a node ref list: %r'%(value,))
#            value = []
#            
#        self.list.clear()
#        self.list.addItems(value)
#            
#    def _set_edit_connections(self):
#        pass
#
#    def _set_read_only(self, b):
#        self.list.setEnabled(not b)
#
#    def _on_menu(self, pos):
#        menu = QtGui.QMenu(self)
#        menu.addAction('Add '+self.related_name, self._on_add)        
#        menu.addAction('Remove Selected', self._on_menu_remove_selected)
#        menu.exec_(self.mapToGlobal(pos))
#    
#    def _on_add(self, _=None):
#        ids, ok = QtGui.QInputDialog.getText(
#            self, 'Add %s(s):'%(self.related_name,), 'New %s:'%(self.related_name,),
#        )
#        if not ok:
#            return
#        new_ids = list(set(ids.replace('-', '_').split(' ')))
#        self.list.addItems(new_ids)
#        self.edit_finished()
#        
#    def _on_menu_remove_selected(self):
#        selected_indexes = self.list.selectedIndexes()
#        nb = len(selected_indexes)
#        button = QtGui.QMessageBox.warning(
#            self, 'Delete %s(s):'%(self.related_name,), 'Confirm Delete %d %s(s)'%(nb, self.related_name,),
#            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel
#            
#        )
#        if button != QtGui.QMessageBox.Ok:
#            return
#        selected_ids = [ self.list.itemFromIndex(i).text() for i in selected_indexes ]
#        ids = [ 
#            self.list.item(i).text() 
#            for i in range(self.list.count()) 
#            if self.list.item(i).text() not in selected_ids
#        ]
#        self.list.clear()
#        self.list.addItems(ids)
#        self.edit_finished()
#            
#class NodeRefsValueEditor(QtGui.QWidget, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        QtGui.QWidget.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#
#        self._multiple = True
#        
#        layout = QtGui.QHBoxLayout()
#        layout.setContentsMargins(0,0,0,0)
#        layout.setSpacing(0)
#        self.setLayout(layout)
#        
#        self.list = QtGui.QListWidget(self)
#        self.list.setAcceptDrops(True)
#        self.list.dragEnterEvent = self._list_dragEnterEvent
#        self.list.dropEvent = self._list_dropEvent
#        self.list.dragMoveEvent = self._list_dragMoveEvent
#        layout.addWidget(self.list)
#        
#        self.tb = QtGui.QToolButton(self)
#        self.tb.setText('+')
#        self.tb.setIcon(resources.get_icon(('flow.icons.nodes', 'casting')))
#        self.tb.pressed.connect(self._on_dialog)
#        layout.addWidget(self.tb)
#
#    def set_single(self):
#        self._multiple = False
#        self.list.setSizePolicy(
#            QtGui.QSizePolicy.MinimumExpanding,
#            QtGui.QSizePolicy.Fixed,
#        )
#        height = self.list.fontMetrics().height()*1.5
#        self.list.setMinimumSize(0, height)
#        
#    def _ui_widgets(self):
#        return [self.list]
#    
#    def _on_dialog(self):
#        from . import node_picker
#        np = node_picker.NodePicker(
#            self._param_editor.view,
#            self._param_editor.view.client,
#            'Edit nodes in '+'/'.join(self._param_editor.param_infos['id']),
#            default_root_name=self._options.get('root_name', None),
#            extra_root_names=self._options.get('extra_root_names', {}),
#        )
#        np.allow_multiple_selection(self._multiple)
#        np.set_selected_ids(self.get_value())
#        result = np.exec_()
#        if result == np.Accepted:
#            self.list.clear()
#            self.list.addItems(
#                [ '/'.join(node_id) for node_id in np.get_picked_ids() ]
#            )
#            self.edit_finished()
#            
#    def get_value(self):
#        if self._multiple:
#            return [ tuple(str(self.list.item(i).text()).split('/')) for i in range(self.list.count()) ]
#        item = self.list.item(0)
#        if item is None:
#            return None
#        return tuple(str(item.text()).split('/'))
#    
#    def set_value(self, value):
#        #print 'SET PY FROM TEXT, value:', repr(value)
#        ValueEditorMixin.set_value(self, value)
#        
#        if value is None:
#            value = []
#        if not isinstance(value, (list, tuple)):
#            self.set_error('GUI ERROR: Not a node ref list: %r'%(value,))
#            value = []
#            
#        self.list.clear()
#        if self._multiple:
#            self.list.addItems(
#                [ '/'.join(node_id) for node_id in value ]
#            )
#        else:
#            self.list.addItem('/'.join(value))
#            
#    def _set_edit_connections(self):
#        pass
#        #self.line_edit.textEdited.connect(self.edit_started)
#        #self.line_edit.returnPressed.connect(self.edit_finished)
#
#    def _set_read_only(self, b):
#        self.tb.setEnabled(not b)
#        self.list.setAcceptDrops(not b)
#
#    def _list_dragEnterEvent(self, e):
#        md = e.mimeData()
#        #print '>>>>>', md.formats(), ':', [ md.data(f) for f in md.formats() ]
#        if (
#            md.hasFormat('kabaret/ids') 
#            or md.hasFormat('text/plain')
#            ):
#            e.accept()
#        else:
#            e.ignore() 
#
#    def _list_dragMoveEvent(self, e):
#        if e.dropAction() == QtCore.Qt.LinkAction:
#            e.accept()
#            
#    def _list_dropEvent(self, e):
#        md = e.mimeData()
#        #print '>>>>> drop:', md.formats(), ':', [ md.data(f) for f in md.formats() ]
#        if md.hasFormat('kabaret/ids'):
#            value = str(md.data('kabaret/ids')).split('\n')
#            if self._multiple:
#                self.list.addItems(value)
#            else:
#                self.list.clear()
#                self.list.addItem(value[0])
#        elif md.hasFormat('text/plain'):
#            if not self._multiple:
#                self.list.clear()
#            self.list.addItem(str(e.mimeData().text()))
#        self.edit_finished()
#
#class NodeRefValueEditor(NodeRefsValueEditor):
#    def __init__(self, *args, **kwargs):
#        super(NodeRefValueEditor, self).__init__(*args, **kwargs)
#        self.set_single()
#        
#class TriggerValueEditor(QtGui.QPushButton, ValueEditorMixin):
#    def __init__(self, parent, param_editor, options):
#        QtGui.QPushButton.__init__(self, parent)
#        ValueEditorMixin.__init__(self, param_editor, options)
#
#    def set_label(self, label=None):
#        if label is None:
#            label = 'Trigger' 
#        self.setText(label)
#        
#    def get_value(self):
#        #print 'TRIGGER GET', self._param_editor.param_infos['id']
#        return None
#    
#    def set_value(self, value):
#        #print 'TRIGGER SET', value, self._param_editor.param_infos['id']
#        pass
#    
#    def _set_edit_connections(self):
#        self.clicked.connect(self.on_clicked)
#    
#    def on_clicked(self):
#        #print 'TRIGGER CLICK', self._param_editor.param_infos['id']
#        self._param_editor.value_editor_set(None)
#        self.set_busy()
#
#    def _set_read_only(self, b):
#        pass
#    
#class EditorFactory(object):
#    def __init__(self):
#        super(EditorFactory, self).__init__()
#        self._default_type = PythonValueEditor
#        self._editor_types = {
#            'int': IntValueEditor,
#            'date': DateValueEditor,
#            'bool': BoolValueEditor,
#            'trigger': TriggerValueEditor,
#            'node_refs': NodeRefsValueEditor,
#            'node_ref': NodeRefValueEditor,
#            'timestamp': TimestampValueEditor,
#            'percent': PercentValueEditor,
#            'pie': PieValueEditor,
#            'choice': ChoiceEditor,
#            'choices_for': ChoicesForEditor,
#            'relation_ids': RelationIdsEditor,
#        }
#    
#    def register(self, key, type, is_default=False):
#        self._editor_types[key] = type
#    
#    def create(self, parent, key, param_editor, options=None):
#        return self._editor_types.get(key, self._default_type)(parent, param_editor, options or {})


class NodeRefsValueEditor(QtGui.QWidget, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        QtGui.QWidget.__init__(self, parent)

        self._multiple = True
        
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        self.list = QtGui.QListWidget(self)
        self.list.itemDoubleClicked.connect(self._on_dble_click)
        self.list.setAcceptDrops(True)
        self.list.dragEnterEvent = self._list_dragEnterEvent
        self.list.dropEvent = self._list_dropEvent
        self.list.dragMoveEvent = self._list_dragMoveEvent
        self.list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._on_menu)
        layout.addWidget(self.list)
        
        self.tb = QtGui.QToolButton(self)
        self.tb.setText('+')
        self.tb.setIcon(resources.get_icon(('flow.icons.nodes', 'casting')))
        self.tb.pressed.connect(self._on_dialog)
        layout.addWidget(self.tb)

        if options.get('single'):
            self.set_single()
            
        ValueEditorMixin.__init__(self, controller, options)

    def set_single(self):
        self._multiple = False
        self.list.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.Fixed,
        )
        height = self.list.fontMetrics().height()*1.5
        self.list.setMinimumSize(0, height)
        
    def _ui_widgets(self):
        return [self.list]
    
    def _on_dialog(self):
        from . import node_picker
        np = node_picker.NodePicker(
            self,
            self._controller.client,
            'Edit nodes in '+'/'.join(self._controller.value_id),
            default_root_name=self._options.get('root_name', None),
            extra_root_names=self._options.get('extra_root_names', {}),
        )
        np.allow_multiple_selection(self._multiple)
        np.set_selected_ids(self.get_value())
        result = np.exec_()
        if result == np.Accepted:
            self.list.clear()
            self.list.addItems(
                [ '/'.join(node_id) for node_id in np.get_picked_ids() ]
            )
            self.edit_finished()
            
    def get_value(self):
        if self._multiple:
            return [ tuple(str(self.list.item(i).text()).split('/')) for i in range(self.list.count()) ]
        item = self.list.item(0)
        if item is None:
            return None
        return tuple(str(item.text()).split('/'))
    
    def set_value(self, value):
        #print 'SET PY FROM TEXT, value:', repr(value)
        ValueEditorMixin.set_value(self, value)
        
        if value is None:
            value = []
        if not isinstance(value, (list, tuple)):
            self.set_error('GUI ERROR: Not a node ref list: %r'%(value,))
            value = []
            
        self.list.clear()
        if self._multiple:
            self.list.addItems(
                [ '/'.join(node_id) for node_id in value ]
            )
        else:
            self.list.addItem('/'.join(value))
            
    def _set_edit_connections(self):
        pass
        #self.line_edit.textEdited.connect(self.edit_started)
        #self.line_edit.returnPressed.connect(self.edit_finished)

    def _set_read_only(self, b):
        self.tb.setEnabled(not b)
        self.list.setAcceptDrops(not b)

    def _list_dragEnterEvent(self, e):
        md = e.mimeData()
        #print '>>>>>', md.formats(), ':', [ md.data(f) for f in md.formats() ]
        if (
            md.hasFormat('kabaret/ids') 
            or md.hasFormat('text/plain')
            ):
            e.accept()
        else:
            e.ignore() 

    def _list_dragMoveEvent(self, e):
        if e.dropAction() == QtCore.Qt.LinkAction:
            e.accept()
            
    def _list_dropEvent(self, e):
        md = e.mimeData()
        #print '>>>>> drop:', md.formats(), ':', [ md.data(f) for f in md.formats() ]
        if md.hasFormat('kabaret/ids'):
            value = str(md.data('kabaret/ids')).split('\n')
            if self._multiple:
                self.list.addItems(value)
            else:
                self.list.clear()
                self.list.addItem(value[0])
        elif md.hasFormat('text/plain'):
            if not self._multiple:
                self.list.clear()
            self.list.addItem(str(e.mimeData().text()))
        self.edit_finished()

    def _on_menu(self, pos):
        current = self.list.currentItem()
        if current is None:
            return
        menu = QtGui.QMenu(self)
        label = current.text()
        if not label:
            return
        node_id = tuple(label.split('/'))
        menu.addAction('Goto '+label, lambda n=node_id: self._goto(n))        
        menu.addAction('Remove '+node_id[-1], lambda item=current: self._remove_item(item))        
        menu.exec_(self.mapToGlobal(pos))

    def _on_dble_click(self, item):
        label = str(item.text())
        if not label:
            return
        node_id = tuple(label.split('/'))
        self._goto(node_id)
        
    def _goto(self, node_id):
        self._controller.goto(node_id)
    
    def _remove_item(self, item):
        self.list.takeItem(self.list.row(item))
        self.edit_finished()
        
class NodeRefValueEditor(NodeRefsValueEditor):
    def __init__(self, parent, controller, options):
        options_singled = dict(options)
        options_singled['single'] = True
        super(NodeRefValueEditor, self).__init__(parent, controller, options_singled)

from kabaret.gui.widgets.value_editor.editors import StrListValueEditor        
class RelationIdsEditor(StrListValueEditor):
    def __init__(self, *args, **kwargs):
        super(RelationIdsEditor, self).__init__(*args, **kwargs)
        self.set_item_name(
            self._controller.get_label().split(' ', 1)[0]
        )
        self._many_relation_name = self._controller.param_infos.get('ids_for_many', None)
        if self._many_relation_name is not None:
            self.list.itemDoubleClicked.connect(self._on_dble_click)
            
    def _fill_menu(self, menu, current_item):
        if self._many_relation_name is not None and current_item is not None:
            name = current_item.text()
            menu.addAction(
                'Goto %s'%(name,), 
                lambda n=name: self._on_goto_related(related_name=n)
            )
            menu.addSeparator()
        
        super(RelationIdsEditor, self)._fill_menu(menu, current_item)
    
    def _on_dble_click(self, item):
        self._on_goto_related(item.text())
        
    def _on_goto_related(self, related_name):
        self._controller.goto_related(self._many_relation_name, related_name)

#class RelationIdsEditor(QtGui.QWidget, ValueEditorMixin):
#    def __init__(self, parent, controller, options):
#        QtGui.QWidget.__init__(self, parent)
#
#        self.related_name = controller.get_label().split(' ', 1)[0]
#
#        self.setLayout(QtGui.QVBoxLayout())
#        self.layout().setContentsMargins(0,0,0,0)
#        self.layout().setSpacing(0)
#        
#        self.list = QtGui.QListWidget(self)
#        self.list.setSelectionMode(self.list.ExtendedSelection)
#        self.list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#        self.list.customContextMenuRequested.connect(self._on_menu)
#        self.layout().addWidget(self.list)
#
#        ValueEditorMixin.__init__(self, controller, options)
#        
#    def _ui_widgets(self):
#        return [self.list]
#
#    def get_value(self):
#        return [ str(self.list.item(i).text()) for i in range(self.list.count()) ]
#    
#    def set_value(self, value):
#        ValueEditorMixin.set_value(self, value)
#        
#        if value is None:
#            value = []
#        if not isinstance(value, (list, tuple)):
#            self.set_error('GUI ERROR: Not a tuple or list: %r'%(value,))
#            value = []
#            
#        self.list.clear()
#        self.list.addItems(value)
#            
#    def _set_edit_connections(self):
#        pass
#
#    def _set_read_only(self, b):
#        self.list.setEnabled(not b)
#
#    def _on_menu(self, pos):
#        menu = QtGui.QMenu(self)
#        menu.addAction('Add '+self.related_name, self._on_add)        
#        menu.addAction('Remove Selected', self._on_menu_remove_selected)
#        menu.exec_(self.mapToGlobal(pos))
#    
#    def _on_add(self, _=None):
#        ids, ok = QtGui.QInputDialog.getText(
#            self, 'Add %s(s):'%(self.related_name,), 'New %s:'%(self.related_name,),
#        )
#        if not ok:
#            return
#        new_ids = list(set(ids.replace('-', '_').split(' ')))
#        self.list.addItems(new_ids)
#        self.edit_finished()
#        
#    def _on_menu_remove_selected(self):
#        selected_indexes = self.list.selectedIndexes()
#        nb = len(selected_indexes)
#        button = QtGui.QMessageBox.warning(
#            self, 'Delete %s(s):'%(self.related_name,), 'Confirm Delete %d %s(s)'%(nb, self.related_name,),
#            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel
#            
#        )
#        if button != QtGui.QMessageBox.Ok:
#            return
#        selected_ids = [ self.list.itemFromIndex(i).text() for i in selected_indexes ]
#        ids = [ 
#            self.list.item(i).text() 
#            for i in range(self.list.count()) 
#            if self.list.item(i).text() not in selected_ids
#        ]
#        self.list.clear()
#        self.list.addItems(ids)
#        self.edit_finished()

class ParamController(ValueController):
    def __init__(self, client, param_infos):
        super(ParamController, self).__init__(client, param_infos['id'], 'FLOW')
        self.param_infos = param_infos

    def get_label(self):
        return self.param_infos['label']

    def get_tooltip(self):
        tt = self.param_infos['param_type']+' <b>'+self.param_infos['name']+'<b>'
        if self.param_infos['error'] is not None:
            tt += (
                '<br><b><font color=#F00>Error:</font></b>'
                '<pre>'+self.param_infos['error'].strip().replace('Error was:', '\nError was:\n')+'</pre>'
            )
        return tt
    
    def set_editor(self, editor):
        super(ParamController, self).set_editor(editor)

        self.editor.set_label(self.get_label())
        self.editor.set_value(self.param_infos['value'])

        if self.param_infos['upstreams']:
            self.editor.set_linked()
        elif self.param_infos['param_type'] == 'ComputedParam':
            self.editor.set_computed()
        elif self.param_infos['param_type'] != 'CaseParam':
            self.editor.set_volatile()
        else:
            self.editor.set_editable()
            
        # set error after setting edit type:
        self.editor.set_error(self.param_infos['error'])
        self.editor.set_tooltip(self.get_tooltip())

    def set_value(self, value):
        param_id = self._set_value_id or self.value_id
            
        #TODO: debug the client.no_result() context (actually, the pyroOneway that blocks :/)
        with self.client.result_to(lambda result: None):
            self.client.apps.FLOW.cmds.SetParamValue(
                param_id,
                value
            )

    def value_invalidated(self, event):
        #print '---- INVALIDATED EVENT:', event.app_key, event.path, event.etype, event.data
        self.editor.set_busy()
        node_id = self.value_id[:-1]
        param_name = self.value_id[-1][1:] # last of id, without the leading '.'
        #print '+ touched:', param_name
        with self.client.result_to(self._on_reload_infos):
            self.client.apps.FLOW.cmds.GetParamUiInfos(
                node_id, param_name
            )
    
    def _on_reload_infos(self, all_param_infos):
        self.param_infos = all_param_infos[0][1][0]
        #print '> reloading:', self.param_infos['name']
        self.editor.update_value(self.param_infos['value'])
        self.editor.set_error(self.param_infos['error'])
        self.editor.setToolTip(self.get_tooltip())

    def goto_related(self, relation_name, related_name):
        parent_id = self.value_id[:-1]
        related_node_id = parent_id + ('%s:%s'%(relation_name, related_name),)
        self.goto(related_node_id)
        
    def goto(self, node_id):
        self.client.send_event(
            Event('GUI', ['FLOW', 'Nav', 'current'], Event.TYPE.UPDATED, node_id)
        )
        
class ParamEditor(QtGui.QWidget):
    _EDITOR_FACTORY = None
    _ICONS = None
    
    _MAX_ITEM_IN_CONNECTION_MENUS = 20
    
    def __init__(self, parent, param_infos, view):
        if self.__class__._EDITOR_FACTORY is None:
            factory = get_global_factory()
            factory.ensured_registered(
                relation_ids=RelationIdsEditor,
                node_refs=NodeRefsValueEditor,
                node_ref=NodeRefValueEditor,
            )
            
            self.__class__._EDITOR_FACTORY = factory
            
        if self.__class__._ICONS is None:
            # Use local cache the icons, must faster
            # than a lookup in to the resource package cache:
            self.__class__._ICONS = {
                'no_connection_in': resources.get_icon(('flow.icons', 'no_connection_in')),
                'connection_in': resources.get_icon(('flow.icons', 'connection_in')),
                'no_connection_out': resources.get_icon(('flow.icons', 'no_connection_out')),
                'connection_out': resources.get_icon(('flow.icons', 'connection_out')),
            }
            
        super(ParamEditor, self).__init__(parent)
        self.view = view
        self.param_infos = param_infos

        lo = QtGui.QHBoxLayout()
        lo.setContentsMargins(0,0,0,0)
        lo.setSpacing(0)
        self.setLayout(lo)

        my_node_id = param_infos['id'][:-1]
        
        b = QtGui.QToolButton(self)
        b.setPopupMode(b.InstantPopup)
        b.setProperty('hide_arrow', True)
        lo.addWidget(b)
        if not param_infos['upstreams']:
            b.setIcon(self._ICONS['no_connection_in'])
            b.setToolTip('Not connected')
            b._goto_menu = QtGui.QMenu('Not connected', b)
            b.setMenu(b._goto_menu)
            b.setEnabled(False)
        else:
            b.setIcon(self._ICONS['connection_in'])
            b.setToolTip('\n'.join([ '/'.join(id) for id in param_infos['upstreams'] ]))
            b._goto_menu = QtGui.QMenu('Goto Upstream', b)
            count = 0
            for up in param_infos['upstreams']:
                count += 1
                if count > self._MAX_ITEM_IN_CONNECTION_MENUS:
                    b._goto_menu.addAction('And more...')
                    break
                rel_id = make_relative_id(my_node_id, up)
                b._goto_menu.addAction('/'.join(rel_id), lambda up=up: self._goto_upstream(up))
            b.setMenu(b._goto_menu)
        
        self._controller = ParamController(self.view.client, param_infos)
        self._editor = self._EDITOR_FACTORY.create(
            self, param_infos['editor'], self._controller, param_infos.get('editor_options')
        )

        lo.addWidget(self._editor)
        
        b = QtGui.QToolButton(self)
        b.setPopupMode(b.InstantPopup)
        b.setProperty('hide_arrow', True)
        lo.addWidget(b)
        if not param_infos['downstreams']:
            b.setIcon(self._ICONS['no_connection_out'])
            b.setToolTip('Not connected')
            b._goto_menu = QtGui.QMenu('Not connected', b)
            b.setMenu(b._goto_menu)
            b.setEnabled(False)
        else:
            b.setIcon(self._ICONS['connection_out'])
            b.setToolTip('\n'.join([ '/'.join(id) for id in param_infos['downstreams'] ]))
            b._goto_menu = QtGui.QMenu('Goto Downstream', b)
            count = 0
            for down in param_infos['downstreams']:
                count += 1
                if count > self._MAX_ITEM_IN_CONNECTION_MENUS:
                    b._goto_menu.addAction('And more...')
                    break
                rel_id = make_relative_id(my_node_id, down)
                b._goto_menu.addAction('/'.join(rel_id), lambda down=down: self._goto_downstream(down))
            b.setMenu(b._goto_menu)

#        self.start_listening()

    def deleteLater(self):
        self._controller.stop_listening()
        super(ParamEditor, self).deleteLater()
        
#    def start_listening(self):
#        self.view.client.add_event_handler(
#            self._on_param_touched, 
#            'FLOW', 
#            self.param_infos['id'], 
#            etype=Event.TYPE.INVALIDATED
#        )
#    
#    def stop_listening(self):
#        self.view.client.remove_event_handler(
#            self._on_param_touched
#        )

    def _goto_upstream(self, up_id):
        self.view.goto(up_id)
        
    def _goto_downstream(self, down_id):
        self.view.goto(down_id)
    
#    def value_editor_set(self, value, param_name=None):
#        '''
#        Trigger the command that will set the given 
#        value to the param edited here.
#        
#        If param_name is not None, it contains the name
#        of the param to set instead of the current one
#        (The param path will always be the current one).
#        '''
#        client = self.view.client
#        param_id = self.param_infos['id']
#        if param_name is not None:
#            param_id = param_id[:-1]+('.'+param_name,)
#        #TODO: debug the client.no_result() context (actually, the pyroOneway that blocks :/)
#        with client.result_to(lambda result: None):
#            client.apps.FLOW.cmds.SetParamValue(
#                param_id,
#                value
#            )
#
#    def _on_param_touched(self, event):
#        #print '---- INVALIDATED EVENT:', event.app_key, event.path, event.etype, event.data
#        self._editor.set_busy()
#        node_id = self.param_infos['id'][:-1]
#        param_name = self.param_infos['name']
#        #print '+ touched:', param_name
#        with self.view.client.result_to(self._on_reload_infos):
#            self.view.client.apps.FLOW.cmds.GetParamUiInfos(
#                node_id, param_name
#            )
#    
#    def _on_reload_infos(self, all_param_infos):
#        self.param_infos = all_param_infos[0][1][0]
#        #print '> reloading:', self.param_infos['name']
#        self._editor.update_value(self.param_infos['value'])
#        self._editor.set_error(self.param_infos['error'])
#        self._set_editor_tooltip()


class ParamsGroup(QtGui.QGroupBox):
    _SS = 'QGroupBox{}'
    def __init__(self, parent, name, view, open=True):
        super(ParamsGroup, self).__init__(parent)
        self.setStyleSheet(self._SS)
        
        self.view = view
        if name:
            if name.startswith('_'):
                name = name[1:]
            self.setTitle(name)
            
        lo = QtGui.QVBoxLayout()
        lo.setContentsMargins(0, 10, 0, 0)
        lo.setSpacing(0)
        self.setLayout(lo)
        
        self._holder = QtGui.QWidget(self)
        self._holder.setLayout(QtGui.QFormLayout())
        lo.addWidget(self._holder)
                
        self._editors = []

        self.setCheckable(True)
        self.toggled.connect(self._on_toggled)
        self.setChecked(open)

    def _set_closed(self, b):
        lo = self.layout()
        for i in range(lo.count()):
            lo.itemAt(i).widget().setHidden(b)
        self.setFlat(b)
        self.setStyleSheet(self._SS) # force update of property dependent style
        self.view.set_default_group_state(str(self.title()), open=not b)
    
    def _on_toggled(self, b):
        self._set_closed(not b)
        
    def add_param(self, param_infos):
        editor = ParamEditor(self._holder, param_infos, self.view)
        if param_infos['editor'] == 'trigger':
            label = ''
        else:
            label = param_infos['label']
        
        self._holder.layout().addRow(label, editor)
        self._editors.append(editor)
        
    def clear(self):
        for e in self._editors:
            e.deleteLater()
        self._editors = []
    
    def deleteLater(self):
        self.clear()
        super(ParamsGroup, self).deleteLater()
        
class ParamsView(AbstractGuiScrollView):
    def __init__(self, parent, client, app_name):
        super(ParamsView, self).__init__(parent, client, app_name)

        self._current_node_id = None

        lo = QtGui.QVBoxLayout()
        self.widget().setLayout(lo)

        # MENU
        self.menu_bar = QtGui.QMenuBar(self)
        lo.addWidget(self.menu_bar)

        options_menu = self.menu_bar.addMenu('Options')
        self._default_group_state = False
        self.reset_default_group_states = options_menu.addAction('Open All Groups', self.open_all_groups)
        self.reset_default_group_states = options_menu.addAction('Close All Groups', self.close_all_groups)

        options_menu.addSeparator()
        
        self.show_protected_params = False
        self.toggle_protected_action = options_menu.addAction('Show Protected Params', self.toggle_protected)
        self.toggle_protected_action.setCheckable(True)
        self.toggle_protected_action.setChecked(False)

        # TOP BAR
        top_bar = QtGui.QHBoxLayout()
        
        self._sync_with_current_nav = True
        self._sync_with_current_nav_butt = QtGui.QPushButton(self)
        self._sync_with_current_icon_ON = resources.get_icon(
            ('gui.icons', 'sync_on'), self._sync_with_current_nav_butt
        )
        self._sync_with_current_icon_OFF = resources.get_icon(
            ('gui.icons', 'sync_off'), self._sync_with_current_nav_butt
        )
        self._sync_with_current_nav_butt.setIcon(
            self._sync_with_current_nav 
            and self._sync_with_current_icon_ON
            or self._sync_with_current_icon_OFF
        )
        self._sync_with_current_nav_butt.setCheckable(True)
        self._sync_with_current_nav_butt.setChecked(self._sync_with_current_nav)
        self._sync_with_current_nav_butt.toggled.connect(self._on_sync_current_nav_click)
        self._on_sync_current_nav_click(True)
        top_bar.addWidget(self._sync_with_current_nav_butt)
        
        self._path_label = PathLabel(self)
        self._path_label.node_id_clicked.connect(self.goto)
        top_bar.addWidget(self._path_label)
        
        top_bar.addStretch(10)
        
        lo.addLayout(top_bar)
        
        # CONTENT DYNAMIC LAYOUT FOR PARAMS
        self._dyn_lo = QtGui.QVBoxLayout()
        lo.addLayout(self._dyn_lo)
        
        lo.addStretch(10)
                
        self._default_group_states = {}
                
        self.client.add_event_handler(
            self.on_nav_current_changed, 'GUI', ['FLOW', 'Nav', 'current']
        )

    def hide_path_label(self, b=True):
        self._path_label.setVisible(not b)
        
    def on_view_toggled(self, visible):
        super(ParamsView, self).on_view_toggled(visible)
        if self._is_active:
            self.reload_node_id()
    
    def _on_sync_current_nav_click(self, checked):
        self._sync_with_current_nav = checked
        self._sync_with_current_nav_butt.setIcon(
            self._sync_with_current_nav 
            and self._sync_with_current_icon_ON
            or self._sync_with_current_icon_OFF
        )
        self._sync_with_current_nav_butt.setToolTip(
            checked
            and 'Follows node selection\nClick to stick to this node.'
            or 'Does not follow node selection\nClick to revert to follow mode.'
        )
        if self._current_node_id is not None:
            self.goto(self._current_node_id)
        
    def clear(self):
        self._path_label.clear()
        
        while self._dyn_lo.count():
            li = self._dyn_lo.takeAt(0)
            li.widget().deleteLater()
            del li
    
    def on_connect(self):
        if self._current_node_id:
            self.reload_node_id()
        
    def on_disconnect(self):
        self.clear()
        
    def on_nav_current_changed(self, event):
        if not self._is_active:
            self._current_node_id = event.data
        elif self._sync_with_current_nav:
            self.load_node_id(event.data)
    
    def reload_node_id(self):
        node_id = self._current_node_id
        self._current_node_id = None
        self.load_node_id(node_id)

    def load_node_id(self, node_id):
#        import time
#        self._times = [('load_node_id', time.time())]
        if self._current_node_id == node_id:
            return
        self._current_node_id = node_id
        
        if not self.is_active():
            return
        
        self.clear()
        if not node_id:
            return
        
        self._path_label.set_node_id(node_id)

        with self.client.result_to(self.on_get_params, self.on_get_params_error):
            self.client.apps.FLOW.cmds.GetParamUiInfos(node_id)

#        self._times.append(('command run', time.time()))

    def on_get_params_error(self, future, error):
        self._dyn_lo.addWidget(
            QtGui.QLabel(
                '<B><FONT COLOR=#FF0000>ERROR:</FONT></B><br>\n'+str(error),
                self
            )
        )
        
    def on_get_params(self, grouped_params_infos):
#        import time
#        self._times.append(('receive param infos', time.time()))

        # Find the lowest group index for each group:

        lo = self._dyn_lo
        last_group_name = None
        group = None
        for group_name, param_infos_list in grouped_params_infos:
            if not self.show_protected_params and group_name.startswith('_'):
                continue
            if group is None or last_group_name != group_name:
                open = self._default_group_states.get(
                    group_name, 
                    (not group_name) and True or self._default_group_state
                )
                group = ParamsGroup(self, group_name, self, open=open)
                lo.addWidget(group)
            last_group_name = group_name
            for param_infos in param_infos_list:
                if not self.show_protected_params and param_infos['name'].startswith('_'):
                    continue
                group.add_param(param_infos)

#        import time
#        self._times.append(('UI done', time.time()))

#        print '#####__________ParamsView load timings:'
#        prev_time = None
#        for label, t in self._times:
#            elapsed = '' 
#            if prev_time is not None:
#                elapsed = str(t - prev_time)
#            print '  ', label, elapsed
#            prev_time = t
            
    def set_default_group_state(self, group_name, open):
        self._default_group_states[group_name] = open
        
    def goto(self, param_id):
        if param_id[-1].startswith('.'):
            param_id = param_id[:-1]
        self.client.send_event(
            Event('GUI', ['FLOW', 'Nav', 'current'], Event.TYPE.UPDATED, param_id)
        )

    def open_all_groups(self):
        self._default_group_state = True
        self._default_group_states = {}
        self.reload_node_id()
    
    def close_all_groups(self):
        self._default_group_state = False
        self._default_group_states = {}
        self.reload_node_id()
    
    def toggle_protected(self):
        self.show_protected_params = not self.show_protected_params
        self.reload_node_id()
