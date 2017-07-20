
try:
    from . import QtCore, QtGui
except ValueError:
    # fucked relative import in non-package
    from kabaret.gui.widgets import QtCore, QtGui
    
class SweepScreen(QtGui.QWidget):
    try:
        start_sweep = QtCore.Signal()
    except AttributeError:
        start_sweep = QtCore.pyqtSignal()
    
    def __init__(self, parent, on_anim):
        super(SweepScreen, self).__init__(parent)
        parent.layout().addWidget(self)
        
        self._state_machine = QtCore.QStateMachine(self)
        
        self.hidden = QtCore.QState(self._state_machine)
        
        self.hidden_done = QtCore.QState(self._state_machine)
        self.hidden_done.entered.connect(self._on_hidden_done)
        
        self.shown = QtCore.QState(self._state_machine)

        self.hidden.addTransition(self.hidden.propertiesAssigned, self.hidden_done)
                
        tr = self.shown.addTransition(self.start_sweep, self.hidden)
        self.anim = QtCore.QPropertyAnimation(self, "geometry")
        self.anim.setDuration(250)
        self.anim.valueChanged.connect(on_anim)
        tr.addAnimation(self.anim)

        self._state_machine.setInitialState(self.shown)
        self._state_machine.start()
        
    def _on_hidden_done(self):
        self.deleteLater()

    def sweep(self):
        rect = self.geometry()
        rect.setWidth(0)
        self.hidden.assignProperty(self, 'geometry', rect)
        self.hidden_done.assignProperty(self, 'geometry', rect)
        
        self.start_sweep.emit()     
        
class SweepPanel(QtGui.QWidget):
    def __init__(self, parent, anim_duration=250):
        super(SweepPanel, self).__init__(parent)
        
        self.anim_duration = anim_duration 
        
        self.setLayout(QtGui.QHBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        
        self.screen_parent = QtGui.QFrame(self)
        self.screen_parent.setLayout(QtGui.QHBoxLayout())
        self.screen_parent.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self.screen_parent)
        
        self.current_screen = None
    
    def _on_hold_screen_anim(self, rect):
        if self.current_screen is not None:
            x = rect.x()+rect.width()
            y = rect.y()
            w = self.width()-x
            h = rect.height()
            self.current_screen.move(x, y)
            self.current_screen.resize(w, h)
            self.current_screen.show()
    
    def clear(self):
        if self.current_screen is not None:
            self.current_screen.sweep()
            self.current_screen = None
    
    def new_screen(self):
        if self.current_screen is not None:
            raise Exception('Already has a screen, please clear first')
        self.current_screen = SweepScreen(self.screen_parent, self._on_hold_screen_anim)
        self.current_screen.anim.setDuration(self.anim_duration)
        self.current_screen.resize(0,0)
        return self.current_screen


if __name__ == '__main__':
    class Tester(QtGui.QScrollArea):
        def __init__(self, parent):
            super(Tester, self).__init__(parent)
            self.sweep_panel = SweepPanel(self, anim_duration=150)
            self.setWidgetResizable(True)
            self.setWidget(self.sweep_panel)
        
            self.index = 0
            self.next()
            
        def next(self):
            self.sweep_panel.clear()
            screen = self.sweep_panel.new_screen()
            screen.setLayout(QtGui.QFormLayout())
            for i in range(10):
                self.index += 1
                screen.layout().addRow('Row #'+str(self.index), QtGui.QLineEdit(i*'blah ', screen))
        
        def clear(self):
            self.sweep_panel.clear()
            
    import sys
    app = QtGui.QApplication(sys.argv)
    f = QtGui.QFrame(None)
    f.resize(500,500)
    f.setLayout(QtGui.QVBoxLayout())
    
    bn = QtGui.QPushButton('next', f)
    f.layout().addWidget(bn)
    
    bc = QtGui.QPushButton('clear', f)
    f.layout().addWidget(bc)

    w = Tester(f)
    f.layout().addWidget(w)

    bn.clicked.connect(w.next)
    bc.clicked.connect(w.clear)

    f.show()
    app.exec_()
    