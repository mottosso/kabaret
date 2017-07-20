
from itertools import izip_longest

from kabaret.core.events.event import Event
from kabaret.core.utils import resources

from kabaret.gui.widgets import log_panel, async_selector
from kabaret.gui.widgets.views import AbstractGuiGraphicsView, AbstractGuiScrollView, QtGui, QtCore, resources

from .path_label import PathLabel
from .proc_exec_panel import prepare_proc_execution

class Item(QtGui.QGraphicsProxyWidget):
    try:
        to_shown = QtCore.Signal()
        to_hidden = QtCore.Signal()
    except AttributeError:
        to_shown = QtCore.pyqtSignal()
        to_hidden = QtCore.pyqtSignal()
    
    def __init__(self, parent, index, node_view):
        super(Item, self).__init__(parent)

        self.index = index
        self.infos = None
        self._is_hidden = False

        self.node_view = node_view
        
        self._create_widget()
                
        self._state_machine = QtCore.QStateMachine(self)
        self.anims = QtCore.QSequentialAnimationGroup()
        self.anims.addPause(30*(self.index-1))
        grp = QtCore.QParallelAnimationGroup()
        opanim = QtCore.QPropertyAnimation(self, "opacity")
        opanim.setDuration(100)
        grp.addAnimation(opanim)
        scaleanim = QtCore.QPropertyAnimation(self, "scale")
        scaleanim.setDuration(100)
        grp.addAnimation(scaleanim)
        self.anims.addAnimation(grp)
        
        self.hidden = QtCore.QState(self._state_machine)
        self.hidden.assignProperty(self, 'opacity', .1)
        self.hidden.assignProperty(self, 'scale', 0.1)
        
        self.hidden_done = QtCore.QState(self._state_machine)
        self.hidden_done.entered.connect(self._on_hidden_done)
        
        self.shown = QtCore.QState(self._state_machine)
        self.shown.assignProperty(self, 'opacity', 1)
        self.shown.assignProperty(self, 'scale', 1)
        self.shown.entered.connect(self._on_shown_start)

        self.hidden.addTransition(self.hidden.propertiesAssigned, self.hidden_done)
        
        tr = self.hidden_done.addTransition(self.to_shown, self.shown)
        tr.addAnimation(self.anims)
        
        tr = self.shown.addTransition(self.to_hidden, self.hidden)
        tr.addAnimation(self.anims)

        self._state_machine.setInitialState(self.hidden_done)
        self._state_machine.start()
    
    def _create_widget(self):
        raise NotImplementedError
 
    def _on_hidden_done(self):
        self._is_hidden = True
        self._update_widget()
        self.parentItem().lineup()
        
    def _update_widget(self):
        raise NotImplementedError
                
    def _on_shown_start(self):
        self._is_hidden = False

    def set_infos(self, node_infos):
        self.infos = node_infos
        if not self._is_hidden:
            self.to_hidden.emit()
        else:
            self._on_hidden_done()

#class CasesItemMenu(Item):
#    def _create_widget(self):
#        self._button = QtGui.QPushButton('', None)
#        self._button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#        self._menu = QtGui.QMenu('Select')
#        self._button.customContextMenuRequested.connect(self._on_menu)
#        self._button.clicked.connect(self._on_menu)
#        self.setWidget(self._button)
#
#    def _update_widget(self):
#        if self.infos is not None:
#            text = 'Select '+self.infos['cases']
#            self._button.setText(text)
#            self._button.setToolTip('Cases: '+self.infos['cases'])
#            self.setVisible(True)
#            self.updateGeometry()
#            self.to_shown.emit()
#        else:
#            self._button.setText('')
#            self._button.setToolTip('')
#            self.setVisible(False)
#            self.updateGeometry()
#    
#    def _on_menu(self, pos=None):
#        self._menu.clear()
#        
#        node_id = self.infos['node_id']
#        relation_name = self.infos['cases']
#        try:
#            case_ids = self.node_view.client.apps.FLOW.cmds.GetCaseIds(node_id, relation_name)
#        except:
#            import traceback
#            traceback.print_exc()
#            case_ids = ['oops, got an error :(']
#            self._menu.addAction('oops, got an error :(')
#        else:
#            for case_id in case_ids:
#                self._menu.addAction(
#                    case_id, lambda case_id=case_id:self._on_select(case_id)
#                )
#        self._menu.exec_(pos or QtGui.QCursor.pos())
#        
#    def _on_select(self, case_id):
#        self.node_view.goto(self.infos['node_id']+(self.infos['cases']+':'+case_id,))
        
class ManyItemSelector(Item):
    def _create_widget(self):
        self._selector = async_selector.Selector('Select...', None)
        self._selector.selected.connect(self._on_select)
        self.setWidget(self._selector)

    def _update_widget(self):
        if self.infos is not None:
            help_text = 'Select %s...'%(self.infos['cases'],)
            self._selector.set_help_text(help_text)
            self._selector.setToolTip(help_text)
            self._selector.show_wait()
            with self.node_view.client.result_to(self._fill_selector):
                self.node_view.client.apps.FLOW.cmds.GetCaseIds(self.infos['node_id'], self.infos['cases'])
            self.setVisible(True)
            self.updateGeometry()
            self.to_shown.emit()
        else:
            self._selector.set_help_text('')
            self._selector.setToolTip('')
            self._selector.set_items([])
            self.setVisible(False)
            self.updateGeometry()
    
    def _fill_selector(self, cases_ids):
        self._selector.set_items([ (i,i) for i in cases_ids ])
        
#    def _on_menu(self, pos=None):
#        self._menu.clear()
#        
#        node_id = self.infos['node_id']
#        relation_name = self.infos['cases']
#        try:
#            case_ids = self.node_view.client.apps.FLOW.cmds.GetCaseIds(node_id, relation_name)
#        except:
#            import traceback
#            traceback.print_exc()
#            case_ids = ['oops, got an error :(']
#            self._menu.addAction('oops, got an error :(')
#        else:
#            for case_id in case_ids:
#                self._menu.addAction(
#                    case_id, lambda case_id=case_id:self._on_select(case_id)
#                )
#        self._menu.exec_(pos or QtGui.QCursor.pos())
        
    def _on_select(self, label, case_id):
        print 'on select case', label, case_id
        if case_id is None:
            #TODO: should we asks for confirmation?
            case_id = str(label).title().replace(' ', '') 
        self.node_view.goto(self.infos['node_id']+(self.infos['cases']+':'+str(case_id),))
        
class CaseItem(Item):
    def _create_widget(self):
        self._button = QtGui.QPushButton('???', None)
        self._button.clicked.connect(self._on_click)
        self.setWidget(self._button)

    def _update_widget(self):
        if self.infos is not None:
            text = self.infos['case']
            self._button.setText(text)
            try:
                self._button.setIcon(
                    resources.get_icon(
                        ('flow.icons.nodes',self.infos['icon']),
                        self._button
                    )
                )
            except resources.ResourcesError:
                pass
            self._button.setToolTip('Case: '+self.infos['case'])
            self.setVisible(True)
            self.updateGeometry()
            self.to_shown.emit()
        else:
            self._button.setText('')
            self._button.setToolTip('')
            self.setVisible(False)
            self.updateGeometry()

    def _on_click(self):
        self.node_view.goto(self.infos['node_id']+(self.infos['case'],))

class ChildItem(Item):
    def _create_widget(self):
        self._button = QtGui.QPushButton('???', None)
        self._button.clicked.connect(self._on_click)
        self.setWidget(self._button)

    def _update_widget(self):
        if self.infos is not None:
            self._button.setText(self.infos['name'])
            try:
                self._button.setIcon(
                    resources.get_icon(
                        ('flow.icons.nodes',self.infos['icon']),
                        self._button
                    )
                )
            except resources.ResourcesError:
                pass
            self._button.setToolTip(self.infos['type'])
            self.setVisible(True)
            self.updateGeometry()
            self.to_shown.emit()
        else:
            self._button.setText('')
            self._button.setToolTip('')
            self.setVisible(False)
            self.updateGeometry()

    def _on_click(self):
        self.node_view.goto(self.infos['id'])

class ProcItem(Item):
    def _create_widget(self):
        self._button = QtGui.QPushButton('???', None)
        self._button.clicked.connect(self._on_click)
        self.setWidget(self._button)

    def _update_widget(self):
        if self.infos is not None:
            self._button.setText('%s (Click to Execute)'%(self.infos['name'],))
            try:
                self._button.setIcon(
                    resources.get_icon(
                        ('flow.icons.nodes',self.infos['icon']),
                        self._button
                    )
                )
            except resources.ResourcesError:
                pass
            self._button.setToolTip(self.infos['type'])
            self.setVisible(True)
            self.updateGeometry()
            self.to_shown.emit()
        else:
            self._button.setText('')
            self._button.setToolTip('')
            self.setVisible(False)
            self.updateGeometry()

    def _on_click(self):
        self.node_view.run_proc(self.infos['id'])
        
class _Liner(QtGui.QGraphicsWidget):
    # After hours of strugling with 
    # QGraphicsLinearLayout, I give up and 
    # use this instead.
    def __init__(self, parent):
        super(_Liner, self).__init__(parent)
        self.spacing = 5
        
    def lineup(self):
        z = 100
        y = 0 
        ig = [ (i.index, i, i.geometry()) for i in self.childItems() if i.isVisible() ]
        if not ig:
            return
        w = max([ g.width() for index, i, g in ig ])
        for _, child, geom in sorted(ig):
            geom.setWidth(w)
            child.setGeometry(geom)
            child.setPos(0, y)
            child.setZValue(z)
            y += geom.height() + self.spacing
            z -= 1

class NodesView(AbstractGuiGraphicsView):
    def __init__(self, parent, client, app_name):
        super(NodesView, self).__init__(parent, client, app_name)
        
        self.node_id = None
        
        self.scene = QtGui.QGraphicsScene(0,0,30,30)
        self.scene.setBackgroundBrush(self.palette().window());
        self.setScene(self.scene)
        
        widget = QtGui.QGraphicsWidget()
        layout = QtGui.QGraphicsLinearLayout(QtCore.Qt.Vertical, widget)
        widget.setLayout(layout)
        self.scene.addItem(widget)
        
        self._path_label = PathLabel()
        self._path_label.node_id_clicked.connect(self.goto)
        self._path_label_proxy = QtGui.QGraphicsProxyWidget(widget)
        self._path_label_proxy.setWidget(self._path_label)
        layout.addItem(self._path_label_proxy)
        
        self._throbber_pix = resources.get_pixmap(
            'gui.icons', 'throbber.gif'
        )
        
        header = QtGui.QWidget()
        header.setLayout(QtGui.QVBoxLayout())
        top_layout = QtGui.QHBoxLayout()
        header.layout().addLayout(top_layout)
        self._pict_label = QtGui.QLabel(header)
        top_layout.addWidget(self._pict_label)
        self._type_label = QtGui.QLabel(header)
        top_layout.addWidget(self._type_label)
        top_layout.addStretch(10)
        bot_layout = QtGui.QHBoxLayout()
        header.layout().addLayout(bot_layout)
        self._doc_label = QtGui.QLabel(header)
        bot_layout.addWidget(self._doc_label)
        
        plp = QtGui.QGraphicsProxyWidget(widget)
        plp.setWidget(header)
        layout.addItem(plp)
        
        self.liner = _Liner(widget)
        layout.addItem(self.liner)
        
        self._proc_items = []
        self._many_items = []
        self._case_items = []
        self._child_items = []
        
        self.client.add_event_handler(
            self.on_nav_current_changed, 'GUI', ['FLOW', 'Nav', 'current']
        )


    def on_view_toggled(self, visible):
        super(NodesView, self).on_view_toggled(visible)
        if visible:
            self.reload_node_id()
            
    def clear(self):
        [ nw.set_infos(None) for nw in self._many_items+self._case_items+self._child_items ]
        self.liner.lineup()
    
    def on_connect(self):
        self.reload_node_id() 
            
    def on_disconnect(self):
        self.clear()
        
    def on_nav_current_changed(self, event):
        node_id = event.data
        self.load_node_id(node_id)
    
    def reload_node_id(self):
        node_id = self.node_id
        self.node_id = None
        self.load_node_id(node_id)

    def load_node_id(self, node_id):
        if self.node_id is not None and node_id == self.node_id:
            return
        self.node_id = node_id
        
        if not self.is_active():
            return
        
        self.clear()
        if node_id is None:
            self.node_id = node_id = self.client.apps.FLOW.cmds.GetRootId()
        
        self._path_label.set_node_id(node_id)
        self._path_label_proxy.updateGeometry()
        
        self._pict_label.setPixmap(self._throbber_pix)
        self._type_label.setText('Loading')
        self._doc_label.setText('...')
        
        with self.client.result_to(self.on_get_relations):
            self.client.apps.FLOW.cmds.GetNodeRelations(node_id, child_nodes=True, proc_nodes=True)

        with self.client.result_to(self.on_get_node_type_infos):
            self.client.apps.FLOW.cmds.GetTypeUiInfos(node_id)
            
    def on_get_relations(self, relations):
        self.on_get_proc_nodes(relations.get('Proc', []))
        self.on_get_many_infos(relations.get('Many', []))
        self.on_get_one_infos(relations.get('One', []))
        self.on_get_child_nodes(relations.get('Child', []))
        self.scene.setSceneRect(QtCore.QRectF())

        self.liner.lineup()
    
    def on_get_proc_nodes(self, proc_infos):
        for item, proc_info in izip_longest(list(self._proc_items), proc_infos):
            if item is None:
                item = ProcItem(self.liner, len(self._proc_items)+1, self)
                self._proc_items.append(item)
            
            if proc_info is not None:
                proc_name, proc_info = proc_info
                proc_info.update({
                    'name': proc_name, 
                    'id':tuple(self.node_id)+(proc_name,), 
                })
                item.set_infos(proc_info)
            else:
                item.set_infos(None)
                
    def on_get_many_infos(self, cases_names):
        for item, relation_info in izip_longest(list(self._many_items), cases_names):
            if item is None:
                item = ManyItemSelector(self.liner, len(self._many_items)+1, self)
                self._many_items.append(item)
                
            if relation_info is not None:
                relation_name, related_infos = relation_info
                related_infos.update({'cases':relation_name, 'node_id':self.node_id})
                item.set_infos(related_infos)
            else:
                item.set_infos(None)

    def on_get_one_infos(self, case_names):
        for item, relation_info in izip_longest(list(self._case_items), case_names):
            if item is None:
                item = CaseItem(self.liner, len(self._case_items)+1, self)
                self._case_items.append(item)
                
            if relation_info is not None:
                relation_name, related_infos = relation_info
                related_infos.update({'case':relation_name, 'node_id':self.node_id})
                item.set_infos(related_infos)
            else:
                item.set_infos(None)
    
    def on_get_child_nodes(self, all_node_infos):
        # filter out protected names:
        all_node_infos = [ infos for infos in all_node_infos if not infos[0].startswith('_') ]

        for item, node_infos in izip_longest(list(self._child_items), all_node_infos):
            if item is None:
                item = ChildItem(self.liner, len(self._child_items)+1, self)
                self._child_items.append(item)
            
            if node_infos is not None:
                node_name, node_infos = node_infos
                node_infos.update({
                    'name': node_name, 
                    'id':tuple(self.node_id)+(node_name,), 
                })
                item.set_infos(node_infos)
            else:
                item.set_infos(None)
                
    def on_get_node_type_infos(self, ui_infos):
        self._type_label.setText(ui_infos['type'])
        self._doc_label.setText(ui_infos['doc'] or '')
        
        if ui_infos['icon']:
            try:
                pix = resources.get_pixmap('flow.icons.nodes', ui_infos['icon'])
                self._pict_label.setPixmap(pix)
            except resources.NotFoundError:
                self._pict_label.clear()
        else:
            self._pict_label.clear()
            
    def goto(self, node_id):
        if not self.client.connected():
            return
        
        if node_id is None:
            with self.client.result_to(self.goto):
                self.client.apps.FLOW.cmds.GetRootId()
        else:
            self.client.send_event(
                Event('GUI', ['FLOW', 'Nav', 'current'], Event.TYPE.UPDATED, node_id)
            )

    def run_proc(self, proc_id):
        prepare_proc_execution(self.client, proc_id)

