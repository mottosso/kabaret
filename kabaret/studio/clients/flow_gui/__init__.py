
from kabaret.gui.widgets.views import QtCore

from . import icons         # install flow icons
from .icons import nodes    # install flow node icons

from .nodes_view import NodesView
from .params_view import ParamsView
from .tree_view import TreeView
from .versions_view import VersionsView
from .search_view import SearchView
# not yet ready: from .user_view import UserView

def install(main_window_manager):
    show_tree = True
    show_params = True
    show_search = True
    show_versions = True

    nodes = main_window_manager.create_docked_view(
        "FLOW", 'Nodes', NodesView, QtCore.Qt.LeftDockWidgetArea, False, None
    )
    params = main_window_manager.create_docked_view(
        "FLOW", 'Params', ParamsView, QtCore.Qt.RightDockWidgetArea, show_params, None
    )
    versions = main_window_manager.create_docked_view(
        "VERSIONS", 'Versions', VersionsView, QtCore.Qt.RightDockWidgetArea, show_versions, None
    )
    tree = main_window_manager.create_docked_view(
        "FLOW", 'Tree', TreeView, QtCore.Qt.LeftDockWidgetArea, show_tree, None
    )
    search = main_window_manager.create_docked_view(
        "FLOW", 'Node Search', SearchView, QtCore.Qt.LeftDockWidgetArea, show_search, None
    )
# not yet ready:
#    project = main_window_manager.create_docked_view(
#        "FLOW", 'Project View', UserView, QtCore.Qt.LeftDockWidgetArea, False, None
#    )
    
    main_window_manager.tabify_docked_view(versions, params)
    main_window_manager.tabify_docked_view(tree, search, nodes)#, project)
    