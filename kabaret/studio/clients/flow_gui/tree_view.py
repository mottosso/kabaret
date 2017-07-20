'''


'''

from kabaret.core.events.event import Event
from kabaret.gui.widgets.views import AbstractGuiView, QtGui, QtCore, resources

from .node_tree import NodeTreePanel

class TreeView(AbstractGuiView):
    def __init__(self, parent, client, app_name):
        super(TreeView, self).__init__(parent, client, app_name)

        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
             
        self.tp = NodeTreePanel(self, self.client)
        self.tp.set_item_menu_filler(self._add_action_to_item_menu)
        self.tp.set_on_current_node_id_change_func(self.goto)
        self.layout().addWidget(self.tp)
            
        # EVENTS
        self.client.add_event_handler(
            self._on_nav_current_changed, 'GUI', ['FLOW', 'Nav', 'current']
        )
        self.client.add_event_handler(
            self._on_nav_root_changed, 'GUI', ['FLOW', 'Nav', 'root'], Event.TYPE.UPDATED
        )
        self.client.add_event_handler(
            self._on_live_bookmark_changed, 'GUI', ['FLOW', 'Nav', 'live_bookmark'], Event.TYPE.UPDATED
        )

    def on_connect(self):
        self.tp.set_connected()

    def on_disconnect(self):
        self.tp.set_disconnected()
        
    def goto(self, node_id):
        self.client.send_event(
            Event('GUI', ['FLOW', 'Nav', 'current'], Event.TYPE.UPDATED, node_id)
        )

    def _on_nav_current_changed(self, event):
        node_id = event.data        
        self.tp.find_and_set_current(node_id)

    def _on_live_bookmark_changed(self, event):
        bookmark_name = event.path[-1]
        node_id = event.data
        self.tp.ensure_live_bookmark(bookmark_name, node_id)
        
    def _on_nav_root_changed(self, event):
        root_name = event.path[-1]
        root_id = event.data
        self.tp.ensure_root_name(root_name, root_id)
        self.tp.set_root_to_id(root_id)

    def _add_action_to_item_menu(self, item, menu):
        for pix_ref, name, func in item.get_menu_actions(self.tp):
            if name is None:
                menu.addSeparator()
                continue
            got_actions = True
            icon = item.model().get_icon(*pix_ref)
            if icon:
                menu.addAction(icon, name, func)
            else:
                menu.addAction(name, func)

        menu.addSeparator()
        for proc_name, proc_infos in item.get_proc_infos():
            icon = item.model().get_icon('flow.icons.nodes', proc_infos['icon'])
            to_call = lambda item=item, proc_name=proc_name: self.tp.run_proc(item.node_id()+(proc_name,))
            if icon:
                menu.addAction(icon, proc_name, to_call)
            else:
                menu.addAction(proc_name, to_call)
                
        menu.addSeparator()
        triggers_infos, choices_fors_infos = item.get_menu_param_infos()
        for trigger_infos in triggers_infos:
            menu.addAction(
                trigger_infos['label'],
                lambda item=item, param_name=trigger_infos['name']: item.trigger(param_name)
            )
        
        if choices_fors_infos:
            menu.addSeparator()
            for choices_for_infos in choices_fors_infos:
                menu.addAction(
                    SetChoiceAction(menu, item, choices_for_infos)
                )

class SetChoiceAction(QtGui.QWidgetAction):
    def __init__(self, parent, item, param_infos):
        super(SetChoiceAction, self).__init__(parent)
        self.param_infos = item.get_param_infos(param_infos['name'])
        choices = self.param_infos['value']
        target_value = item.get_param_infos(self.param_infos['editor_options']['target_param'])['value']
        self.item = item
        
        pWidget = QtGui.QWidget(None)
        pLayout = QtGui.QVBoxLayout()
        pWidget.setLayout(pLayout)
        pLabel = QtGui.QLabel(pWidget)
        pLayout.addWidget(pLabel)
        self.setDefaultWidget(pWidget)

        if not choices:
            pLabel.setText(
                '%s is %r, cannot change it.'%(
                    self.param_infos['editor_options']['target_param'],
                    target_value
                )
            )
            return
        
        if target_value not in choices:
            pLabel.setText(
                'Change %s from %r to:'%(
                    self.param_infos['editor_options']['target_param'],
                    target_value
                ) 
            )
        else:
            pLabel.setText(
                'Set %s:'%(
                    self.param_infos['editor_options']['target_param'],
                )
            )
        
        self._buttons = []
        for v in choices:
            label = v
            if isinstance(label, tuple):
                #TODO: this sucks like dyson. find a cleaner way to handle uid choices
                label = '/'.join(label)
            elif not isinstance(label, basestring):
                label = repr(v)
            if v == target_value:
                label = '[ %s ]'%(label,)
            b = QtGui.QPushButton(label, pWidget)
            pLayout.layout().addWidget(b)
            b.clicked.connect(lambda checked=False, v=v: self.on_button_clicked(checked, v))
            self._buttons.append(b)

    

    def on_button_clicked(self, *args):
        if len(args) == 1:
            # pyside...
            value = args[0]
        else:
            # pyqt
            value = args[-1]
        self.item.apply_choice_for_selection(
            self.param_infos,
            value
        )
        self.parent().hide()
        