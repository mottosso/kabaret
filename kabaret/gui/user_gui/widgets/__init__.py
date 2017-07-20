'''



'''
from kabaret.core.utils import resources

from kabaret.gui.widgets import QtGui, QtCore

from ..definition import Widget

# import all sub modules so that they are registered on Widget:
from .tree import Tree

@Widget.user_widget
class Pix(QtGui.QLabel):
    
    def __init__(self, parent, manager, config):
        super(Pix, self).__init__(parent)
        self.manager = manager
        self.config = config

        self._fixed_size = QtCore.QSize(0,0)
        
        pix_ref = config.get('pix', None)
        if pix_ref is None:
            pix_ref = config.get('icon', None)
        if pix_ref is not None:
            pix = resources.get_pixmap(*pix_ref)
            self.setPixmap(pix)
            self._fixed_size = pix.size()
            
        self.setSizePolicy(
            QtGui.QSizePolicy.Fixed,
            QtGui.QSizePolicy.Fixed,
        )

    def sizeHint(self):
        return self._fixed_size
    
@Widget.user_widget
class Label(QtGui.QLabel):
    
    def __init__(self, parent, manager, config):
        super(Label, self).__init__(parent)
        self.manager = manager
        self.config = config
        
        text = config.get('text', 'Label...')
        format = config.get('format')
        if format is not None:
            try:
                text = format%(text,)
            except:
                pass
        self.setText(text)
        
        try:
            tt = config['tooltip']
        except KeyError:
            pass
        else:
            self.setToolTip(tt or '')
            
        if config.get('short', False):
            self.setSizePolicy(
                QtGui.QSizePolicy.Ignored,
                QtGui.QSizePolicy.Ignored,
            )
        
        self.linkActivated.connect(self.on_link)
        
    def on_link(self, link):
        self.manager.exec_link(str(link))
        
        
@Widget.user_widget
class Button(QtGui.QPushButton):
    
    def __init__(self, parent, manager, config):
        super(Button, self).__init__(parent)
        self.manager = manager
        self._config = config
        
        self.setText(self._config.get('text', 'Button'))
        
        icon_ref = self._config.get('icon')
        if icon_ref is not None:
            icon = resources.get_icon(icon_ref, for_widget=self)
            self.setIcon(icon)

@Widget.user_widget
class Tools(QtGui.QToolButton):
    
    def __init__(self, parent, manager, config):
        super(Tools, self).__init__(parent)
        self.manager = manager
        self._config = config
        
        self.setText(config.get('label', ''))
        self.setPopupMode(self.InstantPopup)
        
        self._action_names = config.get('actions',[])
        for name in self._action_names:
            self.addAction(QtGui.QAction(name, self))

@Widget.user_widget
class Choice(QtGui.QComboBox):
    
    def __init__(self, parent, manager, config):
        super(Choice, self).__init__(parent)
        self.manager = manager
        self._config = config
        
        self.choices = config.get('choices', [])
        self.index_to_choice = dict([ (i, v) for i, v in enumerate(self.choices) ])
        self.addItems(self.choices)
        
        selected = config.get('selected', None)
        if selected:
            try:
                index = self.choices.index(selected)
            except ValueError:
                pass
            else:
                self.setCurrentIndex(index)
            
        
        