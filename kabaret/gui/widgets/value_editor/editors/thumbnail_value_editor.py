'''




'''

import os
import shutil
import time

from ... import QtCore, QtGui
from .. import ValueEditorMixin

_CLEAR_PIX = [
"16 16 2 1",
". c #222222",
"# c #880000",
"................",
"......###...###.",
".......###.###..",
"........#####...",
".........###....",
"........#####...",
".......###.###..",
"......###...###.",
"................",
"................",
"................",
"................",
"................",
"................",
"................",
"................",
]

class WindowMover(QtCore.QObject):
    def __init__(self, widget):
        super(WindowMover, self).__init__(widget)
        self.window = widget.window()
        self.down_pos = None
        self.start_pos = None
        
    def eventFilter(self, obj, event):
        if event.type() == event.MouseButtonPress:
            self.down_pos = event.globalPos()
            self.start_pos = self.window.pos()
            obj.grabMouse()
            return True
        elif self.down_pos is not None and event.type() == event.MouseMove:
            delta = event.globalPos() - self.down_pos
            self.window.move(self.start_pos + delta)
            return True
        elif event.type() == event.MouseButtonRelease:
            self.down_pos = None
            self.start_pos = None
            obj.releaseMouse()
            return True
        else:
            return super(WindowMover, self).eventFilter(obj, event)

class ScreenGrabDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(ScreenGrabDialog, self).__init__(parent)
        
        self.window_to_hide = parent.window()
        self.restore_geom = None
        
        
        self._decoration_height = None
        self.winframe_w = 4
        self.winframe_h = 8
        
        self.setWindowTitle('SnapShot')
        
        self.screen_pix = self.grab_screen()
        
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(0)
        
        self.view = QtGui.QGraphicsView(self)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setResizeAnchor(self.view.NoAnchor)
        self.view.setTransformationAnchor(self.view.NoAnchor)
        self.view.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft)
        self.view.setCursor(QtCore.Qt.SizeAllCursor)
        self.layout().addWidget(self.view)
        
        self.mover = WindowMover(self)
        self.view.installEventFilter(self.mover)

        b = QtGui.QPushButton('Capture', self)
        b.clicked.connect(self.accept)
        self.layout().addWidget(b)
        
        self.scene = QtGui.QGraphicsScene()
        self.pix_item = self.scene.addPixmap(self.screen_pix)
        
        self.view.setScene(self.scene)

        self.resize(100, 100)
        
    def grab_screen(self):
        self.restore_geom = self.window_to_hide.geometry()
        self.window_to_hide.hide()
        time.sleep(0.2)
        screen_pix = QtGui.QPixmap.grabWindow(QtGui.QApplication.desktop().winId())        
        return screen_pix
    
    def moveEvent(self, event):
        pos = event.pos()
        x = pos.x()
        y = pos.y()
        if self._decoration_height is None:
            style = self.style()
            self._decoration_height = style.pixelMetric(style.PM_TitleBarHeight)
            self.winframe_w = 3
        self.pix_item.setPos(-x -self.winframe_w, -y -self._decoration_height -self.winframe_h)
        
    def get_croped_pix(self):
        return QtGui.QPixmap.grabWidget(self.view)
    
    def exec_(self):
        ret = super(ScreenGrabDialog, self).exec_()

        self.window_to_hide.show()
        if self.restore_geom is not None:
            self.window_to_hide.setGeometry(self.restore_geom)
        
        return ret
        
class ThumbnailWidget(QtGui.QLabel):

    def __init__(self, parent):
        super(ThumbnailWidget, self).__init__(parent)
        self.path = None
        self.pix = QtGui.QPixmap()
        self.clear_pix = QtGui.QPixmap(_CLEAR_PIX)
        self.clear()
    
        self._menu = QtGui.QMenu()
        self._menu.addAction('Change...', self._on_change_menu)
        self._menu.addAction('Take a snapshot', self._on_snapshot_menu)
        
    def clear(self):
        self.setPixmap(self.clear_pix)
        
    def set_path(self, path):
        self.path = path
        if self.path and os.path.exists(self.path):
            self._load()
        else:
            self.clear()
            
    def _load(self):
        self.pix.load(self.path)
        self.setPixmap(self.pix)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self._menu.exec_(self.mapToGlobal(event.pos()))
            event.setAccepted(True)
        return super(ThumbnailWidget, self).mouseReleaseEvent(event)
    
    def _move_to_backup(self):
        bak_base = self.path+'.bak_'+str(time.time())
        bakpath = bak_base
        for i in range(10):
            if not os.path.exists(bakpath):
                break
            bakpath = bak_base+'_'+str(i)
        os.rename(self.path, bakpath)

    def _on_change_menu(self):
        if not self.path:
            QtGui.QMessageBox.warning(
                self, 'Change Thumbnail',
                'Sorry, you cannot change the thumbnail: path is not set.'
            )
            return  
        _, extension = os.path.splitext(self.path)
        path = str(QtGui.QFileDialog.getOpenFileName(
            self, 'Select thumbnail', 
            self.path, "%s Files (*%s)"%(extension, extension)
        ))
        if not path:
            return
        self.update_from_path(path)
    
    def update_from_path(self, path):
        '''
        Updates the content of the thumbnail using
        the given file.
        
        A copy of the current thumbnail file is made 
        before overwriting it.
        
        
        '''
        if not self.path:
            raise Exception('Cannot update thumnail: path not set')
        
        if not os.path.exists(path):
            raise Exception('Cannot update thumbnail from unexisting source %r.'%(path,))
                
        _, my_extension = os.path.splitext(self.path)
        _, in_extension = os.path.splitext(path)
        if my_extension != in_extension:
            raise Exception('Cannot, update thumbnail from %r: wrong extension.'%(path,))
        
        dir, base = os.path.split(self.path)
        if os.path.exists(self.path):
            self._move_to_backup()
        else:
            if not os.path.exists(dir):
                os.makedirs(dir)
        
        shutil.copy(path, self.path)
        self._load()

    def _on_snapshot_menu(self):        
        dialog = ScreenGrabDialog(self)
        result = dialog.exec_()
        if result == dialog.Accepted:
            pix = dialog.get_croped_pix()
            if pix is not None:
                self.update_from_pix(pix)
        dialog.deleteLater()

    def update_from_pix(self, pix):
        if not self.path:
            raise Exception('Cannot update thumbnail: path not set')
        
        dir, base = os.path.split(self.path)
        
        if os.path.exists(self.path):
            self._move_to_backup()
        else:
            if not os.path.exists(dir):
                os.makedirs(dir)
        
        pix.save(self.path)
        self._load()

class ThumbnailValueEditor(ThumbnailWidget, ValueEditorMixin):
    def __init__(self, parent, controller, options):
        ThumbnailWidget.__init__(self, parent)
        ValueEditorMixin.__init__(self, controller, options)
        
    def set_value(self, value):
        ValueEditorMixin.set_value(self, value)
        self.set_path(value)

    def _set_read_only(self, b):
        pass #self.setEnabled(not b)


