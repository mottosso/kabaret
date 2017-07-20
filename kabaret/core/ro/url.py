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

    The kabaret.core.ro.url module:
        Define utilities to manage url services.
    
''' 


import os
import socket
import contextlib
import time

import Pyro4
import Pyro4.errors

from kabaret.core.utils import get_user_name
from kabaret.core.project.station_config import get_station_class

URL_ROOT = 'kabaret'

class UrlError(Exception):
    pass

def From(name):
    '''
    Returns the function and the keyword arguments to
    use (in For methods) to generate the given name.
    (i.e. The reverse of For methods)
    
    If the name cannot be decoded, None and {}
    are returned.
    '''
    if '/' not in name:
        return None, {}
    
    root, rest = name.split('/', 1)
    if root != URL_ROOT:
        return None, {}
    
    if '/' not in rest:
        return None, {}
    project_token, rest = rest.split('/', 1)
    
    if project_token != 'project':
        return None, {}
    
    if '/' not in rest:
        return For.project, {'project_name':rest}
    
    project_name, rest = rest.split('/', 1)
    
    if '/' not in rest:
        return None, []
    
    service_type, rest = rest.split('/', 1)
    if service_type == 'apphost':
        try:
            station_class, host, user = rest.split('/')
        except:
            return None, {}
        else:
            return For.apphost, {'project_name':project_name, 'station_class':station_class, 'user':user, 'host':host}
    
    elif service_type == 'client':
        try:
            host, user, client_name = rest.split('/')
        except:
            return None, {}
        else:
            return For.client, {
                'project_name':project_name, 'client_name':client_name, 'user':user, 'host':host
            }
    else:
        return None, {}
    
class For(object):
    '''
    This class is used as a namespace for the
    url constructors.
    '''
    @staticmethod
    def project(project_name):
        return '%s/project/%s'%(URL_ROOT, project_name,)
    
    @staticmethod
    def apphost(project_name, user=None, host=None, station_class=None, match_station_class=True):
        '''
        If user or host are None, the current user and current host name 
        are used, leading to the url of a local apphost.
        
        If the station_class is None, the current station_class is used.
        
        If match_station_class is True, the station_class must match the current
        station class. Use this to ensure the client is compatible with the 
        apphost pointed by the returned url.
        '''
        user = user or get_user_name()
        host = host or socket.gethostname()
        if station_class is None:
            station_class = get_station_class()
        if match_station_class:
            if station_class != get_station_class():
                raise UrlError(
                    'Access to apphost with a station class %r is forbidden '
                    '(your class is %r)'%(
                        station_class, get_station_class()
                    )
                )
        return '%s/project/%s/apphost/%s/%s/%s'%(
            URL_ROOT, project_name, station_class, host, user
        )    
    
    @staticmethod
    def client(project_name, client_name, user=None, host=None):
        user = user or get_user_name()
        host = host or socket.gethostname()
        return '%s/project/%s/client/%s/%s/%s'%(
            URL_ROOT, project_name, host, user, client_name
        )    

def resolve(url, local=True, ping=True):
    ro = None
    with get_service(local=local) as urls:
        try:
            uri = urls.lookup(url)
        except Pyro4.errors.NamingError:
            raise UrlError('Unable to resole %surl %r'%(local and 'local ' or '', url))
        else:
            ro = Pyro4.Proxy(uri)

        if ping:
            try:
                # Check this service is alive
                ro.ping()
            except Pyro4.errors.CommunicationError:
                # service is unreachable,
                # it was probably killed and did not unregister from
                # the url service.
                # let's clean up the url and raise the error:
                print 'Dead url found, cleaning up url service.'
                urls.remove(url)
                raise
    return ro

def wait_for_resolve(url, local=True, nb_try=5, wait_between=1):
    uri = None
    with get_service(local=local) as urls:
        for _ in range(nb_try):
            try:
                uri = urls.lookup(url)
            except Pyro4.naming.NamingError:
                print '  Waiting for service to register its url.'
                time.sleep(wait_between)
            else:
                print '  Url found.'
                break
    if uri is None:
        raise UrlError('Unable to resole %surl %r'%(local and 'local ' or '', url))
    return Pyro4.Proxy(uri)

@contextlib.contextmanager
def get_service(local=False):
    host = local and 'localhost' or None# #socket.gethostname()
    try:
        with Pyro4.locateNS(host) as url_service:
            yield url_service
    except Pyro4.errors.NamingError:
        raise UrlError('Unable to find url service on %r'%(host,))

def start_service(local=True):
    host = local and 'localhost' or socket.gethostname()
    tries = range(3)
    for i, _ in enumerate(tries):
        try:
            Pyro4.naming.startNSloop(
                host=host, port=None,
                enableBroadcast=not local,
                bchost=None, bcport=None,
                unixsocket=None,
                nathost=None, natport=None
            )
        except socket.error, err:
            if err.errno == 98:
                print '#----------- SOCKET ALREADY IN USE!!!!', i
                tries += ['x']
                time.sleep(1)
                
def start_service_in_process(local=True):
    print 'Starting %sUrl in separate process'%(local and 'local ' or '',)
    
    # This import is delayed here because the fucktards at The Foundry were not able
    # to provide a python with multiprocessing on windows:
    import multiprocessing

    p = multiprocessing.Process(
        target=start_service,
        args=(local,)
    )
    p.daemon = True
    p.start()
    
    host = local and 'localhost' or socket.gethostname()
    nb_try = 50
    wait_between = 1
    for _ in range(nb_try):
        try:
            url_service = Pyro4.locateNS(host)
        except Pyro4.errors.NamingError:
            print 'Waiting for %sUrl service to be ready.'%(local and 'local ' or '',)
            time.sleep(wait_between)
        else:
            print '%sUrl service up: %s'%(local and 'Local ' or '', url_service._pyroUri)
            return url_service
         
def ensure_service(local=True, new_process=True):
    host = local and 'localhost' or socket.gethostname()
    try:
        url_service = Pyro4.locateNS(host)
    except Pyro4.errors.NamingError:
        print 'No url service found, starting a one.'
        if new_process:
            return start_service_in_process(local=local)
        else:
            start_service(local=local)
    else:
        print 'Url Service found:', url_service._pyroUri
        return url_service

if __name__ == '__main__':
    import sys
    ensure_service(local='local' in sys.argv[1:])

