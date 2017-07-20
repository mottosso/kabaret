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

    The kabaret.core.project.project module:
        Defines the Project class.
    
'''

import os

from kabaret.core.utils import importlib#, opi
from kabaret.core.project import station_config
from kabaret.core.apps import load_apps

from . import shape
from . import settings

class ProjectError(Exception):
    pass

    
        
class Project(object):
    def __init__(self, store_path, project_name):
        self.store_path = store_path
        self.project_name = project_name

        self._settings = None   # will become a core.project.settings.ProjectSettings()
        
        self._shape_class = None
        
        self._station_class = None
        self._station_config = None
        self._cached_full_station_configs = {}
        
        self._apps = None       # will become {} of app_key -> app
            
    def _load_settings(self):
        # use the default project shape to find
        # the SETTINGS:
        s = shape.get()(self.store_path, self.project_name)
        settings_path = s.path('PROJ_SETTINGS')
        self._settings = settings.ProjectSettings()
        self._settings.load(settings_path, project=self)

        self._station_class = station_config.get_station_class()
        self._station_config = self.get_station_config(
            self._station_class
        )
        self._station_config.apply()
        
    @property    
    def settings(self):
        if self._settings is None:
            self._load_settings()
        return self._settings

    def _get_shape_class(self):
        custom_shape_loader = self.settings.SHAPE.custom_loader
        if custom_shape_loader is not None:
            try:
                loader = importlib.resolve_ref(custom_shape_loader)
            except ValueError:
                raise ProjectError('Bad --shape-loader syntax: %r'%(custom_shape_loader,))
            except ImportError:
                raise ProjectError(
                    'Unable to import module for shape loader %r. '
                    'You may want to check project settings (STATION.CLASSES\' python_paths).'%(
                        custom_shape_loader
                    )
                )
            except AttributeError:
                raise ProjectError(
                    'Unable to find the callable %r '
                    'You may want to check project settings (SHAPE.custom_loader).'%(
                        custom_shape_loader,
                    )
                )
            try:
                loader()
            except TypeError:
                raise ProjectError(
                    'Unable to run the shape loader: '
                    'It must be callable with no argument!\n'
                    'You may want to check project settings (SHAPE.custom_loader).'
                )
        self._shape_class = shape.get(self.settings.SHAPE.name)
         
    @property
    def shape_class(self):
        #TODO: Maybe this should not be public
        if self._shape_class is None:
            self._get_shape_class()
        return self._shape_class
    
    def _load_apps(self):
        '''
        Instanciate the project apps
        '''
        app_refs = self.settings.PROJECT_APPS
        self._apps = load_apps(app_refs, project=self)
        
    @property
    def apps(self):
        '''
        A dict of app_key: app_instance
        '''
        if self._apps is None:
            self._load_apps()
        return self._apps

    def app_keys(self):
        '''
        Returns a list of key for the project app declared 
        in the project settings.
        '''
        return self.apps.keys()
  
    def app(self, app_key):
        '''
        Returns the project app declared with the given key, or
        None if no such app was declared in the project
        settings.
        '''
        return self.apps.get(app_key)
    
    def get_project_name(self):
        # we dont remotely use attribute so we put a method:
        return self.project_name
    
    def get_station_config(self, station_class):
        config = station_config.get_station_config(
            station_class, self.settings.STATIONS.CONFIGS
        )
        full_config = self._cached_full_station_configs.get(
            config.station_class, None
        )
        if full_config:
            return full_config
        full_config = config.copy()

        station_shape = self.shape_class(config.store_path, self.project_name)
        full_config.auto_python_paths = [
            # Additionnal python path:
            station_shape.path('DEV'),
        ]
        full_config.set_project_dirs(station_shape.to_dict())
        self._cached_full_station_configs[full_config.station_class] = full_config
        return full_config


    