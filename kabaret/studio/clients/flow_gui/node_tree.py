'''


'''

from kabaret.core.utils import resources
from kabaret.core.utils import get_user_name

from kabaret.gui.styles import get_style_value
from kabaret.gui.models import tree
from kabaret.gui.widgets import QtGui, QtCore

from .proc_exec_panel import prepare_proc_execution

class _FlowItem(tree.TreeItem):
    def __init__(self, model, item_id, parent, node_type, icon_name, color):
        self._node_type = node_type
        self._icon_name = icon_name
        self._connected = True
        super(_FlowItem, self).__init__(
            model=model, item_id=item_id, parent=parent, 
            color=color
        )
        self._procs = None
        self._triggers_infos = None
        self._choices_for_infos = None

    def set_disconnected(self):
        self._connected = False

    def hasChildren(self):
        if not self._connected:
            return False
        return super(_FlowItem, self).hasChildren()

    def mime_data(self, column):
        ret = {
            'text/plain': self.label(column),
        }
        if column == 0:
            ret['kabaret/ids'] = '/'.join(self.node_id())
        return ret
        
    def columnCount(self):
        return len(self.model()._column_labels)
    
    def label(self, column):
        if column == 0:
            return self.display_name()
        elif column == 1:
            return self.display_node_type()
    
    def pix_ref(self, column):
        if column == 0 and self._icon_name:
            return 'flow.icons.nodes', self._icon_name
        return None
    
    def display_name(self):
        return self.item_id()
    
    def display_node_type(self):
        return self._node_type

    def node_id(self):
        ret = ()
        if self._parent:
            ret = self._parent.node_id()
        return ret+(self.item_id(),)

    def _instantiate_child(self, item_id, node_type, icon_name):
        return NodeItem(self._model, item_id, self, node_type, icon_name)
    
    def _create_child(self, item_id, node_type, icon_name):
        index = self._model.createIndex(self.row(), 0, self)
        first = len(self._children)
        
        self._model.beginInsertRows(index, first, first+1)
        child = self._instantiate_child(item_id, node_type, icon_name)
        self.appendChild(child)
        self._model.endInsertRows()
    
    def _instantiate_proc(self, item_id, node_type, icon_name):
        return ProcItem(self._model, item_id, self, node_type, icon_name)
    
    def _create_proc(self, item_id, node_type, icon_name):
        index = self._model.createIndex(self.row(), 0, self)
        first = len(self._children)
        
        self._model.beginInsertRows(index, first, first+1)
        child = self._instantiate_proc(item_id, node_type, icon_name)
        self.appendChild(child)
        self._model.endInsertRows()
        
    def get_proc_infos(self):
        if self._procs is None:
            procs_infos = self._model.client.apps.FLOW.cmds.GetTypeProcUiInfos(
                self.node_id()
            )
            self._procs = procs_infos
        return self._procs
    
    def get_menu_param_infos(self):
        if self._triggers_infos is None:
            grouped_params_infos = self._model.client.apps.FLOW.cmds.GetTypeParamUiInfos(
                self.node_id()
            )
            self._triggers_infos = [
                param_infos
                for _, param_infos_list in grouped_params_infos
                for param_infos in param_infos_list
                if param_infos['param_type'] == 'TriggerParam'
            ]
            self._choices_for_infos = [
                param_infos
                for _, param_infos_list in grouped_params_infos
                for param_infos in param_infos_list
                if param_infos['editor'] == 'choices_for'
            ]
        return self._triggers_infos, self._choices_for_infos

    def get_param_infos(self, param_name):
        return self._model.client.apps.FLOW.cmds.GetParamUiInfos(
                self.node_id(), param_name
            )[0][1][0]
    
    def get_menu_actions(self, tree_panel):
        '''
        Must return a list of (pix_ref, name, callback).
        If name is None, a separator is inserted instead of
        an action.
        '''
        return [
            (('gui.icons', 'refresh'), 'Refresh', self.refresh),
            (('gui.icons', 'bookmark'), 'Add Bookmark', lambda nid=self.node_id():tree_panel.add_bookmark(nid))
        ]
    
    def apply_choice_for_selection(self, param_infos, value):
        target_param_name = param_infos.get('editor_options', {}).get('target_param')
        if target_param_name is None:
            raise Exception(
                'Could not find the target param of the %r choices_for param'%(
                    param_infos['id'],
                )
            )
        target_param_id = param_infos['id'][:-1]+('.'+target_param_name,)
        
        #TODO: debug the client.no_result() context (actually, the pyroOneway that blocks :/)
        with self._model.client.result_to(lambda result: None):
            self._model.client.apps.FLOW.cmds.SetParamValue(
                target_param_id,
                value
            )

    def trigger(self, param_name):
        with self._model.client.result_to(lambda result: None):
            self._model.client.apps.FLOW.cmds.SetParamValue(
                self.node_id()+('.'+param_name,), None
            )
            
    def refresh(self):
        if not self._connected:
            return
        self._model.client.apps.FLOW.cmds.DropNode(self.node_id())
        self._reset()
        self.load_children()
    
class NodeItem(_FlowItem):
    def __init__(self, model, item_id, parent, node_type, icon_name, color=None):
        color = color or QtGui.QColor(*get_style_value('node_colors', 'CHILD', (200,200,200)))
        super(NodeItem, self).__init__(
            model, item_id, parent, 
            node_type=node_type, icon_name=icon_name, color=color
        )

    def find(self, sub_id_path):
        if not sub_id_path:
            return True, self
        
        if ':' in sub_id_path[0]:
            cid = sub_id_path[0].split(':', 1)[0]
            sub_id_path = [cid]+list(sub_id_path)
        return super(NodeItem, self).find(sub_id_path)
        
    def _create_many_relation_child(self, relation_name, related_type, related_icon):
        index = self._model.createIndex(self.row(), 0, self)
        first = len(self._children)
        
        self._model.beginInsertRows(index, first, first+1)
        relation_item = ManyRelationItem(self._model, relation_name, self, related_type, related_icon)
        self.appendChild(relation_item)
        self._model.endInsertRows()
        return relation_item

    def _create_one_relation_child(self, relation_name, related_type, related_icon):
        index = self._model.createIndex(self.row(), 0, self)
        first = len(self._children)
        
        self._model.beginInsertRows(index, first, first+1)
        relation_item = OneRelationItem(self._model, relation_name, self, related_type, related_icon)
        self.appendChild(relation_item)
        self._model.endInsertRows()
        return relation_item

    def load_children(self, blocking=False):
        if not self._connected:
            return
        
        if not super(NodeItem, self).load_children():
            return

        if blocking:
            relations = self._model.client.apps.FLOW.cmds.GetNodeRelations(
                self.node_id(), 
                child_nodes=self.model().children_shown(self), 
                proc_nodes=self.model()._show_procs,
            )
            self._to_load(relations)
        else:
            with self._model.client.result_to(self._to_load):
                self._model.client.apps.FLOW.cmds.GetNodeRelations(
                    self.node_id(), 
                    child_nodes=self.model().children_shown(self),
                    proc_nodes=self.model()._show_procs,                    
                )
    
    def _to_load(self, relations):        
        for relation_name, related_infos in relations.get('Many', []):
            self._create_many_relation_child(relation_name, related_infos['type'], related_infos['icon'])
            
        for relation_name, related_infos in relations.get('One', []):
            self._create_one_relation_child(relation_name, related_infos['type'], related_infos['icon'])
        
        show_protected = self.model()._show_protected_children
        for relation_name, related_infos in relations.get('Child', []):
            if not show_protected and relation_name.startswith('_'):
                continue
            self._create_child(relation_name, related_infos['type'], related_infos['icon'])
        
        for relation_name, related_infos in relations.get('Proc', []):
            self._create_proc(relation_name, related_infos['type'], related_infos['icon'])
            
        self.children_loaded()


class RelatedNodeItem(NodeItem):
    def __init__(self, model, item_id, parent, node_type, icon_name):
        self._display_name = item_id.split(':', 1)[1]
        super(RelatedNodeItem, self).__init__(model, item_id, parent, node_type, icon_name)
        
    def display_name(self):
        return self._display_name
    
class OneRelationItem(NodeItem):
    def __init__(self, model, relation_name, parent, related_type, icon_name):
        super(OneRelationItem, self).__init__(
            model, relation_name, parent, related_type, icon_name,
            color=QtGui.QColor(*get_style_value('node_colors', 'ONE', (128,128,200)))
        )

    def display_node_type(self):
        return 'One '+self._node_type

    def pix_ref(self, column):
        return None
    
class ManyRelationItem(_FlowItem):
    def __init__(self, model, relation_name, parent, related_type, icon_name):
        super(ManyRelationItem, self).__init__(
            model, relation_name, parent,
            node_type=related_type, icon_name=icon_name,
            color=QtGui.QColor(*get_style_value('node_colors', 'MANY', (128,128,200)))
        )

    def display_node_type(self):
        return 'Many: '+self._node_type

    def pix_ref(self, column):
        return None
    
    def node_id(self):
        return self._parent.node_id()

    def _instantiate_child(self, item_id, node_type, icon_name):
        return RelatedNodeItem(self._model, item_id, self, self._node_type, icon_name)

    def load_children(self, blocking=False):
        if not self._connected:
            return
        
        if not super(ManyRelationItem, self).load_children():
            return
        
        if blocking:
            case_ids = self._model.client.apps.FLOW.cmds.GetCaseIds(
                self.node_id(), self.item_id()
            )
            self._to_load(case_ids)
        else:
            with self._model.client.result_to(self._to_load):
                self._model.client.apps.FLOW.cmds.GetCaseIds(self.node_id(), self.item_id())
            
    def _to_load(self, case_ids):
        for case_id in case_ids:
            self._create_child('%s:%s'%(self._item_id, case_id), self._node_type+':<TYPE>', self._icon_name)
        
        self.children_loaded()

class ProcItem(NodeItem):
    def __init__(self, model, item_id, parent, node_type, icon_name):
        super(ProcItem, self).__init__(
            model, item_id, parent, node_type, icon_name,
            color=QtGui.QColor(*get_style_value('node_colors', 'PROC', (200,128,200)))
        )

    def get_menu_actions(self, tree_panel):
        actions = super(ProcItem, self).get_menu_actions(tree_panel)
        if not self._parent:
            return actions
        actions += [
            (self.pix_ref(0), 'Execute', lambda: tree_panel.run_proc(self.node_id()))
        ]
        return actions 
    
class RootNodeItem(NodeItem):
    def __init__(self, model, node_id):
        super(RootNodeItem, self).__init__(
            model=model, item_id='/'.join(node_id), parent=None, node_type='~Node', icon_name=None
        )
        self._node_id = node_id
    
    def node_id(self):
        return self._node_id

    def display_name(self):
        if not self._connected:
            return "Not Connected..."
        return self.item_id()
    
    def display_node_type(self):
        if not self._connected:
            return "Not Connected..."
        return self._node_type

    def find(self, sub_id_path):
        # ensure it is under this root:        
        for mine, his in zip(self.node_id(), sub_id_path):
            if mine != his:
                return False, self
        
        # get the relative path:
        sub_id_path = sub_id_path[len(self.node_id()):]
        
        # use default find with the relative path
        return super(RootNodeItem, self).find(sub_id_path)

class FlowModel(tree.TreeModel):
    def __init__(self, parent, client, root_id=None):
        super(FlowModel, self).__init__(parent, column_labels=['Name'])
        self.client = client
        self._show_children = True
        self._show_procs = True
        self._show_protected_children = False
        self._show_node_type = False
        
        self.current_root_id = None
        self.setSupportedDragActions(
            QtCore.Qt.LinkAction
        )
        
        #self.change_root_id(root_id)
        self.set_root(
            RootNodeItem(self, 'Not Connected')
        )
        self._root._connected = False
        
    def change_root_id(self, root_id=None):
        self.current_root_id = root_id
        root_id = root_id or self.client.apps.FLOW.cmds.GetRootId()
        self.set_root(
            RootNodeItem(self, root_id)
        )
        self.reset()

    def toggle_node_type(self):
        self._show_node_type = not self._show_node_type
        if self._show_node_type:
            self._column_labels = ['Name', 'Type']
        else:
            self._column_labels = ['Name']
        self.reset()
    
    def toggle_protected_child_nodes(self):
        self._show_protected_children = not self._show_protected_children
        self.reset()
        
    def toggle_child_nodes(self):
        self._show_children = not self._show_children
        self.reset()
    
    def children_shown(self, item):
        '''
        Returns True if the Child nodes of the given item
        should be loaded.
        '''
        return self._show_children or item == self._root or item.parent() == self._root
    
    def toggle_proc_nodes(self):
        self._show_procs = not self._show_procs
        self.reset()

    def set_connected(self):
        self.change_root_id(self.current_root_id) # will call reset
        
    def set_disconnected(self):
        self.root().set_disconnected()
        self.reset()
        
class FlowItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, tree_panel):
        super(FlowItemDelegate, self).__init__(tree_panel)
        self.tree_panel = tree_panel
        
    def editorEvent(self, event, model, option, index):
        if (
            event.type() == event.MouseButtonPress
            and
            event.button() == QtCore.Qt.RightButton
        ):
            self.tree_panel.show_item_menu(index)
            return True
        return False

class TreeViewMenuBar(QtGui.QMenuBar):
    def __init__(self, tree_panel, root_names=[], bookmark_names=[]):
        super(TreeViewMenuBar, self).__init__(tree_panel)
        
        #-- ROOT
        self.root_menu = self.addMenu('Root')
        self.set_root_names(tree_panel, root_names)
        
        #-- BOOKMARKS
        self.bookmark_menu = self.addMenu('Bookmarks')
        self.set_bookmark_names(tree_panel, bookmark_names)
        
        #-- OPTIONS
        options_menu = self.addMenu('Options')
        
        tree_panel.toggle_type_col_action = options_menu.addAction(
            'Show Nodes Type', tree_panel.toggle_node_type
        )
        tree_panel.toggle_type_col_action.setCheckable(True)

        toggle_child_nodes_action = options_menu.addAction(
            'Show Child Nodes', tree_panel.toggle_child_nodes
        )
        toggle_child_nodes_action.setCheckable(True)
        toggle_child_nodes_action.setChecked(True)

        toggle_proc_nodes_action = options_menu.addAction(
            'Show Proc Nodes', tree_panel.toggle_proc_nodes
        )
        toggle_proc_nodes_action.setCheckable(True)
        toggle_proc_nodes_action.setChecked(True)

        toggle_protected_child_nodes_action = options_menu.addAction(
            'Show Protected Child Nodes', tree_panel.toggle_protected_child_nodes
        )
        toggle_protected_child_nodes_action.setCheckable(True)
        toggle_protected_child_nodes_action.setChecked(False)

        options_menu.addSeparator()
        
        action = options_menu.addAction(
            'Alternating Row Colors', tree_panel.toogle_alternating_row_colors
        )
        action.setCheckable(True)
        action.setChecked(False)
        
    def set_root_names(self, tree_panel, root_names=[]):
        self.root_menu.clear()
            
        self.root_menu.addAction('Project', tree_panel.reset_root)

        self.root_menu.addSeparator()
        for root_name in root_names:
            self.root_menu.addAction(
                root_name, lambda root_name=root_name: tree_panel.set_named_root(root_name)
            )
            
        self.root_menu.addSeparator()
        self.root_menu.addAction('Up', tree_panel.set_root_to_root_parent)
        self.root_menu.addAction('Use current path', tree_panel.set_root_to_current)
    
    def set_bookmark_names(self, tree_panel, live_bookmark_names=[], bookmark_names=[]):
        self.bookmark_menu.clear()
        
        self.bookmark_menu.addAction(
            'Add Current Node', tree_panel.add_current_to_bookmarks
        )
        
        if live_bookmark_names:
            self.bookmark_menu.addSeparator()
            for name in live_bookmark_names:
                self.bookmark_menu.addAction(
                    name, lambda name=name: tree_panel.goto_live_bookmark(name)
                )
        
        if not bookmark_names:
            return 
        
        self.bookmark_menu.addSeparator()
        for name in bookmark_names:
            self.bookmark_menu.addAction(
                name, lambda name=name: tree_panel.goto_bookmark(name)
            )
        
        self.bookmark_menu.addSeparator()
        del_menu = self.bookmark_menu.addMenu('Delete Bookmark')
        for name in bookmark_names:
            del_menu.addAction(
                name, lambda name=name: tree_panel.delete_bookmark(name)
            )
        
class NodeTreePanel(QtGui.QWidget):
    def __init__(self, parent, client, extra_root_names={}):
        super(NodeTreePanel, self).__init__(parent)
        
        self.client = client
        self.current_node_id = None

        self._item_menu_filler_func = None
        self._on_current_changed_func = None
        self._extra_root_names = extra_root_names
        self._root_names = {}

        self._bookmarks = {}        # user bookmarks
        self._live_bookmarks = {}   # dynamic/programatic/non-persistent bookmarks
        
        self.model = FlowModel(parent=self, client=self.client)

        # Widgets
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        # MENUS
        self.menu_bar = TreeViewMenuBar(self)
        self.layout().addWidget(self.menu_bar)

        # TREE
        self.tree = QtGui.QTreeView(self)
        self.tree.setAlternatingRowColors(False)
        self.tree.setDragEnabled(True)
        self.tree.setItemDelegate(FlowItemDelegate(self))
        self.tree.setRootIsDecorated(True)
        self.layout().addWidget(self.tree)

        self.tree.setModel(self.model)
        
        self.sel_model = QtGui.QItemSelectionModel(self.model)
        self.sel_model.currentChanged.connect(self._on_current_changed)
        self.tree.setSelectionModel(self.sel_model)

    def set_connected(self):
        '''
        User must call this when the client gets connected to
        an AppHost.
        '''
        self.model.set_connected()

        self._root_names = {}

        # find root names
        root_id = self.model.root().node_id()
        for node_id in self.client.apps.FLOW.cmds.GetRootChildren():
            root_name = node_id[-1]
            self.add_root_name(root_name, node_id)

        for name, node_id in self._extra_root_names.items():
            full_id = root_id + node_id
            self.add_root_name(name, full_id)

        self.menu_bar.set_root_names(self, sorted(self._root_names.keys()))
        
        # find bookmarks
        self._bookmarks = self.client.apps.USERS.cmds.GetUserData(
            login=get_user_name(),
            data_id='flow_bookmarked_uid'
        )
        self.menu_bar.set_bookmark_names(
            self, sorted(self._live_bookmarks.keys()), sorted(self._bookmarks.keys())
        )
        
    def set_disconnected(self):
        '''
        User must call this when the client gets disconnected from
        the AppHost
        '''
        self.model.set_disconnected()
        
        self._root_names = {}
        self.menu_bar.set_root_names(self, sorted(self._root_names.keys()))

    def toogle_alternating_row_colors(self):
        self.tree.setAlternatingRowColors(not self.tree.alternatingRowColors())
        
    def set_item_menu_filler(self, func):
        self._item_menu_filler_func = func
        
    def set_on_current_node_id_change_func(self, func):
        self._on_current_changed_func = func

    def ensure_root_name(self, name, node_id):
        update_menu = name not in self._root_names
        self.add_root_name(name, node_id)
        if update_menu:
            self.menu_bar.set_root_names(self, sorted(self._root_names.keys()))

    def add_root_name(self, name, node_id):
        self._root_names[name] = node_id
    
    def set_named_root(self, name):
        self.set_root_to_id(self._root_names.get(name, None))
        
    def reset_root(self):
        self.set_root_to_id(None)
    
    def set_root_to_root_parent(self):
        if self.model.current_root_id:
            root_id = self.model.current_root_id[:-1]
            if root_id:
                self.set_root_to_id(root_id)
    
    def set_root_to_current(self):
        self.ensure_root_name('/'.join(self.current_node_id), self.current_node_id)
        self.set_root_to_id(self.current_node_id)
    
    def set_root_to_id(self, node_id):
        self.model.change_root_id(node_id)
        self.find_and_set_current(self.current_node_id, force=True)
        
    def toggle_node_type(self):
        self.model.toggle_node_type()
        self.find_and_set_current(self.current_node_id, force=True)
        
    def toggle_protected_child_nodes(self):
        self.model.toggle_protected_child_nodes()
        self.find_and_set_current(self.current_node_id, force=True)
        
    def toggle_child_nodes(self):
        self.model.toggle_child_nodes()
        self.find_and_set_current(self.current_node_id, force=True)

    def toggle_proc_nodes(self):
        self.model.toggle_proc_nodes()
        self.find_and_set_current(self.current_node_id, force=True)

    def add_current_to_bookmarks(self):
        self.add_bookmark(self.current_node_id)

    def ensure_live_bookmark(self, name, node_id):
        self._live_bookmarks[name] = node_id
        self.menu_bar.set_bookmark_names(
            self, sorted(self._live_bookmarks.keys()), sorted(self._bookmarks.keys())
        )

    def add_bookmark(self, node_uid):
        name = '/'.join(node_uid)
        
        # store the new bookmark in user data
        with self.client.result_to(lambda ret: None):
            self.client.apps.USERS.cmds.SetUserData(
                login=get_user_name(),
                data_id='flow_bookmarked_uid',
                key=name,
                value=node_uid
            )
        
        # update this view's bookmarks
        # TODO: we should listen to an UPDATED event on the user data and update
        # so that all NodeTreePanel have sync'ed bookmarks.
        # This is not clean at all:
        self._bookmarks[name] = node_uid
        self.menu_bar.set_bookmark_names(
            self, sorted(self._live_bookmarks.keys()), sorted(self._bookmarks.keys())
        )
    
    def delete_bookmark(self, bookmark_name):
        # store the new bookmark in user data
        with self.client.result_to(lambda ret: None):
            self.client.apps.USERS.cmds.SetUserData(
                login=get_user_name(),
                data_id='flow_bookmarked_uid',
                key=bookmark_name,
                value=None
            )
        
        # update this view's bookmarks
        # TODO: we should listen to an UPDATED event on the user data and update
        # so that all NodeTreePanel have sync'ed bookmarks.
        # This is not clean at all:
        del self._bookmarks[bookmark_name]
        self.menu_bar.set_bookmark_names(
            self, sorted(self._live_bookmarks.keys()), sorted(self._bookmarks.keys())
        )
        
    def goto_bookmark(self, bookmark_name):
        node_id = self._bookmarks.get(bookmark_name)
        if node_id is None:
            return
        self.find_and_set_current(node_id)

    def goto_live_bookmark(self, bookmark_name):
        node_id = self._live_bookmarks.get(bookmark_name)
        if node_id is None:
            return
        self.find_and_set_current(node_id)
        
    def _on_current_changed(self, current_index, previous_index):
        if not current_index.isValid():
            self.current_node_id = None
            self.sel_model.clear()
            return
        
        node_id = current_index.internalPointer().node_id()
        if node_id != self.current_node_id:
            self.current_node_id = node_id
            if self._on_current_changed_func is not None:
                self._on_current_changed_func(node_id)

    def find_and_set_current(self, node_id, force=False):
        if not force and node_id == self.current_node_id:
            return
        
        if node_id is None:
            return

        found, item = self.model.root().find(node_id)
        if item is None:
            return
        
        index = self.model.createIndex(item.row(), 0, item)
        if found:
            self.sel_model.setCurrentIndex(index, self.sel_model.ClearAndSelect)
        else:
            self.sel_model.select(index, self.sel_model.ClearAndSelect)
        self.tree.expand(index)
        self.tree.scrollTo(index, self.tree.EnsureVisible)

    def show_item_menu(self, index):
        if not index.isValid():
            return
        
        self.sel_model.select(index, self.sel_model.ClearAndSelect)

        item = index.internalPointer()
                
        menu = QtGui.QMenu()
        
        if self._item_menu_filler_func is not None:
            self._item_menu_filler_func(item, menu)
            
        if menu.isEmpty():
            menu.addAction('No action here :/')
            
        menu.exec_(QtGui.QCursor.pos())

    def run_proc(self, proc_id):
        prepare_proc_execution(self.client, proc_id)

        