
import traceback

from kabaret.core.apps.base import App
from kabaret.core.conf import Config, Group, Attribute

from kabaret.naming import FileOrFolder

#
#    SETTINGS
#
class NamingAppSettings(Config):
    '''
    The naming App Configuration.
    
    Use this configuration file to define the PathItem classes
    instances available as root in the app. 
    
    Example:
    import proj_naming
    STORE_PATHITEM_CLASS = proj_naming.StoreFolder
    EXTRA_ROOTS = {
        'RootName': proj_naming.RootPathItem.from_name(store_path)
    }
    
    All the project's shape items will be available as children
    of the STORE_PATHITEM_CLASS instance. Use the shape item
    name as root_name in the NamingApp.get_root() method:
        log_path = naming_app.get_root('LOGS')
        
    You (in your apps) can declare additional root items 
    using NamingApp.set_root():
        root_name = naming_app.set_root('local_temp', local_temp_path_item)
        # root_name == 'local_temp'
    
    You can use those variable here:
        project_name:  the name of the project
        store_path:    the store path for the project
        station_class: the name of the staion class (Windows-7, Linux, etc...)
        APP:           the SYSCMD app loading this configuration
    
    NB: if STORE_PATHITEM_CLASS is None, a FileOrFolder will be used.
    '''
    EXTRA_CONTEXT = {
    }
    
    def _define(self):
        self.STORE_PATHITEM_CLASS = Attribute(
            None,
            '''
            The PathItem class to use for the store folder. It must
            handle all the path in the project shape.
            '''
        )
        self.EXTRA_ROOTS = Attribute(
            {},
            '''
            Map of root_name:extra_PathItem_instances to use (see kabaret.apps.naming)
            '''
        )        
            
            
#
#    APP
#
class NamingApp(App):
    APP_KEY = 'NAMING'
    
    def __init__(self, host):
        super(NamingApp, self).__init__(host)
        self._roots = {} # id to path item
        self.store_class = FileOrFolder
        
    def _get_setting_context(self):
        return {
            'project_name' : self.host.project_name,
            'store_path' : self.host.station_config.store_path,
            'station_class' : self.host.station_config.station_class,
            'APP': self,
        }
        
    def _get_setting_class(self):
        return NamingAppSettings
    
    def _apply_settings(self, settings):
        store_class = settings.STORE_PATHITEM_CLASS
        if store_class is not None:
            self.store_class = store_class
        
        store_path = self.host.station_config.store_path
        named_store = self.store_class.from_name(store_path)
        named_store.raise_wild()
        self.set_root('STORE', named_store)

        spl = len(store_path)
        for key, path in self.host.station_config.project_dirs.items():
            if not path.startswith(store_path):
                raise Exception(
                    '/!\\ Project path %r not under store (%r) ?!? /!\\'%(
                        path, store_path
                    )
                )
            path = path[spl:].lstrip('/')
            print '#------- adding root', key, path
            named_path = named_store / path
            if named_path.is_wild():
                print '    /!\\ WARNING: path is wild:', named_path.path()
                if 0:
                    print '   ', path, named_path.why()
            elif named_path.isfile():
                continue

            print '    ->', named_path.__class__.__name__
            self.set_root(key, named_path)
            
        excluded_shape_dirs = ('PROJ_SETTINGS',)
        for name, path_item in settings.EXTRA_ROOTS:
            if name not in excluded_shape_dirs:
                self.set_root(name, path_item)

    def _host_init_done(self):
        print '#---   Initializing Naming App'
        print '  Store item class:', self.store_class
        if 1:
            import pprint
            print '#--- NAMED ROOTS:'
            pprint.pprint(dict([ (k, i.path()) for k, i in self._roots.items() ]))
        
    def get_root(self, root_name):
        root = self._roots.get(root_name, None)
        if root is None:
            raise RootNameError('Cannot find root path item with name %r'%(root_name,))
        return root

    def set_root(self, root_name, path_item):
        try:
            self._roots[root_name] = path_item
        except Exception, err:
            raise RootNameError('Could not add root path item with name %r: %s'%(root_name, err))
        return root_name


#
#    APP Commands
#
from kabaret.core.apps.command import Command, CommandError, Arg

class NamingCommandError(CommandError):
    pass


class RootNameError(NamingCommandError):
    pass

@NamingApp.cmds.register
class GetPath(Command):
    '''
    Returns the string path of the given naming config
    under the given root.
    '''
    root_name=Arg()
    config=Arg()
    def doit(self):
        try:
            return self.app.get_root(self.root_name).to_config(
                self.config
            ).path()
        except Exception, err:
            traceback.print_exc()
            raise NamingCommandError(
                'There was an error: %s\n(see the AppHost output for the trace.)'%(
                    err,
                )
            )

@NamingApp.cmds.register
class GetConfig(Command):
    '''
    Returns the config of 'path' relative to the root path item
    named 'root_name'.
    
    If 'root_name' is None, the class of the 'STORE' root item
    is used to create a temporary root and use it here.
    '''
    
    root_name=Arg()
    path=Arg()
    def doit(self):
        if self.root_name is not None:
            root = self.app.get_root(self.root_name)
            relative_to = root
            named_path = root / self.path
        else:
            root_path, path = self.path.split(self.app.store_class.SEP, 1)
            relative_to = self.app.store_class.from_name(root_path)
            named_path =  relative_to/path
        return named_path.config(relative_to=relative_to)

@NamingApp.cmds.register
class GetKeysFor(Command):
    root_name=Arg()
    type_name=Arg()
    def doit(self):
        try:
            return self.app.get_root(self.root_name).get_keys_for(
                self.type_name
            )
        except Exception, err:
            traceback.print_exc()
            raise NamingCommandError(
                'There was an error: %s\n(see the AppHost output for the trace.)'%(
                    err,
                )
            )

@NamingApp.cmds.register
class GetRootNames(Command):
    def doit(self):
        return sorted(self.app._roots.keys())
    
