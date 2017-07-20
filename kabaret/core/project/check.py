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

    The kabaret.core.project.check module:
        Defines check_project function.
    
'''

class CheckError(Exception):
    pass

def check_dependencies(app_key, app, checking, checked, key_to_app, logger, indent=0):
    '''
    '''
    logger.info((indent*' ')+'%s: %r'%(app_key, app)) 
    if not app.REQ_APPS:
        return
    checking[app_key] = app
    indent += 1
    for dep_app_key in app.REQ_APPS:
        logger.info((indent*' ')+'REQ %s'%(dep_app_key,)) 
        if dep_app_key in checking:
            raise CheckError('Circular Reference in App APIS??? %r, %r'%(dep_app_key, app_key))
        if dep_app_key in checked:
            continue
        if dep_app_key not in key_to_app:
            raise CheckError(
                'Missing API %r needed by app with key %r'%(
                    dep_app_key, app.APP_KEY
                )
            )
        check_dependencies(
            dep_app_key, key_to_app[dep_app_key], 
            checking, checked, key_to_app, logger,
            indent+1
        )
    checked[app_key] = app
    del checking[app_key]
    
def check_project(project, logger):
    '''
    Assert various stuff about the project.
    '''        
    logger.info('Checking Apps')
    key_to_app = project.apps
    for app_key, app in key_to_app.items():
        print '  ', app_key
        check_dependencies(app_key, app, {}, {}, key_to_app, logger)
        