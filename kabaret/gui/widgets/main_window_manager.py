

import contextlib

from kabaret.core.events.event import Event

from kabaret.gui import import_qt
QtCore, QtGui = import_qt()

from kabaret.core.utils import resources
import kabaret.gui.icons #@UnusedImport installs gui icons 
import kabaret.gui.styles

from . import select_apphost_dialog


class MainWindowManager(object):
    class InstallType:
        Standalone = 1
        Embedded = 2
        Parented = 3
        
    def __init__(self, main_window, client):
        super(MainWindowManager, self).__init__()
        self._main_window = main_window
        self.client = client
        self._installed = None
        
        self.USE_VIEW_MENU = False
        self.SHOW_VIEW_TOOLBAR = True
        self.ONE_TOOBAR_PER_APP = True
        self.TITLE_HAS_APP_NAME = False
        self.USE_PROGRESS_BAR = False
        
    def install_standalone(self):
        '''
        This will install everything in the managed
        main_window.
        You need to call this when you build your own
        main window and want the build the kabaret GUI.
        '''

        if self._installed:
            raise Exception('The main window is already pimped.')
        self._installed = self.InstallType.Standalone
        
        kabaret.gui.styles.apply_default_style()

        self._main_window.setDockNestingEnabled(False)
        self._main_window.setDockOptions(
            self._main_window.AnimatedDocks
            | self._main_window.AllowNestedDocks
            | self._main_window.AllowTabbedDocks
        )

        self.status_bar = None
        self._install_status_bar() 
        
        self._progress_bar = None
        if self.USE_PROGRESS_BAR:
            self._install_progress_bar()

        self._load_label = None
        self._install_load_label()
        
        self._throbber_label = None
        self._connection_menu = None
        self._install_throbber()
        
        self.menus = {}
        self.menu_bar = None
        self._install_menu_bar()

        if self.USE_VIEW_MENU:
            self.view_menu = None
            self._install_view_menu('Views')
        
        self._view_toolbars = {}
        # install the Kabaret view toolbar so that we are sure it is hidden:
        self._install_view_toolbar(u"\u20AD", u"\u20AD", shown=False)
            
        self.client_ticker = QtCore.QTimer(self._main_window)
        self.client_ticker.timeout.connect(self.client_tick)
        self.client_ticker.start(500)

        sides = [
            QtCore.Qt.LeftDockWidgetArea,
            QtCore.Qt.RightDockWidgetArea,
            QtCore.Qt.TopDockWidgetArea,
            QtCore.Qt.BottomDockWidgetArea,
        ]
        for side in sides:
            self._main_window.setTabPosition(side, QtGui.QTabWidget.North)

        # Monkey path the closeEvent handler:
        mw_class = self._main_window.__class__
        def closeEvent(event, manager=self):
            manager.on_mainwindow_close_event(event)
            return super(mw_class, manager._main_window).closeEvent(event)
        self._main_window.closeEvent = closeEvent

    def install_embedded(self):
        '''
        This will install missing features in the managed
        main_window.
        You need to call this when you have a reference to
        the application main_window and want the embed the 
        kabaret GUI.
        '''
        if self._installed:
            raise Exception('The main window is already pimped.')
        self._installed = self.InstallType.Embedded

        self.status_bar = self._find_status_bar()
        if self.status_bar is None:
            self._install_status_bar()
            
        self._progress_bar = None
        if self.USE_PROGRESS_BAR:
            self._install_progress_bar()

        self._load_label = None
        self._install_load_label()
        
        self._throbber_label = None
        self._connection_menu = None
        self._install_throbber()
        
        self.menus = {}
        self.menu_bar = None
        self._install_menu_bar()

        if self.USE_VIEW_MENU:
            self.view_menu = None
            self._install_view_menu('Kabaret Views')
        
        self._view_toolbars = {}
        # install the Kabaret view toolbar so that we are sure it is hidden:
        self._install_view_toolbar(u"\u20AD", u"\u20AD", shown=False)
            
        self.client_ticker = QtCore.QTimer(self._main_window)
        self.client_ticker.timeout.connect(self.client_tick)
        self.client_ticker.start(500)

        # Monkey path the closeEvent handler:
        mw_class = self._main_window.__class__
        def closeEvent(event, manager=self):
            manager.on_mainwindow_close_event(event)
            return super(mw_class, manager._main_window).closeEvent(event)
        self._main_window.closeEvent = closeEvent

    def install_parented(self):
        '''
        This will create a main_window under parent_widget 
        and install kabaret gui in it.
        
        You need to use this when you have a reference to
        a widget instead of a main_window and want to embed the 
        kabaret GUI in this widget (This manager must have 
        None used as 'main_window' in its constructor)
        
        If the parent_widget does not have a layout to receive
        the new widgets, a default one is created.
        
        '''
        self.install_standalone()
        self.status_bar.setSizeGripEnabled(False)
        self._installed = self.InstallType.Parented
        
    def on_mainwindow_close_event(self, event):
        print 'CLOSING MAIN WINDOW!!!!'
        self.disconnect()
        print 'disconnected.'

    def _find_status_bar(self):
        '''
        Returns the widget to use as status bar when
        embedding the Kabaret GUI
        '''
        status_bar = self._main_window.findChild(QtGui.QStatusBar)
        return status_bar
    
    def _install_status_bar(self):
        self.status_bar = self._main_window.statusBar() # this creates it if needed :/
        self.status_bar.showMessage("Initializing", 1000)
#        status_bar.setSizeGripEnabled(False)

    def _install_progress_bar(self):
        self._progress_bar = QtGui.QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.reset()
        self.status_bar.addPermanentWidget(self._progress_bar)

    def _install_load_label(self):
        self._load_label = QtGui.QLabel(self._main_window)
        self.status_bar.addPermanentWidget(self._load_label)
        
    def _install_throbber(self): 
        self._throbber_label = QtGui.QLabel(self._main_window)
        self._throbber_label.setStyleSheet('border: none;')
        self._throbber_label.customContextMenuRequested.connect(
            self._on_connection_menu_request
        )
        self._throbber_label.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.throbber_movie = QtGui.QMovie(resources.get('gui.icons', 'throbber.gif'))
        self._throbber_label.setMovie(self.throbber_movie)
        self._throbber_label.resize(16,16)
        self.status_bar.addPermanentWidget(self._throbber_label)

    def _install_menu_bar(self):
        mb = self._main_window.menuBar()
        if not mb:
            mb = QtGui.QMenuBar(None)
            self._main_window.setMenuBar(mb)
        self.menu_bar = mb

    def _install_view_menu(self, title):
        self.view_menu = self.menu_bar.addMenu(title)
        self.view_app_menu = {}

    def _install_view_toolbar(self, app_name, title, shown=None, add_break=False, area=QtCore.Qt.TopToolBarArea):
        '''
        Creates and install a new toolbar for the given app with the given title.
        
        If shown is None, the default is used (self.SHOW_VIEW_TOOLBAR). In other case it
        must be a boolean value that will drive the visibility of the new toolbar.
        
        If add_break is True, a break is added before the new toolbar.
        
        The area argument must be a QtCore.Qt.ToolBarArea
        
        '''
        tb = QtGui.QToolBar(title, self._main_window)
        self._view_toolbars[app_name] = tb
#        tb.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        if add_break:
            self._main_window.addToolBarBreak(area)
        self._main_window.addToolBar(area, tb)
        if shown is None:
            shown = self.SHOW_VIEW_TOOLBAR
        if not shown:
            tb.hide()
        return tb
    
    def send_message(self, msg, path=[]):
        self.client.send_event(
            Event('GUI', path, Event.TYPE.MESSAGE, msg)
        )

    def show_progress(self, nb_step, curr_step, msg):
        if not self.USE_PROGRESS_BAR:
            print 'PROGRESS: %s (%s/%s)'%(msg, curr_step, nb_step)
            return
        self.status_bar.showMessage(msg)
        self._progress_bar.setMaximum(nb_step)
        self._progress_bar.setValue(curr_step)
    
    def clear_progress(self, msg, delay=500):
        if not self.USE_PROGRESS_BAR:
            print 'PROGRESS: %s (Done)'%(msg,)
        else:
            self._progress_bar.setMaximum(100)
            self._progress_bar.reset()
        self.status_bar.showMessage(msg, delay)

    @contextlib.contextmanager
    def wait_cursor(self):
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        try:
            yield
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def get_view_toobar(self, app_name, add_break=False, area=QtCore.Qt.TopToolBarArea):
        '''
        Returns the toolbar containing buttons for the view
        of the given app.
        If it does not exist yet, the toolbar is created and installed in
        the given area with an optional break.
        '''
        title = app_name.title()+' views'
        if not self.ONE_TOOBAR_PER_APP:
            app_name = 'Kabaret View'
        try:
            return self._view_toolbars[app_name]
        except KeyError:
            return self._install_view_toolbar(app_name, title, self.SHOW_VIEW_TOOLBAR, add_break, area)

    def create_toolbar_view(
            self, app_name, title, view_class, area, visible,
            view_set=[]
        ):
        if self.TITLE_HAS_APP_NAME:
            full_title = '%s %s'%(app_name, title)
        else:
            full_title = title

        view = view_class(self._main_window, self.client, app_name)
        self.client.register_view(view)
        view.name = full_title
        view.setWindowTitle(full_title)
        
        def on_visibility_changed(visible, view=view):
            with self.wait_cursor():
                view.on_view_toggled(visible)
        view.visibilityChanged.connect(on_visibility_changed)
        self._main_window.addToolBar(area, view)
        if not visible:
            view.hide()
        view._is_active = visible 
        return view

    def create_docked_view(
            self, app_name, title, view_class, area, visible, icon=None, allowed_areas=None,
            add_to_view_toolbar=True, view_sets=[]
        ):
        if self.TITLE_HAS_APP_NAME:
            full_title = '%s %s'%(app_name, title)
        else:
            full_title = title
        if icon is not None:
            icon = resources.get_icon(icon, self._main_window)
        
        if self.USE_VIEW_MENU:
            view_app_menu = self.view_app_menu.get(app_name)
            if view_app_menu is None:
                view_app_menu = self.view_menu.addMenu(app_name)
                if icon is not None:
                    view_app_menu.setIcon(icon)
                self.view_app_menu[app_name] = view_app_menu

        d = QtGui.QDockWidget(full_title, self._main_window)
        
        if allowed_areas is not None:
            d.setAllowedAreas(
                QtCore.Qt.TopDockWidgetArea
                | QtCore.Qt.BottomDockWidgetArea
            )
        view = view_class(self._main_window, self.client, app_name)
        if self._installed != self.InstallType.Standalone:
            kabaret.gui.styles.apply_default_style(view)
        
        self.client.register_view(view)
        view.name = full_title
        d.setWidget(view)
        def on_visibility_changed(visible, view=view):
            with self.wait_cursor():
                view.on_view_toggled(visible)
        d.connect(d, QtCore.SIGNAL('visibilityChanged(bool)'), on_visibility_changed)
        self._main_window.addDockWidget(area, d)
        toggle_action = d.toggleViewAction()
        if icon is not None:
            toggle_action.setIcon(icon)
        toggle_action.setStatusTip('Show/Hide %s'%full_title)
        if self.USE_VIEW_MENU:
            view_app_menu.addAction(toggle_action)
        if add_to_view_toolbar:
            tb = self.get_view_toobar(app_name)
            tb.addAction(toggle_action)
        if not visible:
            d.hide()
        view._is_active = visible 
        return d

    def tabify_docked_view(self, docked_view, *other_docked_views):
        for dv in other_docked_views:
            self._main_window.tabifyDockWidget(docked_view, dv)
        
    def client_tick(self):
        status = self.client.tick()
        self._load_label.setText('%s - %s'%(self.client.project_name, status))            
        self.throbber_movie.jumpToNextFrame()
    
    def _on_connection_menu_request(self, pos):
        if self._connection_menu is None:
            self._connection_menu = QtGui.QMenu(self._main_window)
            self._connection_menu.addAction('Ping AppHost', self.ping_apphost)
            self._connection_menu.addAction('Ping Project', self.ping_project)
            self._connection_menu.addSeparator()
            self._connection_menu.addAction('Connect...', self.show_connect_dialog)
            self._connection_menu.addSeparator()
            self._connection_menu.addAction('Reconnect', self.reconnect)
            self._connection_menu.addAction('Disconnect', self.disconnect)
            self._connection_menu.addAction('Kill AppHost', self.kill_apphost)
        self._connection_menu.exec_(QtGui.QCursor.pos())

    def update_window_title(self):
        project_name = self.client.project_name
        if project_name is None:
            self._main_window.setWindowTitle('Not Connected - '+str(QtGui.qApp.applicationName()))
        else:
            self._main_window.setWindowTitle('%s - %s'%(project_name, QtGui.qApp.applicationName()))

    def ping_apphost(self):
        pong = self.client.apphost.ping()
        self.send_message(pong, ['ping_apphost'])
        
    def ping_project(self):
        pong = self.client.apphost.ping_project()
        self.send_message(pong, ['ping_project'])
        
    def kill_apphost(self):
        self.client.kill_apphost()
        self.send_message('Done', ['kill_apphost'])
        
    def disconnect(self):
        pong = self.client.disconnect()
        self.send_message('Done', ['disconnect', pong])
        self.update_window_title()

    def reconnect(self):
        if not self.client.project_name:
            return self.show_connect_dialog()
        pong = self.client.connect()
        self.send_message('Done', ['reconnect', pong])
        self.update_window_title()

    def show_connect_dialog(self):
        dialog = select_apphost_dialog.SelectAppHostDialog(
            self._main_window, self.client
        )
        ret = dialog.exec_()
        connection_kwargs = dialog.get_connection_infos()
        if not connection_kwargs:
            return
        project_name = connection_kwargs.get('project_name')
        
        if ret != dialog.Accepted or not project_name:
            self.send_message('Cancel', ['connect'])
            if self.client.connected():
                self.update_window_title()
            else:
                self.client.project_name = None
                self.update_window_title()
            return
        
        #print '>>>>>>>>>', connection_kwargs
        self.client.connect(**connection_kwargs)
        
        self.send_message('Done', ['connect', project_name])
        self.update_window_title()
        
        dialog.deleteLater()
        
    