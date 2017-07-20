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

    The kabaret.core.project.station_config module:
        Defines the StationConfig class and station class utilities.
    
    The station class is used by the project to select a suitable
    station config from the ones declared in its settings.
    
    The station class is deduced from platform information (specifically 
    a platform.system() call return value) or the environment
    variable 'KABARET_STATION_CLASS' if it is defined.
    
    The station config holds project informations specific to the station
    like the store path or the python path etc...
    
    An AppHost instance will ask the project to provide a StationConfig
    for a given station class, and apply() it.
'''


import os 
import sys
import platform
import pprint

ENV__STATION_CLASS = 'KABARET_STATION_CLASS'


class StationConfig(object):
    def __init__(self, station_class, store_path, python_paths):
        super(StationConfig, self).__init__()
        self.station_class = station_class
        self.store_path = store_path
        self.python_paths = python_paths
        self.auto_python_paths = []
        self.project_dirs = {}
        
    def __repr__(self):
        return '%s(\n\tstation_class=%r,\n\tstore_path=%r,\n\tpython_paths=%s\n)'%(
            self.__class__.__name__,
            self.station_class, 
            self.store_path,
            pprint.pformat(self.python_paths)
        )

    def copy(self):
        station_config = self.__class__(
            self.station_class,
            self.store_path,
            self.python_paths
        )
        station_config.auto_python_paths = self.auto_python_paths
        station_config.project_dirs = self.project_dirs.copy()
        return station_config
    
    def set_project_dirs(self, key_to_path):
        self.project_dirs = dict(key_to_path)
    
    def get_python_paths(self):
        '''
        Return an orderer list of path that should be present in
        the python path (in this order) when this config is applied.
        (this means self.python_paths+self.auto_python_paths)
        '''
        # beware: self.auto_python_paths must be in front
        # of self.python_paths in sys.path since
        # the project Dev must be able to override 
        # the generic code.
        return [ path for path in self.python_paths+self.auto_python_paths ]
        
    def apply(self):
        for path in reversed(self.get_python_paths()):
            if path not in sys.path:
                sys.path.insert(0, path)

        
def get_station_config(station_class, station_config_list):
    default_config = None
    selected = None
    for config in station_config_list:
        if default_config is None and config.station_class is None:
            default_config = config
        elif station_class == config.station_class:
            selected = config
            break
        
    if selected is None:
        if default_config is None:
            raise ValueError(
                'Unable to find a StationConfig matching %r, and no default found either'%(
                    station_class
                )
            )
        selected = default_config
    return selected

def get_station_class():
    if ENV__STATION_CLASS in os.environ:
        station_class = os.environ[ENV__STATION_CLASS]
    else:
        station_class = platform.system()
    return station_class
