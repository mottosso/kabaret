'''

    A command line interface for the kabaret.core package.

'''

import sys
import os
import kabaret.core.cmdln as cmdln

ENV_DEFAULT_STORE = 'KABARET_STORE_PATH'

class KabAdmin(cmdln.Cmdln):
    '''Usage:
        {name} SUBCOMMAND [ARGS...]
        {name} help SUBCOMMAND
    
    blah...
    
    ${command_list}
    ${help_list}
    
    '''%({'name':'kabadmin'})
    
    class DEFAULTS:
        store = os.environ.get(ENV_DEFAULT_STORE, 'X:/TEST_STORE') 
        
    def __init__(self, *args, **kwargs):
        cmdln.Cmdln.__init__(self, *args, **kwargs)
        cmdln.Cmdln.do_help.aliases.append('h') #@UndefinedVariable from decorator

    @cmdln.alias('crpr')
    @cmdln.option(
        '-v', '--verbose', action='store_true',
        help='print extra information'
    )
    @cmdln.option(
        '-S', '--store', metavar='ARG',
        help='The store to use for the new project. Defaults to %r'%(DEFAULTS.store,)
    )
    @cmdln.option(
        '--shape-loader', metavar='ARG',
        help='optional. A command that register custom project shapes.'
    )
    @cmdln.option(
        '--shape-name', metavar='ARG',
        help='optional. The name of the project shape to use.'
    )
    def do_creproj(self, subcmd, opts, *args):
        '''Create a new project
        usage:
            creproj <project name>...
            
        The project must not exist yet.
        
        ${cmd_option_list}
        '''
        import kabaret.core.project
        import kabaret.core.project.log
        
        args = list(args) # make it popable
        try:
            project = args.pop(0)
        except IndexError:
            raise cmdln.CmdlnUserError('Missing project argument')
        if args:
            raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))
        
        if opts.store is None:
            print 'Using default store %r'%(self.DEFAULTS.store,)
            opts.store = self.DEFAULTS.store
                
        if opts.verbose:
            level = kabaret.core.project.log.INFO
            kabaret.core.project.log.setup(stdout_level=level)
        else:
            kabaret.core.project.log.setup() # use default level
                    
        try:
            kabaret.core.project.create(
                opts.store, project, opts.shape_name, opts.shape_loader
            )
        except Exception, err:
            msg = 'There was an error creating the project: %s'%(err,)
            if opts.verbose:
                import traceback
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            raise cmdln.CmdlnUserError(msg)

    @cmdln.alias('ps')
    @cmdln.option(
        '-v', '--verbose', action='store_true',
        help='print extra information'
    )
    @cmdln.option(
        '-S', '--store', metavar='ARG',
        help='The store to use for the new project. Defaults to %r'%(DEFAULTS.store,)
    )
    def do_projsettings(self, subcmd, opts, *args):
        import kabaret.core.project.log

        args = list(args) # make it popable
        try:
            project_name = args.pop(0)
        except IndexError:
            raise cmdln.CmdlnUserError('Missing project argument')
        if args:
            raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))
        
        if opts.store is None:
            print 'Using default store %r'%(self.DEFAULTS.store,)
            opts.store = self.DEFAULTS.store
                
        if opts.verbose:
            level = kabaret.core.project.log.INFO
            kabaret.core.project.log.setup(stdout_level=level)
        else:
            kabaret.core.project.log.setup() # use default level
                
        try:
            project = kabaret.core.project.project.Project(
                opts.store, project_name
            )
            print project.settings.pformat()
            
        except Exception, err:
            msg = 'There was an error accessing the project settings: %s'%(err,)
            if opts.verbose:
                import traceback
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            raise cmdln.CmdlnUserError(msg)
   
    @cmdln.alias('pc')
    @cmdln.option(
        '-v', '--verbose', action='store_true',
        help='print extra information'
    )
    @cmdln.option(
        '-S', '--store', metavar='ARG',
        help='The store to use for the new project. Defaults to %r'%(DEFAULTS.store,)
    )
    def do_projcheck(self, subcmd, opts, *args):
        import kabaret.core.project.check
        import kabaret.core.project.log

        args = list(args) # make it popable
        try:
            project_name = args.pop(0)
        except IndexError:
            raise cmdln.CmdlnUserError('Missing project argument')
        if args:
            raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))
        
        if opts.store is None:
            print 'Using default store %r'%(self.DEFAULTS.store,)
            opts.store = self.DEFAULTS.store
                
        if opts.verbose:
            level = kabaret.core.project.log.INFO
            kabaret.core.project.log.setup(stdout_level=level)
        else:
            kabaret.core.project.log.setup() # use default level
                
        try:
            project = kabaret.core.project.Project(
                opts.store, project_name
            )
            kabaret.core.project.check.check_project(
                project, kabaret.core.project.log.getLogger()
            )
            
        except Exception, err:
            msg = 'There was an error accessing the project settings: %s'%(err,)
            if opts.verbose:
                import traceback
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            raise cmdln.CmdlnUserError(msg)

    @cmdln.option(
        '-v', '--verbose', action='store_true',
        help='print extra information'
    )
    @cmdln.option(
        '-S', '--store', metavar='ARG',
        help='The store to use for the new project. Defaults to %r'%(DEFAULTS.store,)
    )
    def do_cli(self, subcmd, opts, *args):
        import kabaret.core.cmdln.apphost
        import kabaret.core.project.log
        
        args = list(args) # make it popable
        try:
            project_name = args.pop(0)
        except IndexError:
            raise cmdln.CmdlnUserError('Missing project argument')
        if args:
            raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))
        
        if opts.store is None:
            print 'Using default store %r'%(self.DEFAULTS.store,)
            opts.store = self.DEFAULTS.store
                
        if opts.verbose:
            level = kabaret.core.project.log.INFO
            kabaret.core.project.log.setup(stdout_level=level)
        else:
            kabaret.core.project.log.setup() # use default level
                
        try:
            project = kabaret.core.project.project.Project(
                opts.store, project_name
            )
            cli = kabaret.core.cmdln.apphost.CLAppHost(project)
            cli.run()
            
        except Exception, err:
            msg = 'There was an error running the project CLI: %s'%(err,)
            if opts.verbose:
                import traceback
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            raise cmdln.CmdlnUserError(msg)

    @cmdln.alias('serve')
    @cmdln.option(
        '-v', '--verbose', action='store_true',
        help='print extra information'
    )
    @cmdln.option(
        '-d', '--demonize', action='store_true',
        help='Demonize the server (run it in background)'
    )
    @cmdln.option(
        '-S', '--store', metavar='ARG',
        help='The store to use for the new project. Defaults to %r'%(DEFAULTS.store,)
    )
    def do_projserver(self, subcmd, opts, *args):
        '''Start serving the given project
        usage:
            projserver <project name>...
            
        The project must exist and have been checked.
        
        ${cmd_option_list}
        '''
        import kabaret.core.services.project
        import kabaret.core.project.log
        
        args = list(args) # make it popable
        try:
            project_name = args.pop(0)
        except IndexError:
            raise cmdln.CmdlnUserError('Missing project argument')
        if args:
            raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))
        
        if opts.store is None:
            print 'Using default store %r'%(self.DEFAULTS.store,)
            opts.store = self.DEFAULTS.store
                
        if opts.verbose:
            level = kabaret.core.project.log.INFO
            kabaret.core.project.log.setup(stdout_level=level)
        else:
            kabaret.core.project.log.setup() # use default level
                
        try:
            pserv = kabaret.core.services.project.ProjectServiceProcess(
                opts.store, project_name
            )
            pserv.start()
            run = True
            while run:
                a = raw_input('#>')
                a = a.strip()
                if a == 'q':
                    run=False
                elif a == '?':
                    print '? : help'
                    print 'q : quit'
            
            
        except Exception, err:
            msg = 'There was an error while serving the project: %s'%(err,)
            if opts.verbose:
                import traceback
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            raise cmdln.CmdlnUserError(msg)

    def do_apphost(self, subcmd, opts, *args):
        '''Start an app host for the given project
        usage:
            apphost <project name>
            
        The project service must be up and running.
        
        ${cmd_option_list}
        '''
        import kabaret.core.services.apphost
        
        args = list(args) # make it popable
        try:
            project_name = args.pop(0)
        except IndexError:
            raise cmdln.CmdlnUserError('Missing project argument')
        if args:
            raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))

        try:
            print 'Starting AppHost Process for project', project_name
            apphost_process = kabaret.core.services.apphost.AppHostServiceProcess(
                project_name
            )
            apphost_process.start()
            print 'AppHost is Running'

        except Exception, err:
            msg = 'There was an error while serving the project: %s'%(err,)
            if opts.verbose:
                import traceback
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            raise cmdln.CmdlnUserError(msg)

    @cmdln.option(
        '-S', '--store', metavar='ARG',
        help='The store to use for the service. Defaults to %r'%(DEFAULTS.store,)
    )
    @cmdln.option(
        '-P', '--project', metavar='ARG',
        help='The project to use for the service.'
    )
    @cmdln.option(
        '-l', '--local', action='store_true',
        help='use with "start u" to make the url service local.' 
    )
    @cmdln.option(
        '-v', '--verbose', action='store_true',
        help='print extra information'
    )
    def do_start(self, subcmd, opts, *args):
        '''Start a service
        usage:
            start <u|p|a>
            
        u: starts the url service.
        p: starts the project service, --project and --store required.
        a: starts an app host for the given project, --project required.
        
        If the service is already running, nothing is done.
        ${cmd_option_list}
        '''
        args = list(args) # make it popable
        try:
            service_type = args.pop(0)
        except IndexError:
            raise cmdln.CmdlnUserError('Missing service argument')

        if service_type not in 'upa':
            raise cmdln.CmdlnUserError('Bad service argument')
        
        try:
            if service_type == 'u':
                if args:
                    raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))
                print 'Starting Url Service'
                import kabaret.core.ro.url
                kabaret.core.ro.url.ensure_service(local=opts.local, new_process=False)
                
            elif service_type == 'p':
                if opts.project is None:
                    raise cmdln.CmdlnUserError('Missing -P or --project')
                if opts.store is None:
                    print 'Using default store %r'%(self.DEFAULTS.store,)
                    opts.store = self.DEFAULTS.store
                print 'Starting Project Service for', opts.project
                import kabaret.core.ro.project
                kabaret.core.ro.project.ensure_service(opts.store, opts.project)
                    
            elif service_type == 'a':
                if opts.project is None:
                    raise cmdln.CmdlnUserError('Missing -P or --project')
                import kabaret.core.ro.apphost
                print 'Ensuring Local AppHost Service exists for', opts.project
                kabaret.core.ro.apphost.ensure_service(opts.project, new_process=False)
        
        except KeyboardInterrupt:
            print 'Service Interrupted'
            
        except Exception, err:
            msg = 'There was an error while starting a service: %s'%(err,)
            if opts.verbose:
                import traceback
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            raise cmdln.CmdlnUserError(msg)

    @cmdln.option(
        '-l', '--local', action='store_true',
        help='Use the local url service.'
    )
    @cmdln.option(
        '-v', '--verbose', action='store_true',
        help='print extra information'
    )
    def do_url(self, subcmd, opts, *args):
        '''Operate with the url service
        usage:
            url list
            url rem <url>
            
        list: list the urls known by the service.
        rem: remove an url from the service.
        
        ${cmd_option_list}
        '''
        args = list(args) # make it popable
        try:
            cmd = args.pop(0)
        except IndexError:
            raise cmdln.CmdlnUserError('Missing action argument.')
        
        import kabaret.core.ro.url
                
        try:
            if cmd == 'list':
                if args:
                    raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))
                try:
                    with kabaret.core.ro.url.get_service(local=opts.local) as service:
                        print 'Using Url service:', service._pyroUri.location
                        for url, uri in service.list().items():
                            print '%40s --> %s'%(url, uri)
                except Exception:
                    raise cmdln.CmdlnUserError(
                        'Unable to contact the %surl service'%(
                            opts.local and 'local ' or ''
                        )    
                    )

            elif cmd == 'rem':
                try:
                    url_to_rem = args.pop(0)
                except IndexError:
                    raise cmdln.CmdlnUserError('Missing url to remove argument')
                if args:
                    raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))
                try:
                    with kabaret.core.ro.url.get_service(local=opts.local) as service:
                        print 'Removing url', url_to_rem
                        result = service.remove(url_to_rem)
                        print 'Result:', result
                except Exception:
                    raise cmdln.CmdlnUserError(
                        'Unable to contact the %surl service or remove the url %r'%(
                            opts.local and 'local ' or '', url_to_rem
                        )    
                    )
                
        except Exception, err:
            msg = 'There was an error while starting a service: %s'%(err,)
            if opts.verbose:
                import traceback
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            raise cmdln.CmdlnUserError(msg)

    @cmdln.option(
        '-v', '--verbose', action='store_true',
        help='print extra information'
    )
    def do_client(self, subcmd, opts, *args):
        '''Run a client for the given project.
        
        Local Url and AppHost services will be run if not active yet.
        In such case, those services will be shut down when the client
        exits (but not when client is killed).
        
        usage:
            client <project_name>

        ${cmd_option_list}
        '''
        args = list(args) # make it popable
        try:
            project_name = args.pop(0)
        except IndexError:
            raise cmdln.CmdlnUserError('Missing project argument')
        if args:
            raise cmdln.CmdlnUserError('Too many arguments: %r'%(args,))
        
        import kabaret.core.ro.url
        import kabaret.core.ro.apphost
        import kabaret.core.ro.client
        import traceback
        client = None
        try:
            print
            print '#-------------- Client'
            client = kabaret.core.ro.client.Client(project_name)
            if project_name:
                client.connect()
                
            running = True
            context = {'c':client}
            print 'Starting Client Console. Enter "h" for help.'
            while running:
                r = raw_input('#>')
                r = r.strip()
                if not r:
                    client.tick()
                    continue
                if r == 'q':
                    running = False
                    print "Closing"
                    continue
                if r == 'h':
                    print 'Enter python code or commands. (The name "c" is the client)'
                    print 'Commands:'
                    print '    return   :    execute or update client loop'
                    print '    q        :    quit'
                    print '    h        :    help'
                    print '    other    :    python code.'
                    continue
            
                try:
                    #print(' ', r)
                    result = eval(r, context)
                    context['_'] = result
                except SyntaxError:
                    try:
                        exec(r, context)
                    except:
                        traceback.print_exc()
                except:
                    traceback.print_exc()
                else:
                    if result is not None:
                        print ' ', result
        
                
        except Exception, err:
            msg = 'There was an error while starting a service: %s'%(err,)
            if opts.verbose:
                import traceback
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            raise cmdln.CmdlnUserError(msg)
        finally:
            if client is not None:
                client.shutdown()

def main():
    import kabaret.core.project.log
    if 0:
        kabaret.core.project.log.setup(
            kabaret.core.project.log.INFO
        )
        logger = kabaret.core.project.log.getLogger()
        print logger.handlers[0].level, kabaret.core.project.log.INFO
        logger.info('TEST')
        
    else:
        kabadmin = KabAdmin()
        sys.exit(kabadmin.main())

if __name__ == "__main__":
    main()
    