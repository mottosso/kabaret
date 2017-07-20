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

    The kabaret.core.apps package:
        Define all classes related to project apps.
        
        The projects settings declares the app to use.
        Each AppHost running on the work station connects to
        the project and fetch from it the list of apps to 
        instantiate.
        The apps then live in the AppHost process and their 
        commands can be triggered by the clients.
        
        See the 'base' sub-module for more details on the App class.
        
        An app contains a list of Commands. Those commands are
        be available by the clients.
        See the 'command' sub-module for more details on the 
        Command and Arg classes.
        
'''

import inspect
import traceback

from kabaret.core.utils import importlib
from .base import App

class AppError(Exception):
    pass

class AppLoadError(AppError):
    pass

def _print_original_trace(title):
    trace_str = (
        '#'+20*'-'+title+' Error:\n#  '
        +traceback.format_exc().replace('\n', '\n#  ')
        +'\n#'+(20+len(title))*'-'
    )
    print trace_str

def load_apps(app_refs, project=None, apphost=None):
    if project is None and apphost is None:
        raise ValueError(
            'You must require apps for a project or for an apphost'
        )
    
    apps = {}
    for app_ref in app_refs:
        try:
            app = importlib.resolve_ref(app_ref)
        except ValueError:
            _print_original_trace('Get App class')
            raise AppLoadError('Bad app ref: %r'%(app_ref,))
        except ImportError:
            _print_original_trace('Import App Module')
            import sys
            raise AppLoadError(
                'Unable to import module for app ref %r.\n(sys.path was: %r)\n'
                'You may want to refine your STATIONS.CLASSES in the project settings.'%(
                    app_ref, sys.path
                )
            )
        except AttributeError:
            raise AppLoadError(
                'Unable to find the class %r '%(app_ref,)
            )

        if not inspect.isclass(app) or not issubclass(app, App):
            raise AppLoadError(
                'The class %r is not a %s.%s'%(app_ref, App.__module__, App.__name__)
            )
        
        if project is not None:
            #BEWARE: this is not yet fully supported.
            apps[app.APP_KEY] = app(host=project)

        elif apphost is not None:
            apps[app.APP_KEY] = app(host=apphost)

    return apps
