'''



'''

import collections

from kabaret.gui.styles import get_style_values

from ... import QtCore, QtGui
from .. import ValueEditorMixin


class PieChart(QtGui.QWidget):
    def __init__(self, parent):
        super(PieChart, self).__init__(parent)
        
        self._entries_details = {}
        self.data = {}
        self.total = 0
        self._text_colors = {'None':'#F00', True: '#080', False: '#800'}
        
        # cached for draw speed:
        self._color_names = QtGui.QColor.colorNames()
        self._nb_color_name = len(self._color_names)
        
        self.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding,
        )
        
    def set_data(self, data):
        self._entries_details = {}
        self.data = data

        try:
            self.total = sum(self.data.values())
        except TypeError:
            self.data = {}
            self.total = 0
            
        h = (len(self.data)+1)*self.fontMetrics().height() * 1.5
        self.setMinimumHeight(h)
    
    def set_entries_details(self, details):
        self._entries_details = dict(details)
        
    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(p.Antialiasing, True)

        colorPos = 13
        height = self.rect().height()
        pieRect = QtCore.QRect(0, 0, height, height)
        
        legendRect = self.rect()
        legendRect.setLeft(pieRect.width())
        legendRect.adjust(10,10,-10,-10)
        lastAngleOffset = 0
        currentPos = 0
        
        # bring to local for speed
        total = self.total
        get_color_for = self.get_color_for
        get_detailed_text = self.get_detailed_text
        light = QtGui.QColor(255, 255, 255, 200)#QtCore.Qt.white
        
        for text in sorted(self.data.keys()):
            value = self.data[text]
            angle = int(16*360*(value/(total*1.0)))
            col = QtGui.QColor(get_color_for(text, colorPos))
            colorPos += 1
            
            rg = QtGui.QRadialGradient(
                QtCore.QPointF(pieRect.center()), pieRect.width()/2.0,
                QtCore.QPointF(pieRect.topLeft())
            )
            rg.setColorAt(0, light)
            rg.setColorAt(1, col)
            p.setBrush(rg)
            pen = p.pen()
            p.setPen(QtCore.Qt.NoPen)
            
            p.drawPie(pieRect, lastAngleOffset, angle)
            lastAngleOffset += angle
            
            fh = self.fontMetrics().height()
            legendEntryRect = QtCore.QRect(0,(fh*1.5)*currentPos,fh,fh)
            currentPos += 1
            legendEntryRect.translate(legendRect.topLeft())
            
            lg = QtGui.QLinearGradient(
                QtCore.QPointF(legendEntryRect.topLeft()),
                QtCore.QPointF(legendEntryRect.bottomRight())
            )
            lg.setColorAt(0, col)
            lg.setColorAt(1, light)
            p.setBrush(lg)
            p.drawRect(legendEntryRect)
            
            textStart = legendEntryRect.topRight()
            textStart = textStart + QtCore.QPoint(self.fontMetrics().width('x'), 0)
            
            textEnd = QtCore.QPoint(legendRect.right(), legendEntryRect.bottom())
            textEntryRect = QtCore.QRect(textStart, textEnd)
            p.setPen(pen)
            p.drawText(textEntryRect, QtCore.Qt.AlignVCenter, get_detailed_text(text))
    
    def get_detailed_text(self, text):
        if text in self._entries_details:
            text += '  '+self._entries_details[text]
        return text
    
    def get_legend_text(self):
        return '\n'.join(
            '%s: %s'%(k,v) for k,v in self.data.items()
        )

    def set_text_color(self, **text_to_color):
        self._text_colors.update(text_to_color)
        
    def get_color_for(self, text, index=None):
        '''
        Returns the name of the color to use for 
        the given text at the given index.
        '''
        color_name = self._text_colors.get(text)
        if color_name is None:
            print 'Pie color not found', text
            return self._color_names[index%self._nb_color_name]
        return color_name

class PieValueEditor(PieChart, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        PieChart.__init__(self, parent)

        ValueEditorMixin.__init__(self, controller, options)

    def get_value(self):
        return self._last_value_set
    
    def set_value(self, value):
        ValueEditorMixin.set_value(self, value)

        if value is None:
            value = {}
            
        try:
            items = value.items()
        except (AttributeError, TypeError):
            import traceback
            traceback.print_exc()
            print '#---CANT PIE--> value was', value, 'in', self.value_id
            self.set_data({'All':'Error'})
            self.set_error('GUI ERROR: cannot display value %r as Pie'%(value,))
            return
        
        data = collections.defaultdict(int)
        ids = collections.defaultdict(list)
        for k, v in items:
            if not isinstance(v, basestring):
                v = repr(v)
            data[v] += 1
            ids[v].append(k)
        ids = dict([ (k, '(%s)'%(', '.join(v),)) for k, v in ids.items() ])
        self.set_data(dict(data))
        self.set_entries_details(ids)
        
    def _set_edit_connections(self):
        pass

    def _set_read_only(self, b):
        return

    def set_tooltip(self, text):
        super(PieValueEditor, self).set_tooltip(
            text+'\n<br><pre>%s</pre>'%(self.get_legend_text(),)
        )

class PieStatusesEditor(PieValueEditor):
    def __init__(self, *args, **kwargs):
        super(PieStatusesEditor, self).__init__(*args, **kwargs)
        self.set_text_color(**get_style_values('statuses'))
        
