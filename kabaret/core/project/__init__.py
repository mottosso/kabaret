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

    The kabaret.core.project package:
        Create and inspect projects.
    
'''

import os
import traceback

import kabaret.core.utils.importlib

from . import shape
from .project import Project, ProjectError
from .settings import ProjectSettings

class ProjectAdminError(Exception):
    pass

def create(store_path, name, shape_name=None, custom_shape_loader=None):
    '''
    Creates a project 'name' in the store at 'store_path'.
    
    The store must already exist or a ProjectAdminError 
    will be raised.
    
    The project may not already exist. Its shape will be
    extended to the given one, and settings will be reset
    to default values (a settings_XXX.old is saved).
    '''
    if not os.path.isdir(store_path):
        raise ProjectAdminError(
            'Store {0!r} does not exists.'.format(store_path)
        )
    
    if custom_shape_loader is not None:
        try:
            loader = kabaret.core.utils.importlib.resolve_ref(custom_shape_loader)
        except ValueError:
            raise ProjectError('Bad --shape-loader syntax: %r'%(custom_shape_loader,))
        except ImportError:
            raise ProjectError(
                'Unable to import module for shape loader %r. '
                'You may want to check your PYTHONPATH.'%(
                    custom_shape_loader
                )
            )
        except AttributeError:
            raise ProjectError(
                'Unable to find the callable %r '%(custom_shape_loader,)
            )
        try:
            loader()
        except TypeError:
            raise ProjectError(
                'Unable to run the shape loader: '
                'it must be callable with no argument'
            )

    proj_shape = shape.get(shape_name)(store_path, name)
    proj_shape.create()
    proj_settings = ProjectSettings()
    proj_settings.SHAPE.custom_loader = custom_shape_loader
    proj_settings.SHAPE.name = shape_name
    proj_settings.STATIONS.CONFIGS[0].store_path = store_path
    print proj_settings.to_script()
    print custom_shape_loader, shape_name
    proj_settings.save(proj_shape.path('PROJ_SETTINGS'), do_backup=True)
    
 