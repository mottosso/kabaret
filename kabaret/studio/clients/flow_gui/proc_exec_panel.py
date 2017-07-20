'''


'''

from kabaret.gui.widgets import QtGui, QtCore
from kabaret.gui.widgets.views import WorkersTable, WorkerToolBar
from kabaret.gui.widgets.value_editor import get_global_factory, ValueEditorMixin, ValueController
from .utils import make_relative_id


def prepare_proc_execution(client, proc_id, dialog_parent=None):
    '''
    Does what's needed to execute the ProcNode with the given proc_id.
    In simple circumstances the exection may run directly but in most
    cases a Dialog will be presented to the user so he can configure
    the execution or cancel it.
    
    The dialog_parent must be None or a widget instance.
    '''
    context = get_execution_context(client, proc_id)
    #import pprint
    #pprint.pprint(context)
    print 'allow_exec:', context['allow_exec'], 'params:', context['params'], 'up_contexts:', context['up_contexts']
    if context['allow_exec'] and not context['params'] and not context['up_contexts']:
        # This does not need user validation if the default worker 
        # can handle the execution:
        features = context['depth_needed_features']
        documents = context['all_documents']
        worker_id = client.get_embedded_worker_id(features, documents)
        print 'EMBEDDED COMPATIBLE WORKER ID', worker_id
        if worker_id is not None:
            return execute_proc(client, proc_id, context, worker_id)

    # Use the dialog to let the user choose options and worker:
    dialog = ProcExecDialog(dialog_parent, client)
    dialog.exec_for_proc(proc_id, context)
    # Don't let the dialog die with active event handlers!:
    dialog.about_to_be_destroyed()
        
def get_execution_context(client, proc_id, context=None):
    '''
    Returns an execution context usable with the execute(context)
    function.
    
    If the context argument is not None, it is used as a starting
    point to build a new one.
    If not None, it must be a dict with a valid structure.
    (You should use one returned be this function...)
    
    The returned object is a dict with a value associated to
    the 'allow_exe' key. This value must be True in order for the
    execute(context) function to accept it. 
    '''
    context = client.apps.FLOW.cmds.PrepareProcExec(proc_id, context)
    #import pprint
    #pprint.pprint(context)
    return context

def execute_proc(client, proc_id, context, worker_id=None):
    client.apps.FLOW.cmds.ProcExec(proc_id, context, worker_id)




class NodeBox(QtGui.QGroupBox):
    _SS = 'QGroupBox { font-size: 14px; font-weight: bold }'
    
    def __init__(self, parent, proc_exec_panel, node_id, open=True):
        super(NodeBox, self).__init__(parent)
        self.proc_exec_panel = proc_exec_panel
        self.node_id = node_id
        
        self.setStyleSheet(self._SS)
        
        self.update_label()
                    
        lo = QtGui.QVBoxLayout()
        lo.setContentsMargins(0, 10, 0, 0)
        lo.setSpacing(0)
        self.setLayout(lo)
        
        self._holder = QtGui.QWidget(self)
        self._holder.setLayout(QtGui.QFormLayout())
        lo.addWidget(self._holder)
                
        self.setCheckable(True)
        self.toggled.connect(self._on_toggled)
        self.setChecked(open)

    def _set_closed(self, b):
        lo = self.layout()
        for i in range(lo.count()):
            lo.itemAt(i).widget().setHidden(b)
        self.setFlat(b)
        self.setStyleSheet(self._SS) # force update of property dependent style
        self.proc_exec_panel.set_default_node_groupe_state(self.node_id, open=not b)

    def _on_toggled(self, b):
        self._set_closed(not b)
        
    def add_context(self, context):
        if 1 or self._holder.layout().rowCount():
            line = QtGui.QFrame(self._holder)
            line.setFrameShape(line.HLine)
            self._holder.layout().addRow(line)
        
        proc_uid = context['proc_uid']
        label = proc_uid[-1]

        self._holder.layout().addRow(
            '<h3>%s</h3>'%(label,), 
            ExecContextWidget(self._holder, self.proc_exec_panel, context)
        )
    
    def update_label(self):
        self.setTitle(
            '/'.join(make_relative_id(self.proc_exec_panel.node_id[:-1], self.node_id)),
        )


#class ProcParams(QtGui.QWidget):
#    def __init__(self, parent, node_box, proc_uid, params, proc_doc):
#        super(ProcParams, self).__init__(parent)
#        self.node_box = node_box
#        self.proc_id = proc_uid
#        self.params = params
#        
#        layout = QtGui.QFormLayout()
#        self.setLayout(layout)
#        
#        self.setToolTip(proc_doc or '')
#        
#        for param in self.params:
#            if param['name'] == 'Needed':
#                self._add_needed_indicator(layout, param['value'])
#            else:
#                self._add_param(
#                    layout, param['name'], param['value'], 
#                    param['editor'], param['editor_options'], 
#                    param['doc']
#                )
#    
#    def _add_needed_indicator(self, layout, needed):
#        if needed:
#            text = 'This Proc says you should execute it!'
#        else:
#            text = 'This Proc seems up to date'
#        layout.addRow('Needed', QtGui.QLabel(text))
#
#    def _add_param(self, layout, name, value=None, editor=None, editor_options=None, doc=None):
#        input_controler = InputControler(self, name)
#        value_editor = self.node_box.proc_exec_panel.EDITOR_FACTORY.create(
#            self, editor, input_controler, options=editor_options
#        )
#        value_editor.set_editable()
#        value_editor.set_busy = lambda: None
#        
#        value_editor._input_controler = input_controler
#        input_controler.value_editor = value_editor
#        
#        value_editor.set_value(value)
#        tt = '<b>%s</b>'%(name,)
#        if doc:
#            tt += '<pre>'+doc+'</pre>'
#        value_editor.set_tooltip(tt)
#
#        layout.addRow(name, value_editor)

#class ParamInputControler(object):
#    def __init__(self, context_widget, param_name):
#        super(ParamInputControler, self).__init__()
#        self.context_widget = context_widget
#        self.param_name = param_name
#        self.value_editor = None
#    
#    def value_editor_set(self, value):
#        self.context_widget.set_param_value(self.param_name, value)

class ContextParamController(ValueController):
    '''
    This controller overrides _start_listening() and stop_listening()
    to not use the kabaret client
    '''
    #TODO: this kind of controller (sync, without client) should be available in gui.widget.value_editor!
    def __init__(self, context_widget, param_name, param_infos):
        super(ContextParamController, self).__init__(None, param_name)
        self.context_widget = context_widget
        self.param_infos = param_infos
        
    def set_editor(self, editor):
        super(ContextParamController, self).set_editor(editor)
        
        self.editor.set_editable()
        #self.editor.set_busy = lambda: None
                    
        editor.set_value(self.param_infos['value'])
        tt = '<b>%s</b>'%(self.value_id,)
        doc = self.param_infos.get('doc')
        if doc:
            tt += '<pre>'+self.param_infos['doc']+'</pre>'
        self.editor.set_tooltip(tt)

    def _start_listening(self):
        pass
    
    def stop_listening(self):
        pass
    
    def set_value(self, value):
        self.context_widget.set_param_value(self.value_id, value)
        
class ContextAttrController(ContextParamController):
    def __init__(self, context_widget, attr_name, init_value):
        super(ContextAttrController, self).__init__(context_widget, attr_name, {'value':init_value})
    
    def set_value(self, value):
        self.context_widget.set_context_attr_value(self.value_id, value)

class ExecContextWidget(QtGui.QWidget):
    def __init__(self, parent, proc_exec_panel, context):
        super(ExecContextWidget, self).__init__(parent)
        self.proc_exec_panel = proc_exec_panel
        self.context = context
        
        self.setLayout(QtGui.QVBoxLayout())
        
        if context['proc_doc']:
            doc_label = QtGui.QTextEdit(self)
            doc_label.setReadOnly(True)
            doc_label.setPlainText(context['proc_doc'])
            self.layout().addWidget(doc_label)
        
        self.param_layout = QtGui.QFormLayout()
        self.param_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        self.layout().addLayout(self.param_layout)
        
        lb = QtGui.QLabel(', '.join(context['needed_features']) or 'None', self)
        self.param_layout.addRow('Worker Features', lb)

        lb = QtGui.QLabel(context['document'] or 'None', self)
        self.param_layout.addRow('Document', lb)
        
        why = context['why_needs_to_run'] and ': '+context['why_needs_to_run'] or ''
        lb = QtGui.QLabel(
            context['needs_to_run'] and 'Yes'+why or 'No'+why,
            self
        )
        self.param_layout.addRow('Needed', lb)

        why = context['why'] and ': '+context['why'] or ''
        lb = QtGui.QLabel(
            (context['allow_exec'] and 'Yes' or '<font color="#FF8888">No')+str(why),
            self
        )
        self.param_layout.addRow('Ready', lb)
        
        input_controler = ContextAttrController(self, 'run', self.context['run'])
        value_editor = self.proc_exec_panel.EDITOR_FACTORY.create(
            self, 'bool', input_controler
        )
#        value_editor.set_editable()
#        value_editor.set_busy = lambda: None
#        value_editor._input_controler = input_controler
#        input_controler.value_editor = value_editor
#        value_editor.set_value(self.context['run'])
        self.param_layout.addRow('Run', value_editor)

        self.param_layout.addRow(' ', QtGui.QWidget(self))
        
        for param in self.context['params']:
            controller = ContextParamController(self, param['name'], param)
            value_editor = self.proc_exec_panel.EDITOR_FACTORY.create(
                self, param['editor'], controller, options=param['editor_options']
            )
    
            self.param_layout.addRow(param['name'], value_editor)
    
    def set_param_value(self, param_name, value):
        for param in self.context['params']:
            if param['name'] == param_name:
                param['value'] = value
                self.proc_exec_panel.do_round_trip()
                return
        raise Exception(
            'Could not set the value for param %r: not found in context %r'%(
                param_name,
                self.context
            )
        )
    
    def set_context_attr_value(self, attr_name, value):
        self.context[attr_name] = value
        self.proc_exec_panel.do_round_trip()
        
class ProcExecPanel(QtGui.QWidget):
    USE_SPLITTER = False 
    EDITOR_FACTORY = None
    
    try:
        context_updated = QtCore.Signal()
    except AttributeError:
        context_updated = QtCore.pyqtSignal()

    def __init__(self, parent, client):
        super(ProcExecPanel, self).__init__(parent)
        if self.__class__.EDITOR_FACTORY is None:
            self.__class__.EDITOR_FACTORY = get_global_factory()
        
        self.client = client
        
        self._context = None
    
        self.setLayout(QtGui.QVBoxLayout())
        
        #
        #    HEADER
        #
        self.header = QtGui.QLabel(self)
        self.layout().addWidget(self.header)
        
        if self.USE_SPLITTER:
            splitter = QtGui.QSplitter(self)
            self.layout().addWidget(splitter, stretch=100)
        else:
            splitter = QtGui.QHBoxLayout()
            self.layout().addLayout(splitter)
            
        #
        #    INPUT COLUMN
        #
        input_scroll = QtGui.QScrollArea(self)
        input_scroll.setFrameStyle(input_scroll.NoFrame)
        input_scroll.setWidgetResizable(True)
        self.input_parent = QtGui.QWidget()
        lo = QtGui.QVBoxLayout()
        self.input_layout = QtGui.QVBoxLayout()
        lo.addLayout(self.input_layout)
        lo.addStretch(100)
        self.input_parent.setLayout(lo)
        input_scroll.setWidget(self.input_parent)
        splitter.addWidget(input_scroll)
        
        self._node_boxes = {}
        self._node_boxes_open = {}
        
        #
        #    WORKER COLUMN
        #
        column = QtGui.QWidget(self)
        column.setLayout(QtGui.QVBoxLayout())
        column.layout().setContentsMargins(0,0,0,0)
        splitter.addWidget(column)

        self.workers_table = WorkersTable(self.client, self)
        self.workers_table.show_mine_only(True)
        self.workers_table.selectionModel().selectionChanged.connect(self._on_worker_changed)
        self.workers_table.refresh_done.connect(self._on_worker_changed)
        
        self.workers_tb = WorkerToolBar(self, self.workers_table)

        column.layout().addWidget(self.workers_tb)
        column.layout().addWidget(self.workers_table)
        
        self.workers_table.on_connect()
        self.workers_tb.on_connect()
        
        self.depth_needed_features_label = QtGui.QLabel(
            'Overall Features Needed: <no context loaded>',
            self
        )
        column.layout().addWidget(self.depth_needed_features_label)
        
        self.acceptable_docs_label = QtGui.QLabel(
            'Acceptable Document: <no context loaded>',
            self
        )
        column.layout().addWidget(self.acceptable_docs_label)
        
        self.selected_worker_features_label = QtGui.QLabel(
            'Selected Features: <No Worker Selected>',
            self
        )
        column.layout().addWidget(self.selected_worker_features_label)
        
        self.selected_worker_doc_label = QtGui.QLabel(
            'Selected Document: <No Worker Seleced>',
            self
        )
        column.layout().addWidget(self.selected_worker_doc_label)
        
        if self.USE_SPLITTER:
            if 0:
                # make the detail panel hidden but resizable:
                splitter.setSizes([1,0])
            else:
                splitter.setSizes([100,100])

    def about_to_be_destroyed(self):
        '''
        Someone must call this before the death of this Panel.
        '''
        self.workers_table.stop_listening()
        
    def _on_worker_changed(self, model_index=None):
        self.selected_worker_features_label.setText(
            'Selected Features: '+
            ', '.join(self.workers_table.get_current_features())
        )        
        self.selected_worker_doc_label.setText(
            'Seleted Document: %s'%(self.workers_table.get_current_document(),)
        )
        self.context_updated.emit()
        
    def clear(self):
        self.header.setText('<h1>No Proc selected.</h1>')
        self.proc_id = None
        self.node_id = None
        self._context = None
        self._node_boxes = {}
        
        lo = self.input_layout
        while lo.count():
            li = lo.takeAt(0)
            w = li.widget()
            if w is not None:
                w.deleteLater()
            del li
        
        if 0:
            # Not required, eats bandwidth,
            # and there's a button but it...
            self.workers_table.refresh()
        
    def load_context(self, context_data):
        self.clear()
        
        self._context = context_data
        self.proc_id = self._context['proc_uid']
        self.node_id = self.proc_id[:-1]

        self.header.setText('<h1>%s</h1>'%('/'.join(self.node_id),))

        self._add_context_params(self._context)
        
        if 0:
            details = []
            for p in self._context['passes']:
                processes = p['processes']
                if processes:
                    details.append('#--- %s'%(p['name'],))
                    last_uid = None
                    for (proc_uid, func_name, args, kwargs) in processes:
                        if last_uid != proc_uid:
                            details.append('   '+'/'.join(proc_uid))
                        last_uid = proc_uid
                        details.append(
                            '        %s(%s)'%(
                                func_name,
                                ', '.join(
                                    [ repr(i) for i in args ]
                                    + [ '%s=%r'%(k, v) for k, v in kwargs.items() ]
                                )
                            )
                        )
                    details.append('')
            self.run_details.setText('\n'.join(details))
            
        else: # if 0
            self.depth_needed_features_label.setText(
                'Overall Features Needed: %s'%(', '.join(self._context['depth_needed_features']) or 'None',)
            )
            
            acceptable_docs = self._acceptable_worker_documents()
            if acceptable_docs == [None]:
                acceptable_text = 'Free Worker'
            else:
                acceptable_text = ', '.join([ i is None and 'Any' or i for i in acceptable_docs ])
            self.acceptable_docs_label.setText(
                'Acceptable Document(s): '+acceptable_text
            )
            
        self.context_updated.emit()
    
    def set_default_node_groupe_state(self, node_id, open):
        self._node_boxes_open[node_id] = open
    
    def get_default_node_groupe_state(self, node_id):
        return self._node_boxes_open.get(node_id, True)
    
    def _add_context_params(self, context):
        proc_uid = context['proc_uid']
        node_id = proc_uid[:-1]
        node_box = self._node_boxes.get(node_id)
        if node_box is None:
            node_box = NodeBox(
                self.input_parent, 
                self, 
                node_id, 
                open=self.get_default_node_groupe_state(node_id)
            )
            self.input_layout.addWidget(node_box)
            self._node_boxes[node_id] = node_box
        node_box.add_context(context)
        
        for up_context in context['up_contexts']:
            self._add_context_params(up_context)
            
    def set_proc(self, proc_id, context=None):
        '''
        Set the current proc and the context to display.
        If context is None, a new one is fetched.
        '''
        self.clear()
        context = context or get_execution_context(self.client, proc_id, None)
        self.load_context(context)
    
    def set_param(self, proc_uid, param_name, value):
        if not self._context:
            raise Exception('Cannot set param without execution context.')

        param_to_set = None
        for param in self._context['params']:
            if param['name'] == param_name:
                param_to_set = param
                break
            
        if param_to_set is None:
            raise Exception('Cannot set input %r: not present in execution context'%(param_name,))
        param_to_set['value'] = value
    
    def proc_count(self):
        return sum(
            len(p['processes'])
            for p in self._context['passes']
        )

    def do_round_trip(self):
        context = get_execution_context(self.client, self.proc_id, self._context)
        self.load_context(context)

    def _acceptable_worker_documents(self):
        '''
        Returns a list of acceptable value for the worker document
        in order for the execution to be runnable.
        A value of None means 'any document will be fine'.
        '''
        context_docs = list(self._context['all_documents'])
        print '  ', context_docs, '<-->', self.workers_table.get_current_document()
        if len(context_docs) > 1:
            # Multiple documents requires a free worker:
            return [None] # must be Free
        else:
            return context_docs # must match this doc

    def _check_selected_worker_features(self):
        print '  ', self._context['depth_needed_features'], 'in', self.workers_table.get_current_features()
        return (
            self.workers_table.get_current_id() is not None 
            and 
            set(self._context['depth_needed_features']).issubset(
                self.workers_table.get_current_features()
            )
        )
    
    def _check_selected_worker_document(self):
        if self.workers_table.get_current_id() is None:
            return False

        wdoc = self.workers_table.get_current_document()
        if not wdoc:
            wdoc = None
        print 'check selected doc, having', wdoc, 'needing', self._context['all_documents']
        if wdoc is None:
            return True
        
        for doc in self._context['all_documents']:
            if doc != wdoc:
                return False
        
        return True
    
    def _check_selected_worker_status(self):
        return (
            self.workers_table.get_current_id() is not None 
            and
            self.workers_table.get_current_status() == 'Waiting'
        )
        
    def can_submit_context_execution(self):
        return (
            self._context['depth_allow_exec']
            and
            self._check_selected_worker_features()
            and 
            self._check_selected_worker_document()
            and 
            self._check_selected_worker_status()
        )
        
    def execute(self):
        return execute_proc(self.client, self.proc_id, self._context, self.workers_table.get_current_id())
        
class ProcExecDialog(QtGui.QDialog):
    def __init__(self, parent, client):
        super(ProcExecDialog, self).__init__(parent)
        
        self.setLayout(QtGui.QVBoxLayout())
        
        self.pep = ProcExecPanel(self, client)
        self.pep.context_updated.connect(self._on_context_update)
        self.layout().addWidget(self.pep)

        buttons_layout = QtGui.QHBoxLayout()
        self.layout().addLayout(buttons_layout)
        
        self.execute_button = QtGui.QPushButton('Execute', self)
        self.execute_button.clicked.connect(self.execute)
        buttons_layout.addWidget(self.execute_button)

        b = QtGui.QPushButton('Close', self)
        b.clicked.connect(self.close)
        buttons_layout.addWidget(b)

    def keyPressEvent(self, event):
        # Eat the Return and Enter key event emited when
        # a line edit receives the key.
        # It suck we have to do this, but dealing with setDefault(False)
        # on all button is a PITA :/
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            event.accept()
            return

        super(ProcExecDialog, self).keyPressEvent(event)

    def exec_for_proc(self, proc_id, context=None):
        self.pep.set_proc(proc_id)
        super(ProcExecDialog, self).exec_()
        
    def _on_context_update(self):
        if self.pep.can_submit_context_execution():
            self.execute_button.setEnabled(True)
            self.execute_button.setText('Execute')
        else:
            self.execute_button.setText('Not Ready')
            self.execute_button.setEnabled(False)
            
    def execute(self):
        self.accept()
        self.pep.execute()
    
    def about_to_be_destroyed(self):
        self.pep.about_to_be_destroyed()
        