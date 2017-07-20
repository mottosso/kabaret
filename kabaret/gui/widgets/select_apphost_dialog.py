'''


'''

import fnmatch

from kabaret.gui import import_qt
QtCore, QtGui = import_qt()


class SelectAppHostDialog(QtGui.QDialog):
    def __init__(self, parent, client):
        super(SelectAppHostDialog, self).__init__(parent)
        self.client = client
        self.filter = '*'
        self._selected = None
        
        self.setWindowTitle('Connect to AppHost')
        
        self.setLayout(QtGui.QVBoxLayout())
        
        header = QtGui.QLabel('Select a Project AppHost to use:', self)
        self.layout().addWidget(header)

        lo = QtGui.QHBoxLayout()
        self.layout().addLayout(lo)
        filter_lb = QtGui.QLabel('Filter:', self)
        lo.addWidget(filter_lb)
        self.le = QtGui.QLineEdit(self.client.project_name or '', self)
        self.le.editingFinished.connect(self.set_filter)
        lo.addWidget(self.le)
        
        self.sc_cb = QtGui.QCheckBox('Match Station Class', self)
        self.sc_cb.setChecked(True)
        self.sc_cb.toggled.connect(self.match_station_class_changed)
        self.layout().addWidget(self.sc_cb)
        
        self.scan_button = QtGui.QPushButton('Scan Network', self)
        self.scan_button.clicked.connect(self.on_scan)
        self.layout().addWidget(self.scan_button)
        
        self.scan_result = QtGui.QListWidget(self)
        self.scan_result.itemDoubleClicked.connect(self.on_scan_result_double_click)
        self.layout().addWidget(self.scan_result)
        
        button_layout = QtGui.QHBoxLayout()
        self.layout().addLayout(button_layout)
        
#        b = QtGui.QPushButton('Ok', self)
#        b.clicked.connect(self.accept)
#        button_layout.addWidget(b)
    
        b = QtGui.QPushButton('Cancel', self)
        b.clicked.connect(self.reject)
        button_layout.addWidget(b)
    
    def showEvent(self, e):
        super(SelectAppHostDialog, self).showEvent(e)
        self.on_scan()
        
    def set_filter(self):
        text = self.le.text()
        if '*' not in text:
            text = '*%s*'%(text,)
        self.filter = text
        self.on_scan()
    
    def match_station_class_changed(self, b):
        self.on_scan()
        
    def on_scan(self):
        self.scan_result.clear()
        apphost_infos = self.client.get_available_apphost_infos(match_station_class=self.sc_cb.isChecked())
        for info in apphost_infos:
            label = info['project_name'] +' on %s (%s) by %s'%(info['host'], info['station_class'], info['user'])
            if self.filter and not fnmatch.fnmatch(label, self.filter):
                continue
            item = QtGui.QListWidgetItem(label, self.scan_result)
            item._apphost_info = info
        self.scan_button.setText('Re-Scan')
        
    def on_scan_result_double_click(self, item):
        self._selected = item._apphost_info
        self.accept()
        
    def get_connection_infos(self):
        return self._selected
