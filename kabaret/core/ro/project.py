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

    The kabaret.core.ro.client module:
        Define the ProjectService, a remotly
        accessible Project.
    
''' 
import os

import Pyro4

from . import url
from . import this_host
from . import CommunicationError

from kabaret.core.project.project import Project

class ProjectService(Project):
    def __init__(self, store_path, project_name):
        super(ProjectService, self).__init__(store_path, project_name)
        self.store_path = store_path
        self.project_name = project_name
        
    def assert_store_path(self, store_path):
        if self.store_path != store_path:
            raise ValueError('The project service store_path %s does not match %s'%(
                    self.store_path, store_path
                )   
            )

    def get_settings(self):
        # The project.setting is a property
        # and does not deal well as ro method.
        # So we define this.
        return self.settings
    
    def ping(self):
        return '%s (pid:%s)'%(self._pyroDaemon.locationStr, os.getpid())


def start_service(store_path, project_name):
    with Pyro4.core.Daemon(this_host()) as daemon:
        with url.get_service(local=False) as urls:
            ps=ProjectService(store_path, project_name)
            uri=daemon.register(ps)
            urls.register(url.For.project(project_name), uri)
        print("Project Service running.")
        daemon.requestLoop()

def ensure_service(store_path, project_name):
    project = None
    try:
        project = url.resolve(url.For.project(project_name), local=False, ping=True)
    except url.UrlError:
        print 'No project service found for %r, starting a one.'%(project_name,)
    except CommunicationError:
        print 'Dead project service found for %r, starting a one.'%(project_name,)
    else:
        print 'Project Service found:', project._pyroUri
        print 'checking store'
        project.assert_store_path(store_path)
            
    if project is None:
        start_service(store_path, project_name)




if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    if not args:
        raise RuntimeError('Please provide the project name in first command line argument.')
    project_name = args.pop(0)
    
    if not args:
        raise RuntimeError('Please provide the store path in secong command line argument.')
    store_path = args.pop(0)
    
    if args:
        raise RuntimeError('Too many command line arguments.')
    
    ensure_service(store_path, project_name)
    
