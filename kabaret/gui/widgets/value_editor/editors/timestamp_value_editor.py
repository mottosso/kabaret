'''




'''

import time
import datetime

from . import datetime_value_editor

class TimestampValueEditor(datetime_value_editor.DatetimeValueEditor):
    _SHOW_TIME = True
    def get_value(self):
        v = super(TimestampValueEditor, self).get_value()
        return time.mktime(v.timetuple())
    
    def set_value(self, value):
        super(TimestampValueEditor, self).set_value(
            datetime.datetime.fromtimestamp(value or 0)
        )
