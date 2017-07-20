'''


'''
import os

from kabaret.flow import Flow
from kabaret.flow.case import CaseData


class DBCaseData(CaseData):
    '''
    This CaseData uses a collection from the DB app
    to persist data.
    
    The root instance must have its collection set with
    set_DB_colletion(). This collection will be passed on 
    to sub instances.
    '''
    
    def __init__(self, node_uid, node_type_names, sub_path=(), creator=None):
        super(DBCaseData, self).__init__(node_uid, node_type_names, sub_path, creator=creator)
        self._DB_collection = creator and creator._DB_collection or None

    def set_DB_collection(self, collection):
        if self._DB_collection is not None:
            raise Exception('The DB Collection is already set and cannot be overriden.')
        self._DB_collection = collection
        
    def ensure_exists(self):
        self._DB_collection._ensure_exists()
                    
    def load(self):
        self._doc = self._DB_collection.get_doc(
            self.get_mandatory_doc()
        )
                        
    def save(self):
        self._DB_collection.set_doc(self._doc)
                
    def find_cases(self, type_name, under_uid=None, sub_paths=[], **where):
        where.update({
            '_id': ('$under', under_uid),
            'type_names': ('$has', type_name),
        })
        return self._DB_collection.find(sub_paths, **where)
            

class ProjectFlow(Flow):
    '''
    The ProjectFlow gives access to the FLOW app's linked apps (USERS,
    DB, CMDS, NAMING, etc...) to the nodes it contains.
    
    It also notifies the FLOW app when a param is modified.
    
    The ProjectFlow is able to generate named (naming.path.PathItem)
    for the nodes in its root and trigger a callback when a node's
    param is modified.
    
    One must call the set_named_store() method before any
    call to the get_named() method.
    
    Use the set_on_param_touched_func()
    to set the function to call whenever a node param is touched. 
    The given function must accept a single argument: 
    the ParamValue that has been modified or touched.
    
    '''
    
    def __init__(self, project_name):
        super(ProjectFlow, self).__init__(project_name)
        self.named_store = None
        self._system_cmds_app = None
        self._users_app = None

    def set_named_store(self, store):
        self.named_store = store
        
    def get_named_store(self, store_path):
        return self.named_store
        
    def get_named(self, naming_config):
        named = self.named_store(**naming_config)
        return named
    
    def set_on_param_touched_func(self, func):
        self._on_param_touched_func = func
        
    def on_param_touched(self, param_value):
        super(ProjectFlow, self).on_param_touched(param_value)
        if self._on_param_touched_func is not None:
            self._on_param_touched_func(param_value)
    
    def set_system_cmds_app(self, app):
        self._system_cmds_app = app
        
    def get_client_system_cmd(self, station_class, cmd_id):
        if self._system_cmds_app is None:
            return None
        return self._system_cmds_app.cmds.GetClientCmd(station_class, cmd_id)

    def set_users_app(self, app):
        self._users_app = app
    
    def get_users_app(self):
        return self._users_app
    