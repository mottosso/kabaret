
from kabaret.gui.widgets.views import QtCore

from . import icons         # install system_cmds icons

from .launch_view import LaunchToolBarView

def install(main_window_manager):
    main_window_manager.create_toolbar_view(
        u"CMDS", 'Launcher', LaunchToolBarView, QtCore.Qt.BottomToolBarArea, True, None
    )
