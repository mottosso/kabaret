'''



'''
import urlparse

from kabaret.core.events.event import Event

from kabaret.gui.widgets import QtGui, QtCore

class _Base(object):
    @classmethod
    def from_dict(cls, parent, data):
        raise NotImplementedError
    
    def __init__(self, parent):
        super(_Base, self).__init__()
        self.parent = parent
    
    def root(self):
        return self.parent and self.parent.root() or self
        
    def build(self):
        raise NotImplementedError
    
    def clear(self):
        raise NotImplementedError
    
    def exec_link(self, link):
        if not self.parent:
            raise Exception('Cannot exec link without client')
        self.root().exec_link(link)

class Widget(_Base):
    _USER_WIDGETS = {}

    @classmethod
    def from_dict(cls, parent, data):
        widget = cls(parent, **data)
        return widget

    @classmethod
    def user_widget(cls, klass):
        try:
            name = klass.widget_name()
        except AttributeError:
            name = klass.__name__
        cls._USER_WIDGETS[name] = klass
        return klass
    
    @classmethod
    def get_widget_class(cls, widget_type):
        return cls._USER_WIDGETS[widget_type]

    def __init__(self, parent, widget, **config):
        super(Widget, self).__init__(parent)
        self.parent = parent
        self.widget_type = widget
        self.config = config
        self.widget = None
    
    def root(self):
        return self.parent and self.parent.root() or self
    
    def get_align(self):
        return {
            None:QtCore.Qt.AlignLeft,
            'left': QtCore.Qt.AlignLeft,
            'right': QtCore.Qt.AlignRight,
            'center': QtCore.Qt.AlignHCenter,
            'jutify': QtCore.Qt.AlignJustify,
        }[self.config.get('align', None)]
    
    def get_style_sheet(self):
        ss = {}
        try:
            ss['color'] = self.config['color']
        except KeyError:
            pass
        try:
            ss['background'] = self.config['bg']
        except KeyError:
            pass
        try:
            ss['border'] = self.config['border']
        except KeyError:
            pass
        if not ss:
            return None
        return '; '.join( ['%s: %s'%(k, v) for k, v in ss.items() ])

    def build(self, parent, layout):
        widget_class = self.get_widget_class(self.widget_type)
        self.widget = widget_class(parent, self, self.config)
        ss = self.get_style_sheet()
        if ss:
            self.widget.setStyleSheet('%s{%s;}'%(self.widget.__class__.__name__, ss))
        layout.addWidget(
            self.widget,
            self.config.get('extend', 0),
            self.get_align(),
        )
            
    def clear(self):
        if self.widget is None:
            return
        self.widget.deleteLater()
        self.widget = None
    
class Row(_Base):
    
    @classmethod
    def from_dict(cls, parent, data):
        row = cls(parent)
        for wd in data['widgets']:
            row.widgets.append(Widget.from_dict(row, wd))
        return row
        
    def __init__(self, parent):
        super(Row, self).__init__(parent)
        self.parent = parent
        self.widgets = []
        
    def build(self, parent):
        parent_lo = parent.layout()
        lo = QtGui.QHBoxLayout()
        parent_lo.addLayout(lo)
        
        for widget in self.widgets:
            widget.build(parent, lo)

    def clear(self):
        [ widget.clear() for widget in self.widgets ]
        
class Definition(_Base):
    
    @classmethod
    def from_dict(cls, client, data):
        definition = cls(client)
        definition.title = data.get('title', 'UntitledView')
        definition.query = data.get('query', None)
        query_digest = None
        if definition.query:
            query_digest = definition.query
        definition.rows.append(
            Row.from_dict(
                definition,
                {
                    'widgets':[
                        {
                            'widget':'Label', 
                            'text':definition.title, 
                            'format':'<center><H1>%s</H1></center>',
                            'tooltip': query_digest,
                        }
                    ]
                }
            )
        )
        for rd in data.get('rows', []):
            definition.rows.append(Row.from_dict(definition, rd))
        return definition
        
    def __init__(self, client):
        super(Definition, self).__init__(None)
        self.client = client
        self.title = 'Untitled'
        
        self.rows = []
    
    def build(self, parent):        
        for row in self.rows:
            row.build(parent)
        parent.layout().addStretch()
        
    def clear(self):
        [ row.clear() for row in self.rows ]
    
    def exec_link(self, link):
        parsed = urlparse.urlparse(link)
        if parsed.scheme == 'kabaret':
            # In python 2.6, the urlparse fail to get netloc on
            # exotic scheme. So we reparse with http scheme forced:
            # (Anyway, even on 2.7, the query is wrong under exotic scheme)
            parsed = urlparse.urlparse(parsed.path, scheme='http')
            if parsed.netloc == 'Event':
                params = urlparse.parse_qs(parsed.query)
                app_key = params['app_key'][0]
                path = params['path']
                etype = params['etype'][0]
                if 'node_id' in params:
                    data = tuple(params.pop('node_id'))
                else:
                    data = params['data']
                print 'sending', app_key, path, etype, data
                self.client.send_event(Event(app_key, path, etype, data))
