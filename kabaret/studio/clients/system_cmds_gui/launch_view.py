'''



'''


from kabaret.core.events.event import Event
from kabaret.core.utils import resources
from kabaret.core import syscmd
 
from kabaret.gui.widgets.views import AbstractGuiToolBarView, QtGui, QtCore


class LaunchToolBarView(AbstractGuiToolBarView):
    USE_MENU = True # set to FALSE to use toolbuttons instead
    
    def __init__(self, parent, client, app_name):
        super(LaunchToolBarView, self).__init__(parent, client, app_name)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self._grouped_cmds = []
        self._build_waiter()
        
    def on_disconnect(self):
        self._grouped_cmds = []
        self._build_waiter()
        
    def on_connect(self):
        self._build_waiter()
        self.fetch_cmds()            

    def fetch_cmds(self):
        with self.client.result_to(self._receive_cmds_ui_infos):
            self.client.apps['CMDS'].cmds.GetClientCmdInfos(self.client.station_class)

    def _receive_cmds_ui_infos(self, grouped_cmds):
        self._grouped_cmds = grouped_cmds
        self._build_ui()

    def _build_ui(self):
        self.clear()
        if self.USE_MENU:
            # We use one menubar per menu so that the toolbar can
            # be resize and horiented correctly
            for group_name, cmd_infos in self._grouped_cmds.items():
                menubar = QtGui.QMenuBar(self)
                menubar.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
                self.addWidget(menubar)
                menu = menubar.addMenu(group_name)
                for cmd in cmd_infos:
                    action = menu.addAction(
                        cmd['label'], 
                        lambda cmd_id=cmd['id']: self.trigger_cmd(cmd_id)
                    )
                    action.setToolTip('%s/%s'%(group_name, cmd['id']))
                    if cmd['icon'] is not None:
                        try:
                            icon = resources.get_icon(('system_cmds.icons',cmd['icon']))
                        except resources.NotFoundError:
                            pass
                        else:
                            action.setIcon(icon)
            return
        
        else: # if self.USE_MENU
            for group_name, cmd_infos in self._grouped_cmds.items():
                group_button = QtGui.QToolButton()
                group_button.setText(group_name)
                group_button.setPopupMode(group_button.InstantPopup)
                menu = QtGui.QMenu(group_button)
                group_button.setMenu(menu)
                try:
                    icon = resources.get_icon(('system_cmds.icons', group_name))
                except resources.NotFoundError:
                    pass
                else:
                    group_button.setIcon(icon)
                self.addWidget(group_button)
                
                for cmd in cmd_infos:
                    action = menu.addAction(
                        cmd['label'],
                        lambda cmd_id=cmd['id']: self.trigger_cmd(cmd_id)
                    )
                    action.setToolTip('%s/%s'%(group_name, cmd['id']))
                    if cmd['icon'] is not None:
                        try:
                            icon = resources.get_icon(('system_cmds',cmd['icon']))
                        except resources.NotFoundError:
                            pass
                        else:
                            action.setIcon(icon)
                    group_button.addAction(action)
                
    def _build_waiter(self):
        self.clear()
        waitter = QtGui.QLabel('Loading')
        wait_movie = QtGui.QMovie(resources.get('gui.icons', 'throbber.gif'))
        waitter.setMovie(wait_movie)
        self.addWidget(waitter)
        wait_movie.start()

    def trigger_cmd(self, cmd_id):
        with self.client.result_to(self._receive_cmd_infos_to_launch):
            self.client.apps['CMDS'].cmds.GetClientCmd(cmd_id=cmd_id, station_class=self.client.station_class)

    def _receive_cmd_infos_to_launch(self, cmd_infos):
        print 'Received CMD:', cmd_infos
        
        cmd = syscmd.SysCmd(
            executable=cmd_infos['executable'], 
            args=[], 
            env=cmd_infos['env'], 
            additional_env=cmd_infos['additional_env']
        )
        print '#-------- Got SysCmd:' 
        print cmd
        cmd.execute()

        
