
import os
import subprocess
import collections
import pprint

from kabaret.core.apps.base import App
from kabaret.core.conf import Config, Group, Attribute

#
#    SETTINGS
#
class CmdInfos(object):
    def __init__(self, cmd_id, path, label=None, icon=None, groups=[]):
        '''
        This class is a helper to collect cmd info in settings.
        It is quite dumb for now but it may someday provide
        kool stuffs like 'find_app_by_name('Maya*')
        
        '''
        super(CmdInfos, self).__init__()
        self.cmd_id = cmd_id
        self.path = path
        self.label = label
        self.icon = icon
        self.groups = groups

class SystemCmdsSettings(Config):
    '''
    The SystemCmds App Configuration.
    
    Use this configuration file to define all the system commands
    available to Kabaret.
    
    Each commands is declared with a call to register().
    (see examples below)

    A command contains a name, a station_class and an executable path.
    It may have a label, an icon, and a list of group names which are
    used in user interfaces only.
    It can also have an 'env' dict to override the system environment or
    an 'additional_env' dict to add to (or modify) the system environment.
    
    By default, the command can run on the app host and on the client.
    To disallow client side execution, set the 'client_exec' argument to False.
    
    Some command may spawn a worker that will connect to the apphost.
    Those command must be registered with the 'is_worker' argument set to True
    in order to let the user run them in contexts needing a worker.
    
    Examples:

        #
        # Simple call to an executable, can run from AppHost and from Client, and
        # is usable as a worker:
        #
        register(
            'Maya', 'Windows-7', 'C:/Progam Files/Autodesk/Maya2013/bin/maya.exe',
            is_worker=True
        )
        
        #
        # Simple call to an executable, can't run from Client, is not a worker:
        #
        register(
            'Maya', 'Windows-7', 'C:/Progam Files/Autodesk/Maya2013/bin/maya.exe',
            client_exec=False
        )
        
        #
        # Call to an executable with altered environment:
        #
        register(
            'Maya', 'Windows-7', 'C:/Progam Files/Autodesk/Maya2013/bin/maya.exe',
            MAYA_SCRIPT_PATH = 'path/to/project/scripts;path/to/user/scripts',
            VRAY_FOR_MAYA2012_MAIN_x64 = "C:/Progam Files/vray",
            VRAY_FOR_MAYA2012_PLUGINS_x64 = "C:/Progam Files/vray/vrayplugins",
        )
        
        #
        # Preparing a more complex environment:
        #
        
        # Env:
        root_path = 'path/to/maya_stuffs'
        additional_env = {
            'MAYA_SCRIPT_PATH' : ';'.join(
                root_path+'/project/scripts'
                root_path+'path/to/user/scripts'
                )
        }
        if ALLOW_VRAY:
            additional_env['VRAY_FOR_MAYA2012_MAIN_x64'] = 'path/to/vray'
            additional_env['VRAY_FOR_MAYA2012_PLUGINS_x64'] = 'path/to/vray/vrayplugins'
        
        # Action:
        register(
            'Maya', 'Windows-7', 'C:/Progam Files/Autodesk/Maya2013/bin/maya.exe',
            **additional_env
        )
        
        #
        # Defining complex env using EnvSet
        #
        
        # The kabaret.core.syscmd.env_set package contains tool to 
        # define environments in a user friendly manner.
        # You may use it in your scripts (in the project or at the 
        # studio level) to pre-define envs and use them here:
        from kabaret.core.syscmd.env import SysSet, SetCollection
        import mystudio.maya.envsets as maya_envsets
        if USE_2013:
            maya_env = maya_envsets.Maya2013()
        else:
            maya_env = maya_envsets.Maya2012()
        register(
            'Maya', 'Windows-7', maya_env.vars.MAYA_BIN,
            **maya_env.items()
        )
            
            
    You can use those variable here:
        register(
            cmd_id, station_class, executable, 
            label=None, icon=None, groups=None,
            client_exec=True, is_worker=False, env=None,
            **additional_env
        ):             the function to call to register a new command
        project_name:  the name of the project
        store_path:    the store path for the project
        station_class: the name of the app host station class (Windows-7, Linux, etc...)
        apphost_url:   the url of the apphost.
    '''
    
    def _define(self):
        pass
    
#
#    APP
#
class SystemCmdsApp(App):
    APP_KEY = 'CMDS'
    
    def __init__(self, host):
        super(SystemCmdsApp, self).__init__(host)
        self._class_cmds = {} # [station_class][cmd_id] -> cmd_infos
        self.host_station_class = self.host.station_config.station_class,
        
    def add_sys_cmd(self,
        cmd_id, station_class, executable, 
        label=None, icon=None, groups=None,
        client_exec=True, is_worker=False, env=None,
        **additional_env
    ):
        if station_class not in self._class_cmds:
            self._class_cmds[station_class] = {}

        self._class_cmds[station_class][cmd_id] = {
            'executable': executable,
            'label': label or cmd_id,
            'icon': icon,
            'groups': groups or ['Others'],
            'client_exec': client_exec,
            'is_worker': is_worker,
            'env': env,
            'additional_env': additional_env,
        }
            
    def _get_setting_context(self):
        try:
            host_url = self.host.url
        except:
            host_url = None # the url does not exist if the apphost is not a remote object (local instance)
        return {
            'register': self.add_sys_cmd,
            'project_name' : self.host.project_name,
            'store_path' : self.host.station_config.store_path,
            'station_class' : self.host_station_class,
            'apphost_url': host_url,
        }
        
    def _get_setting_class(self):
        return SystemCmdsSettings
    
    def _apply_settings(self, settings):
        # everything is done by the setting 'register' object.
        pass
#        for i in settings.COMMANDS:
#            if isinstance(i, CmdInfos):
#                self._cmds[i.cmd_id] = RunCmd(
#                    label=i.label, path=i.path, icon=i.icon, groups=i.groups
#                )
#            else:
#                try:
#                    cmd_id, cmd = i
#                except:
#                    raise ValueError(
#                        'Invalid value %r in %r.settings.COMMANDS'%(
#                            i, self.APP_KEY
#                        )
#                    )
#                self._cmds[cmd_id] = cmd

    def _host_init_done(self):
        print '#---   Initializing System Cmds'
        for station_class, cmds in self._class_cmds.iteritems():
            print ' ', station_class+':'
            for name, data in cmds.iteritems():
                print '   ', name,
                if data['is_worker']:
                    print '(worker)'
                else:
                    print

    def itercmds(self, station_class):
        return self._class_cmds.get(station_class,{}).iteritems()
    
    def get_cmd(self, cmd_id, station_class):
        return self._class_cmds.get(station_class, {}).get(cmd_id, None)
    
    def get_client_cmd(self, client_station_class, cmd_id):
        cmd = self.get_cmd(cmd_id, client_station_class)
        return cmd

    def get_host_cmd(self, cmd_id):
        cmd = self.get_cmd(cmd_id, self.host_station_class)
        return cmd
    

#
#    APP Commands
#
from kabaret.core.apps.command import Command, Arg
class CmdIdError(ValueError):
    pass

@SystemCmdsApp.cmds.register
class SysCmdRun(Command):
    '''
    Executes the given command from the AppHost, with
    the given string argument.
    '''
    cmd_id=Arg()
    args_str=Arg()
    def doit(self):
        cmd = self.app.get_host_cmd(self.cmd_id)
        if cmd is None:
            raise CmdIdError('Cannot find AppHost command with id %r'%(self.cmd_id,))
        print '>> EXECUTING SYSTEM COMMAND ON APPHOST:'
        pprint.pprint(cmd)
        print '<<'

@SystemCmdsApp.cmds.register
class GetClientCmdInfos(Command):
    '''
    Retuns a dict like {group_name: [cmd_infos, cmd_infos]}
    where cmd_infos has the keys ['id', 'label', 'icon']
    
    Only the command allowed to run on the client side are
    returned.
    
    The same command may appear once in each group.
    
    '''
    station_class = Arg()
    def doit(self):
        ret = collections.defaultdict(list)
        for cmd_id, cmd in self.app.itercmds(self.station_class):
            if not cmd['client_exec']:
                continue
            for group in cmd['groups']:
                ret[group].append({'id':cmd_id, 'label':cmd['label'], 'icon':cmd['icon']})
    
        return dict(ret)

@SystemCmdsApp.cmds.register
class GetWorkerCmdInfos(Command):
    '''
    Returns a list like [cmd_infos, cmd_infos]
    where cmd_infos has the keys ['id', 'label', 'icon']
    
    Only the command registered as worker for the given station_class
    are returned.
    
    '''
    station_class = Arg()
    def doit(self):
        ret = []
        for cmd_id, cmd in self.app.itercmds(self.station_class):
            if not cmd['is_worker']:
                continue
            ret.append({'id':cmd_id, 'label':cmd['label'], 'icon':cmd['icon']})
    
        return ret

@SystemCmdsApp.cmds.register
class GetClientCmd(Command):
    '''
    Returns a dict depicting the given command for 
    the given station_class.
    The dict is like:
        {
        cmd_id: <the id of the command>, 
        path: <the path of the executable>, 
        env: <the environment dict to use or None for inherited>,
        additional_env: <a dict of environment value to set>,
        }
        
    Only the command allowed to run on the client side can be
    returned.
    '''
    station_class = Arg()
    cmd_id = Arg()
    def doit(self):
        client_cmd = self.app.get_client_cmd(
            self.station_class,
            self.cmd_id
        )
        if client_cmd is None:
            raise CmdIdError(
                'Cannot find Client command with id %r for station class %r.'%(
                    self.cmd_id, self.station_class
                )
            )
        # NB: we copy the dicts here to avoid external modifications:
        return {
            'executable':   client_cmd['executable'],
            'env':   client_cmd['env'] and dict(client_cmd['env']) or None,
            'additional_env':   dict(client_cmd['additional_env']),        
        }
        
        
#@SystemCmdsApp.cmds.register
#class SysCmdList(Command):
#    group=Arg()
#    def doit(self):
#        fil = lambda x: True
#        if self.group is not None:
#            fil = lambda x, f=self.group: x.startswith(f)
#        
#        return [ cmd_id for cmd_id, cmd in self.app.itercmds() if fil(cmd.groups) ]


#
#    CMDS
#
class SysCmd(object):
    def __init__(self, label, path, icon=None, groups=[], client_enabled=True):
        super(SysCmd, self).__init__()
        self.client_enabled = client_enabled
        self.path = path
        self.label = label
        self.icon = icon
        self.groups = groups

        self.stdout = None
        self.stderr = None
        self.cwd = None
        self.wait = False
        self.popen = None
        
    def __call__(self, *args, **kwargs):
        self.run(*args, **kwargs)
        
    def run(self, args_str):
        raise NotImplementedError
    
    def _run_subprocess(self, command, *args, **subprocess_extra_kw_args):
        print '----->', command, args, subprocess_extra_kw_args
        stdout = self.stdout
        stderr = self.stderr
        
        if self.wait:
            self.popen = subprocess.call(
                [command]+list(args), stdout=stdout, stderr=stderr, cwd=self.cwd,
                **subprocess_extra_kw_args
            )
        else:
            self.popen = subprocess.Popen(
                [command]+list(args), stdout=stdout, stderr=stderr, cwd=self.cwd,
                **subprocess_extra_kw_args
            )

class RunCmd(SysCmd):
    def run(self, args_str):
        print 'RUN CMD', self.path, args_str
        self._run_subprocess(self.path)

class Explorer(RunCmd):
    def __init__(self):
        super(Explorer, self).__init__(
            label='Explorer', path=r'explorer.exe', 
            groups=['Apps/Utils']
        )

    def run(self, args_str):
        path_to_open = args_str
        last = None
        while last != path_to_open and not os.path.isdir(path_to_open):
            last = path_to_open
            path_to_open = os.path.dirname(path_to_open)
        if last == path_to_open:
            path_to_open = ''
        
        path_to_open = path_to_open.replace('/', '\\')
        self._run_subprocess(self.path, path_to_open)
        
class Calc(RunCmd):
    def __init__(self):
        super(Calc, self).__init__(
            label='Calculator', path=r'C:\Windows\system32\calc.exe', 
            groups=['Apps/Utils']
        )
        