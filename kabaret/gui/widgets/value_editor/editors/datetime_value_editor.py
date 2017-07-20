'''




'''

import datetime

from ... import QtCore, QtGui
from .. import ValueEditorMixin


class DatetimeValueEditor(QtGui.QWidget, ValueEditorMixin):
    _SHOW_TIME = False
    def __init__(self, parent, controller, options):
        QtGui.QWidget.__init__(self, parent)

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        top_layout = QtGui.QHBoxLayout()
        top_layout.setContentsMargins(0,0,0,0)
        layout.addLayout(top_layout)
        
        if self._SHOW_TIME:
            self.date_edit = QtGui.QDateTimeEdit(self)
        else:
            self.date_edit = QtGui.QDateEdit(self)
        top_layout.addWidget(self.date_edit)
        
        self.tb = QtGui.QToolButton(self)
        self.tb.setText('...')
        self.tb.setCheckable(True)
        self.tb.setChecked(False)
        self.tb.toggled.connect(self._on_toggle_calendar)
        top_layout.addWidget(self.tb)
        
        self.calendar = QtGui.QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        layout.addWidget(self.calendar)
        
        self.calendar.hide()
        
        ValueEditorMixin.__init__(self, controller, options)
        
    def _ui_widgets(self):
        return [self.date_edit]
    
    def _on_toggle_calendar(self, checked):
        self.calendar.setVisible(checked)
        
    def get_value(self):
        qdate = self.date_edit.dateTime().date()
        if not self._SHOW_TIME:
            return datetime.date(*qdate.getDate())
        qtime = self.date_edit.dateTime().time()
        params = list(qdate.getDate())
        params += [qtime.hour(), qtime.minute(), qtime.second(), qtime.msec()]
        return datetime.datetime(*params)
    
    def set_value(self, value):
        ValueEditorMixin.set_value(self, value)
        if not isinstance(value, (datetime.date, datetime.datetime)):
            self.set_error('GUI ERROR: cannot display value %r (not a date or datetime)'%(value,))
        else:
            qdate = QtCore.QDate(value.year, value.month, value.day)
            if self._SHOW_TIME:
                qtime = QtCore.QTime(value.hour, value.minute, value.second, value.microsecond/1000)
                qdatetime = QtCore.QDateTime(
                    qdate, qtime
                )
                self.date_edit.setDateTime(qdatetime)
                self.calendar.setSelectedDate(qdate)
            
            else:
                self.date_edit.setDate(qdate)
                self.calendar.setSelectedDate(qdate)
            
    def _set_edit_connections(self):
        self.date_edit.dateChanged.connect(self.edit_started)
        self.date_edit.editingFinished.connect(self.edit_finished)
        self.calendar.activated.connect(self.set_date_from_calendar)

    def set_date_from_calendar(self, date):
        self.date_edit.setFocus()
        self.tb.toggle()
        self.date_edit.setDate(date)
        self.edit_finished()
        
    def _set_read_only(self, b):
        self.tb.setVisible(not b)
        self.calendar.setEnabled(not b)
        ValueEditorMixin._set_read_only(self, b)
