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

    The kabaret.core.project.settings module:
        Defines the project settings and their defaults.
    
'''

from kabaret.core.conf import Config, Group, Attribute
from .station_config import StationConfig

        
class ProjectSettings(Config):
    '''
    The Project Configuration.
    
    You can use 'project' to access the Project instance that loads the file.
    For example: 
        store = project.store_path
        proj_name = project.name
    
    Beware that this project instance has no settings yet and thus cannot
    be very helpful.
    Also, the project.store_path is the server one and is likely to be different
    from yours.
    
    '''
    EXTRA_CONTEXT = {
        'StationConfig': StationConfig,
    }
    
    def _define(self):
        self.SHAPE = Group(
            'The shape defines the mandatory filesystem structure of the project.',
            custom_loader = Attribute(
                None, 
                'An entry point for custom shapes. '
                'Use a callable with no argument.'
            ),
            name = Attribute(None, 'The shape name. Use None for kabaret default') 
        )
        
#        self.NAME_SERVICE = Group(
#            '''
#            The name service is used to discover servives on the LAN.
#            You can tweak the ports to avoid (rare) clashes with other
#            softwares using broadcasting UDP. Beware that all clients must
#            know those ports number''',
#            request_port = 9999,
#            reponse_port = 9998
#        )
        
        self.STATIONS = Group(
            '''
            This section let you define the different classes
            of stations allowed in the project.
            
            You must instantiate some StationClassConfig and 
            store then in STATIONS.CONFIGS:
            
            win7_work = StationConfig(
                station_class='Windows-7',
                store_path='path/to/store',
                python_paths=['more/path', 'for/python'],
            )
            
            The 'station_class' must be a string identifying the
            station class. 
            On the client side, the station class is taken
            from the KABARET_STATION_CLASS env variable, or
            the value of "platform.system()" if the env variable 
            is not defined.
            (see kabaret.core.station_config.get_station_class)
            All 'station_class' here must be defined accordingly 
            to this.
            
            A StationConfig with None in its station_class 
            will be used when no matching class was found.
            
            ''',
            #TODO: support station_class in the form client@station_class
            # (maya may want different python_paths)
            
            CONFIGS = [
                StationConfig(
                    station_class=None, 
                    store_path="path/to/store",
                    python_paths=[]
                )
            ]
        )
        
        self.APPS = Attribute(
           [],
           '''
           List of apps available to Clients (living in each AppHost).
           Each entry must be a string pointing to the app class, i.e: kabaret.studio.apps.flow_app.FlowApp
           '''
        )        
        self.PROJECT_APPS = Attribute(
           [],
           '''
           List of apps available to AppHost (living in the Project).
           This feature has beed disabled for now.
           '''
        )        
