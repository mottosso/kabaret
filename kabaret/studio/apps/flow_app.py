tmp = '''




#  ----> init 29 seq with 99 shot each:

set_param = client.apps.FLOW.cmds.SetParamValue
shot_ids = [ 'P%03d'%(i+1,) for i in range(99) ]
for seq in [ 'S%02d'%(i+1,) for i in range(29) ]:
  pid = ('Project', 'work', 'films:FILM', 'seqs:'+seq, '.shot_ids')
  set_param(pid, shot_ids)

# -----> create shot case by setting anim.work_days to 2:
set_param = client.apps.FLOW.cmds.SetParamValue
shot_ids = [ 'P%03d'%(i+1,) for i in range(99) ]
for seq in [ 'S%02d'%(i+1,) for i in range(29) ]:
    for shot in shot_ids:
      pid = ('Project', 'work', 'films:FILM', 'seqs:'+seq, 'shots:'+shot, 'anim', '.work_days')
      set_param(pid, 2)


  
'''


import traceback
import time, datetime
import os
import collections

from kabaret.core import utils
from kabaret.core.apps.base import App
from kabaret.core.events.event import Event
from kabaret.core.conf import Config, Group, Attribute, ConfigError

from kabaret.flow.relations.many import _CaseProducer

from ..flow import DBCaseData, ProjectFlow

#
#    SETTINGS
#
class FlowAppSettings(Config):
    '''
    The Flow App Configuration.
    
    '''
    EXTRA_CONTEXT = {
    }
    
    def _define(self):
        self.ROOT_CLASS = Attribute(
            None,
            '''
            The class to use as root in the Flow.
            It must be a subclass of kabaret.flow.node.Node
            '''
        )
        self.CASE_CLASS = Attribute(
            None,
            '''
            The class to use as case for the project.
            It must be a subclass of kabaret.studio.flow.case.DBCaseData
            with the same constructor signature.
            '''
        )
        self.FLOW_CLASS = Attribute(
            None,
            '''
            The Flow class to use for the project.
            It must be a subclass of kabaret.studio.flow.project.ProjectFlow
            Set to None to use the default (kabaret.studio.flow.project.ProjectFlow).
            '''
        )
            
         
#
#    APP
#
class FlowIdError(ValueError):
    pass

class FlowApp(App):
    APP_KEY = 'FLOW'
    REQ_APPS = ['DB', 'NAMING', 'USERS', 'CMDS', 'VERSIONS']
    
    def __init__(self, host):
        super(FlowApp, self).__init__(host)
        self.flow = None
        self.cases = None
        self.root_class = None
        self.case_class = DBCaseData
        self.flow_class = ProjectFlow
        
    def _get_setting_context(self):
        return {
            'project_name' : self.host.project_name,
            'store_path' : self.host.station_config.store_path,
            'station_class' : self.host.station_config.station_class,
            'APP': self,
        }
        
    def _get_setting_class(self):
        return FlowAppSettings
    
    def _apply_settings(self, settings):
        root_class = settings.ROOT_CLASS
        if root_class is None:
            raise ConfigError('The ROOT_CLASS is not defined in FLOW settings.')
        self.root_class = root_class
            
        case_class = settings.CASE_CLASS
        if case_class is not None:
            self.case_class = case_class
        if not issubclass(self.case_class, DBCaseData):
            print (
                'WARNING: The CaseData class %r defined in the setting is not '
                'a subclass of %r. Use at your own risks.'%(
                    self.case_class, DBCaseData
                )
            )
            
        flow_class = settings.FLOW_CLASS
        if flow_class is not None:
            self.flow_class = flow_class
                
        print '#------- Flow Class %s (root:%s, case type:%s)'%(
            self.flow_class, self.root_class, self.case_class
        )
        
    def _host_init_done(self):
        print '#---   Initializing Flow'

        project_name = self.host.project_name
        
        #----- Configure the App
        self.batch_temp_path = os.path.join(
            self.host.get_project_dir('LOGS'),
            'FlowBatch',
            utils.get_user_name()
        )

        #----- Init and configure the flow instance
        self.flow = self.flow_class(project_name)
        
        # callbacks
        self.flow.set_on_param_touched_func(self._on_param_touched)
        
        # naming
        self.flow.set_named_store(self.NAMING.get_root('STORE'))
        self.flow.set_root_class(self.root_class)
        
        # system cmds
        self.flow.set_system_cmds_app(self.CMDS)
        
        # users
        self.flow.set_users_app(self.USERS)
        
        # root case, using db 
        project_case = self.case_class(('Project',), self.root_class.type_names())
        collection = self.DB.get_collection(
            'FLOW.'+self.root_class.__name__, ['type_names', '_id']
        )
        project_case.set_DB_collection(collection)
            
        project_case.load()
        
        #----- Init root node
        root = self.flow.init_root(project_case, 'Project')
        print '  Ok. (root: %r)'%(root,)
            
    def _on_param_touched(self, param_value):
        '''
        Sends an 'INVALIDATED' Event with the id
        of param_value and no data (None).
        '''
        event = Event(
            self.APP_KEY,
            param_value.uid(),
            Event.TYPE.INVALIDATED,
            None
        )
        self.emit_event(event)
        
    def get_node(self, node_uid):
        return self.flow.get(node_uid)

    def get_node_type(self, node_uid):
        return self.flow.get_type(node_uid)
    
    def get_param(self, param_uid):
        return self.flow.get(param_uid)
    
    def arrange_param_ui_infos(self, param_ui_infos_list):
        param_ui_infos_list.sort(cmp=lambda a,b:cmp(a['index'], b['index']))

        # group by group and find each group higher index
        group_indexes = collections.defaultdict(int)
        grouped = collections.defaultdict(list)
        for i in param_ui_infos_list:
            group = i['group']
            grouped[group].append(i)
            group_indexes[group] = max(i['group_index'], group_indexes[group])
        
        # build an orderer grouped list: ((group, (info, info)), (group, (info, info)), ...)
        sorted_groups = sorted([ (v, k) for k, v in group_indexes.items() ])
        ret = []
        for i, group in sorted_groups:
            ret.append((group, grouped[group]))
        
        return tuple(ret)

    def get_kababatch(self):
        '''
        Returns the kababatch executable, env and additional env
        needed to run a kababatch with kabaret.core.syscmd.run
        '''
        return utils.get_kababatch_script(), None, {}

#
#    APP Commands
#
from kabaret.core.apps.command import Command, CommandError, Arg

class FLowCommandError(CommandError):
    pass

class FlowCommand(Command):
    def run(self):
        self.app.flow.tick()
        return super(FlowCommand, self).run()

@FlowApp.cmds.register
class GetRootId(FlowCommand):
    def doit(self):
        return self.app.get_node([]).uid()
    
@FlowApp.cmds.register
class GetRootChildren(FlowCommand):
    def doit(self):
        root = self.app.get_node([])
        return [ c.uid() for _, c in root.iterchildren() ]
    
#@FlowApp.cmds.register
#class GetClass(FlowCommand):
#    '''
#    Returns the name of the class of the given node or param.
#    '''
#    id=Arg()
#    def doit(self):
#        node_type = self.app.get_node_type(self.id)
#        return node_type.__name__
    
@FlowApp.cmds.register
class GetNodeRelations(FlowCommand):
    '''
    Returns a mapping {relation_type_name: relation_name}.
    If the Arg 'child_nodes' is not True, the ChildNode relations are excluded
    from the returned mapping.
    '''
    node_id=Arg()
    child_nodes=Arg()
    proc_nodes=Arg()
    def doit(self):
        node_type = self.app.get_node_type(self.node_id)
        ret = collections.defaultdict(list)
        
        index_cmp = lambda a,b: cmp(a.index, b.index)
        
        for relation in sorted(node_type.iterrelations(), cmp=index_cmp):
            ret[relation.__class__.__name__].append((relation.name, relation.node_type.ui_infos()))
            
        if self.child_nodes:
            for relation in sorted(node_type.iterchildrelations(), cmp=index_cmp):
                ret['Child'].append((relation.name, relation.node_type.ui_infos()))
                
        if self.proc_nodes:
            for relation in sorted(node_type.iterprocrelations(), cmp=index_cmp):
                ret['Proc'].append((relation.name, relation.node_type.ui_infos()))
                
        return dict(ret)
        
@FlowApp.cmds.register
class GetTypeUiInfos(FlowCommand):
    '''
    Returns ui infos for the type of the given node id.
    If the extended command argument is True, more data 
    are returned (doc...).
    '''
    node_id=Arg()
    extended=Arg(True)
    def doit(self):
        node_type = self.app.get_node_type(self.node_id)
        infos = node_type.ui_infos()
        if self.extended:
            infos['doc'] = node_type.doc()
        return infos

@FlowApp.cmds.register
class GetTypeParamUiInfos(FlowCommand):
    '''
    Returns a list of param ui infos for the type of the given node id.
    '''
    node_id=Arg()
    def doit(self):
        node_type = self.app.get_node_type(self.node_id)
        
        ret = [
            param.ui_infos() for param in node_type.iterparams()
        ]
        
        return self.app.arrange_param_ui_infos(ret)

@FlowApp.cmds.register
class GetTypeProcUiInfos(FlowCommand):
    '''
    Returns a list of related Proc ui infos for the type of the given node id.
    '''
    node_id=Arg()
    def doit(self):
        node_type = self.app.get_node_type(self.node_id)
        
        index_cmp = lambda a,b: cmp(a.index, b.index)
        ret = [
            (relation.name, relation.node_type.ui_infos())
            for relation in sorted(node_type.iterprocrelations(), cmp=index_cmp)
        ]

        return ret

@FlowApp.cmds.register
class GetParamValue(FlowCommand):
    '''
    Returns the value of the given param.
    '''
    param_id=Arg()
    def doit(self):
        param = self.app.get_param(self.param_id)
        return param.get()

@FlowApp.cmds.register
class GetParamUiInfos(FlowCommand):
    '''
    Returns a list of param ui infos (a dict like {'editor':<str>, 'group':<str>, 'index':<int>})
    If the 'param_name' argument is None, all params in the node are returned.
    '''
    node_id=Arg()
    param_name=Arg()
    def doit(self):
        node = self.app.get_node(self.node_id)
        if isinstance(node, _CaseProducer):
            node = node.parent_node
        if self.param_name is None:
            ret = [
                param.ui_infos(node) for param in node.iterparams()
            ]
        else:
            ret = [ node.get_param(self.param_name).ui_infos(node) ]
        
        return self.app.arrange_param_ui_infos(ret)

@FlowApp.cmds.register
class GetCaseIds(FlowCommand):
    '''
    Returns a list of case ids for the given relation in the
    given node
    '''
    node_id=Arg()
    relation_name=Arg()
    def doit(self):
        node = self.app.get_node(self.node_id)
        relation = node.get_relation(self.relation_name)
        return relation.get_related_ids(node)
    
@FlowApp.cmds.register
class SetParamValue(FlowCommand):
    '''
    Sets the value of the given param.
    '''
    param_id=Arg()
    value=Arg()
    def doit(self):
        param_name = self.param_id[-1][1:]
        node_id = self.param_id[:-1]
        node = self.app.get_node(node_id)
        node.get_param_value(param_name).set(self.value)

@FlowApp.cmds.register
class LoadAll(FlowCommand):
    '''
    Recursively instantiates all the related node of the given
    one.
    
    If the given node_id is None, the root node is used.
    '''
    node_id=Arg()
    def doit(self):
        node = self.app.get_node(self.node_id)
        node.load_related(depth=True)
        
        
@FlowApp.cmds.register
class DropNode(FlowCommand):
    '''
    Drops this node from its parent so that next access
    to its uid will create a new instance.
    
    If called on the root node, nothing is done.
    '''
    node_id=Arg()
    def doit(self):
        parent_uid = self.node_id[:-1]
        
        if not parent_uid:
            return
        
        parent = self.app.get_node(parent_uid)
        parent.drop_related(self.node_id[-1])

@FlowApp.cmds.register
class PrepareProcExec(FlowCommand):
    '''
    Returns execution context data describing the tasks to run
    to execute the given ProcNode.
    
    If the context argument is not None it must contain
    data used to pre-configure the returned context.
    '''
    proc_id=Arg()
    context=Arg()
    def doit(self):
        proc_node = self.app.get_node(self.proc_id)
        
        context = proc_node.prepare(self.context)
        
        return context.to_dict()
        
@FlowApp.cmds.register
class ProcExec(FlowCommand):
    '''
    Executes the ProcNode using the given context and worker.
    
    If worker_id is None and some features are required by the
    execution context, one is looked up.
    If worker_id is None and no features are required, the worker
    will be None.
    
    '''
    proc_id = Arg()
    context = Arg()
    worker_id = Arg()
    def doit(self):
        proc_node = self.app.get_node(self.proc_id)
        
        context = proc_node.get_execution_context_from_dict(self.context)
        if self.worker_id is None:
            features = context.get_needed_features()
            print 'worker look up for features', features
            if features:
                worker = self.app.host.find_worker_featuring(features)
            else:
                worker = None
        else:
            worker = self.app.host.get_worker(self.worker_id)
            if worker is None:
                raise CommandError('Cannot find a worker with id %r'%(self.worker_id,))
            if not worker.check_connected():
                raise CommandError('The worker with id %r is not connected!'%(self.worker_id,))
            
        return proc_node.execute(self.context, worker)
        
        
#@FlowApp.cmds.register
#class TestWorker(FlowCommand):
#    '''
#    Just testing...
#    '''
#    features = Arg([])
#    def doit(self):
#        worker = self.app.host.find_worker_featuring(*self.features)
#        if worker is None:
#            return '<worker not found>', None
#        
#        return repr(worker), worker.execute('v = 8'), worker.evaluate('v+v')

        
@FlowApp.cmds.register
class GetNodeTypeNames(FlowCommand):
    '''
    Return a list of (type_name, icon) used under the
    'under' uid.
    If the argument 'case_nodes_only' is True, only
    the node type used in a Many or One relation are
    returned (those are the node holding a Case)
    '''
    case_nodes_only=Arg()
    under=Arg()
    def doit(self):
        under = self.app.get_node_type(self.under or ())
        ret = under.collect_types(
            exclude_children=self.case_nodes_only,
            visit_children=True,
        )
        
        return sorted(
            (node_type.type_name(), node_type.ICON_NAME) 
            for node_type in ret
        )
        

@FlowApp.cmds.register
class GetCaseAttributes(FlowCommand):
    '''
    Return a list of possible attribute
    names for the given node type name.
    ''' 
    type_name=Arg()
    under=Arg()
    def doit(self):
        under = self.app.get_node_type(self.under or ())
        comp = lambda a, b: cmp(a.split('.'), b.split('.'))
        return sorted(
            under.collect_case_attributes(self.type_name),
            cmp=comp
        )

@FlowApp.cmds.register
class CollectParams(FlowCommand):
    '''
    Returns a list of param uid having at least one
    of the given tags in the given node and its children
    '''
    node_id=Arg()
    tags=Arg()
    def doit(self):
        if self.node_id is None:
            raise CommandError('CollectParams argument "node_id" cannot be None.')
        node = self.app.get_node(self.node_id)

        try:
            uids = node.collect_params(*self.tags)
        except TypeError:
            raise CommandError('CollectParams argument "tags" must be iterable.')
        
        return uids
    
@FlowApp.cmds.register
class FindCases(FlowCommand):
    '''
    Returns all uids of Nodes under the uid 'under' having 
    a type 'type_name' and a case matching every clauses in the 
    'where' dict.
    The 'where' dict may be like:
    {
        'some_param': 'The value to have',
        'child.param': True,
        'other_param': ('acceptable', 'values'),
    }
    
    '''
    type_name=Arg()
    under = Arg()
    where=Arg()
    sub_paths=Arg()
    def doit(self):
        under = self.app.get_node(self.under or []) # default is root node
        uids = under.find(self.type_name, sub_paths=self.sub_paths, **self.where or {})
                    
        #print '-------  FIND UNDER ROOT', self.type_name
        #for uid in uids:
        #    print uid
        return uids
        
