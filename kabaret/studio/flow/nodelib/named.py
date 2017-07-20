
import os, stat

from kabaret.flow.nodes.node import Node
from kabaret.flow.nodes.proc import ProcNode

from kabaret.flow.params.param import Param, param_group
from kabaret.flow.params.computed import ComputedParam
from kabaret.flow.params.trigger import TriggerParam

from kabaret.flow.relations.child import Child
from kabaret.flow.relations.proc import Proc


class NamingNode(Node):
    in_naming = Param()
    config = Param({})
    out_naming = ComputedParam()

    def _configure(self):
        super(NamingNode, self)._configure()
        parent = self.parent()
        if not parent:
            raise Exception('NamingNode cannot be a root')
        
        # default config is class_name:node_id
        self.config.set({parent.__class__.__name__:parent.node_id})
        
        # output is for parent _naming:
        parent._naming.add_source(self.out_naming)
        
        # input is from grand parent naming, or empty
        gparent = parent.parent()
        if not gparent:
            self.in_naming.set({})
        elif not gparent.has_param('_naming'):
            self.in_naming.set({'Project':gparent.node_id})
        else:
            self.in_naming.add_source(gparent._naming)
    
    def param_touched(self, param_name):
        if param_name in ('in_naming', 'config'):
            self.out_naming.touch()
            
    def compute(self, param_name):
        if param_name == 'out_naming':
            cfg = dict(self.in_naming.get() or {})
            config = self.config.get()
            if config:
                # Update cfg and remove the key with None value:
                for k, v in config.items():
                    if v is None:
                        try:
                            del cfg[k]
                        except KeyError:
                            pass
                    else:
                        cfg[k] = v
            self.out_naming.set(cfg)

class NamedNode(Node):
    with param_group('_Naming', group_index=1000):
        _naming = Param()

    _namer = Child(NamingNode)

    def set_namer_config(self, **config):
        self._namer.config.set(config)
    
    def add_namer_config(self, **config):
        cfg = self._namer.config.get() or {}
        cfg.update(config)
        self._namer.config.set(cfg)
        
    def set_namer_from_id(self, key=None):
        key = key or self.__class__.__name__
        self._namer.config.set({key:self.node_id})

class BrowseCmdNode(ProcNode):
    NEEDED_FEATURES = ['kabaret']
    ICON_NAME = 'editor_proc' 

    filename = Param().tag('filename')
    folder = ComputedParam()
    existing_folder = ComputedParam()
    
    def _needs_to_run(self, ups_needs_to_run):
        # This proc is not intended to be dependent on 
        # upstream procs. It should run whenever requested:
        return True, 'By User Request'
    
    def param_touched(self, param_name):
        if param_name == 'filename':
            self.folder.touch()
            return

        if param_name == 'folder':
            self.existing_folder.touch()
            return

        super(BrowseCmdNode, self).param_touched(param_name)
        
    def compute(self, param_name):
        if param_name == 'folder':
            self.folder.set(
                os.path.dirname(self.filename.get() or '')
            )
            return
        
        if param_name == 'existing_folder':
            p = self.folder.get()
            deepest_folder = ''
            while p:
                if os.path.exists(p):
                    deepest_folder = p
                    break
                p, _ = os.path.split(p)
            self.existing_folder.set(p)
            return 
        
        super(BrowseCmdNode, self).compute(param_name)

    def validate_execution_context(self, context):
        folder = self.folder.get()
        existing_folder = self.existing_folder.get()
        if folder == existing_folder:
            context.allow_exec = True
            context.why = None
            return
        
        if not context.get_value('Open this instead', ''):
            context.set_param(
                'Open this instead',
                existing_folder,
                doc='''
The path %r does not exists, the deepest existing folder is %r.
(Clear the value to update the deepest existing folder)
                '''%(folder, existing_folder))
            
        if not context.has_param('Confirm'):
            context.set_param(
                'Confirm',
                False,
                editor='bool',
                doc='Check this to allow execution'
            )
            context.allow_exec = False
            context.why = 'Please confirm'
        else:
            if context.get_value('Confirm'):
                context.allow_exec = True
                context.why = 'Confirmed'
            else:
                context.allow_exec = False
                context.why = 'Please confirm'
            
    def process(self, context, worker):
        if context.has_param('Open this instead'):
            path = context.get_value('Open this instead')
        else:
            path = self.existing_folder.get()
        
        # Get the system command and its env:
        station_class = worker.get_station_class()
        cmd = self.flow().get_client_system_cmd(station_class, 'BROWSE')
        if 'window' in station_class.lower():
            path = path.replace('/', '\\')
        
        additional_env = cmd['additional_env']
        additional_env['KABARET_FOCUS_ID'] = repr(self.uid())
        
        # define a launcher function:
        def run_sys_cmd(executable, args, env, additional_env):
            import kabaret.core.syscmd
            cmd = kabaret.core.syscmd.SysCmd(
                executable, args, env, additional_env
            )
            cmd.execute()
            
        # trigger the launcher function on the worker
        with worker.busy():
            worker.send_func(run_sys_cmd)
            worker.call(
                'run_sys_cmd', 
                cmd['executable'], 
                [path], 
                cmd['env'], additional_env
            ) 

class FileNode(NamedNode):
    
    thumbnail = ComputedParam().tag('preview').ui(editor='thumbnail', group_index=-1, index=-1)
    
    with param_group('Previous File'):
        prev_filename = Param().tag('filename')
        prev_mtime = Param().ui(editor='timestamp')
        
    with param_group('File'):
        filename = ComputedParam().tag('filename')
        exists = ComputedParam()
        mtime = ComputedParam().ui(editor='timestamp')
        
    def set_prev_file(self, file_node):
        self.prev_filename.disconnect()
        self.prev_filename.add_source(file_node.filename)
        
        self.prev_mtime.disconnect()
        self.prev_mtime.add_source(file_node.mtime)

    browse = Proc(BrowseCmdNode)
    
    def _configure(self):
        super(FileNode, self)._configure()
        self.browse.filename.add_source(self.filename)
        self.set_ticked()

    def tick(self):
        '''
        Checks for mtime modifications and update it
        if needed.
        '''
        # Skip tick when it might come from a touch of the params used here:
        # (it could lead to a loop)
        if self.exists.is_dirty() or self.mtime.is_dirty() or self.filename.is_dirty():
            return
        
        # Check file existence first
        filename = self.filename.get()
        if not os.path.exists(filename):
            if self.exists.get():
                self.exists.touch()
            return
        elif not self.exists.get():
            self.exists.touch()
            return
        
        curr_mtime = self.mtime.get()
        real_mtime = os.stat(filename)[stat.ST_MTIME]   
        if real_mtime != curr_mtime:
            self.mtime.touch()
            
    def param_touched(self, param_name):
        if param_name == '_naming':
            self.filename.touch()
        elif param_name == 'filename':
            self.exists.touch()
            self.thumbnail.touch()
        elif param_name == 'exists':
            self.mtime.touch()
        else:
            super(FileNode, self).param_touched(param_name)
            
    def compute(self, param_name):
        if param_name == 'filename':
            config = self._naming.get()
            named = self.flow().get_named(config)
            self.filename.set(named.path())
            
        elif param_name == 'exists':
            filename = self.filename.get()
            if not filename:
                self.exists.set(False)
            else:
                self.exists.set(os.path.exists(filename))
        
        elif param_name == 'mtime':
            if not self.exists.get():
                self.mtime.set(0)
            else:
                filename = self.filename.get()
                self.mtime.set(
                    os.stat(filename)[stat.ST_MTIME]
                )

        elif param_name == 'thumbnail':
            dir, name = os.path.split(self.filename.get())
            thumbnail = os.path.join(dir, '.thumbnails', name+'.png')
            self.thumbnail.set(thumbnail)
            
                    