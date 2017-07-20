'''
    Copyright (c) Supamonks Studio and individual contributors.
    All rights reserved.

    This file is part of kabaret, a python Digital Creation Framework.

    Kabaret is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.
        
    Redistributions in binary form must reproduce the above copyright 
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
    
    Kabaret is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.
    
    You should have received a copy of the GNU Lesser General Public License
    along with kabaret.  If not, see <http://www.gnu.org/licenses/>

--

    The kabaret.core.ro.apphost module:
        Define the AppHostService: a remotly 
        accessible AppHost.
    
''' 
 
import os
import sys
import multiprocessing

import Pyro4

from kabaret.core.apphost import AppHost

from . import url
from . import this_host
from . import CommunicationError


class AppHostService(AppHost):
    def __init__(self, project_name):
        self.project_name = project_name
        project_url = url.For.project(project_name)
        project = url.resolve(project_url, local=False)
        self.url = url.For.apphost(self.project_name)
        super(AppHostService, self).__init__(project)
        
    def kill(self):
        import signal
        pid = os.getpid()
        try:
            os.kill(os.getpid(), signal.SIGTERM)
        except AttributeError:
            # Look like a window python < 2.7 :/
            import ctypes
            PROCESS_TERMINATE = 1
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
            ctypes.windll.kernel32.TerminateProcess(handle, -1)
            ctypes.windll.kernel32.CloseHandle(handle)
               
    def ping(self):
        ret = '%s (pid:%s)'%(self._pyroDaemon.locationStr, os.getpid())
        print 'Client pings AppHost, returning', ret
        print 'DEBUG Clients:'
        for client in self._clients:
            print '   ', client
        return ret
    
    def ping_project(self):
        ret = self._project.ping()
        print 'Client pings Project thru AppHost, returning', ret
        return ret

    def print_clients(self):
        print '#--'*10
        for c in self._clients:
            print c
            print '  ping', c.ping()
            

def start_service(project_name):
    '''
    Starts an AppHost service for the given project.
    The service will be registered to the current user.
    '''
    with Pyro4.core.Daemon(this_host()) as daemon:
        with url.get_service() as urls:
            ah=AppHostService(project_name)
            uri=daemon.register(ah)
            service_url = url.For.apphost(project_name)
            urls.register(service_url, uri)
            daemon.requestLoop() #TODO: make the loop condition work!
            daemon.shutdown()
            urls.remove(service_url)

def start_service_in_process(project_name, local_url=False):
    '''
    Same as start_service(project_name) but launch the service in
    another process and returns an AppHost connected to it.
    '''
    print('Starting %r AppHost in separate process'%(project_name,))
    p = multiprocessing.Process(
        target=start_service,
        args=(project_name,)
    )
    p.daemon = True
    p.start()
    
    app_host_url = url.For.apphost(project_name)
    app_host = url.wait_for_resolve(app_host_url, local=local_url)
    return app_host, app_host_url


def ensure_service(project_name, new_process=True):
    '''
    Verifies that a local AppHost is running for the current user,
    starting one if not.
    '''
    apphost = None
    service_url = url.For.apphost(project_name)
    try:
        apphost = url.resolve(service_url, local=False)
    except url.UrlError, err:
        #print '>>>', err
        print 'No AppHost service found for %r (%s), starting a new one.'%(project_name,service_url)
    except CommunicationError, err:
        #print '>>>>', err
        print 'Dead AppHost service found for %r (%s), starting a new one.'%(project_name,service_url)
    else:
        print 'AppHost Service for %r (%s) found: %s'%(project_name,service_url,apphost._pyroUri.location)
            
    if apphost is None:
        if new_process:
            return start_service_in_process(project_name)
        else:
            start_service(project_name)
    return apphost, service_url

def find_service(project_name, user=None, host=None):
    '''
    Returns the AppHost service for the given project_name.
    
    If user or host are None, they default to the current
    user and the current host.
    '''
    service_url = url.For.apphost(project_name, user, host)
    try:
        apphost = url.resolve(service_url, local=False)
    except (url.UrlError, CommunicationError):
        print 'AppHost service %r not found.'%(service_url,)
        raise
    
    print 'AppHost Service found:', apphost._pyroUri.location
    return apphost
    
if __name__ == '__main__':
    import sys
    project_name = sys.argv[1:]
    if not project_name:
        raise RuntimeError('Please provide the project name in first command line argument.')
    apphost = ensure_service(project_name, new_process=True)

    r = raw_input('Press Enter to close the app host service (or k+Enter to kill it).')
    if r == 'k':
        apphost._pyroOneway.add('kill')
        apphost.kill()
        print 'AppHost Killed.'
    else:
        print 'AppHost Stopped.'
    
