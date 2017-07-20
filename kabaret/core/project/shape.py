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

    The kabaret.core.project.shape module.
    
    Holds the possible shapes of a project.
    A project's shape is the structure of the mandatory
    directories and files for a folder to act as
    a kabaret project.

    Applications can declare new shapes or alter existing
    ones with set(shape_name, shape).
    
    A shape is retrieved with get(shape_name).
    
    The administration tools will give an option to 
    call a python method that declares custom shapes
    before creating a project.
    Once created, the project will store a copy of
    this shape so that it can use it for all its
    lifetime.
    
    A Shape contains path to files or folder.
    Each path can be given an unique KEY that kabaret
    will use when referring to this path.
    The BaseShape class defines all the KEYs needed
    by the kabaret framework. You can inherit it to 
    alter the paths or to declare new KEYs used by
    your modules.
        
'''
import os

from . import log

class ShapeItem(object):
    '''
    ShapeItem are used in project shapes.
    They declare a path relative to the project, defining it as
    a folder or a file, and bind a description to it.
    '''
    FOLDER = 1
    FILE = 2

    @classmethod
    def _cmp(cls, a, b):
        return cmp(a.proj_path, b.proj_path)
    
    def __init__(self, proj_path, description=None, type=0):
        '''
        Creates a ShapeItem for the in project path 'proj_path'.
        The type must be Shape.FOLDER or ShapeItem.FILE (default is Shape.FOLDER).
        The optional description could be presented to an administrator user.
        '''
        self.proj_path = proj_path
        self.type = type or self.__class__.FOLDER
        self.description = description
    
    def get_path(self, for_shape):
        '''
        Your subclasses can override this to create some
        wild and not recommended behavior like path
        outside the project root folder.
        '''
        return for_shape.item_path(self)
    
    def create(self, for_shape):
        '''
        Your subclasses can override this to create some
        esoteric behavior like creations or multiple
        paths, links, etc...
        '''
        path = self.get_path(for_shape)
        if self.type == self.__class__.FOLDER:
            os.makedirs(path)
        else:
            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(path, 'w'):
                pass
        
    def ensure_exists(self, for_shape):
        '''
        Ensures the path exists for the given project
        shape.
        Returns True if the path exists and False
        if it had to be created.
        '''
        path = self.get_path(for_shape)
        if os.path.exists(path):
            return True
        self.create(for_shape)
        return False
        
class BaseShape(object):
    '''
    This is the default project shape and also the base class for all
    project shapes.
    
    When creating a new shape, you subclass one like this:
    
    class MyShape(BaseShape):
        TEMP = ShapeItem('_TEMP_')         # override the default TEMP path
        UTEMP = ShapeItem('_TEMP_/users')  # declare a new KEY
    
    /!\ Note that overriding the SETTINGS KEY is not yet supported /!\
    
    '''
    PROD = ShapeItem('Production', 'Management team Folder')
    PREZ = ShapeItem('Production/Presentation', 'Folder for files shown to the clients')
    RECEP = ShapeItem('Production/Reception', 'Folder for files reveived from the clients')
    REFS = ShapeItem('References', 'Folder for all references used by the creative team')
    WORK = ShapeItem('Workspace', 'Creative team folder (all the deliverable work)')
    TEMP = ShapeItem('Temp', 'Temp folder for exange or sandboxing')
    ENVS = ShapeItem('System/Env', 'Folder for Kabaret environment configuration')
    REPO = ShapeItem('System/Repo', 'Kabaret versioned file repository')
    LOGS = ShapeItem('System/Logs', 'Folder for Kabaret apps logs')
    DEV = ShapeItem('System/Dev', 'Folder for project specific dev')
    SETTINGS_DIR = ShapeItem('System/Settings', 'Apps setting')
    PROJ_SETTINGS = ShapeItem('System/Settings/_project_.kbr', 'Project setting', ShapeItem.FILE)

    @classmethod
    def items(cls):
        '''
        Returns list of ShapeItem declared here.
        '''
        # sort by path so that order is a little meaningful:
        path_to_item = sorted([ 
            (v.proj_path, v) for v in cls.__dict__.itervalues() if isinstance(v, ShapeItem)
        ])
        return [ i[1] for i in path_to_item ]

    @classmethod
    def key_names(cls):
        '''
        Returns a string list of KEYs declared here.
        '''
        # sort by path so that order is a little meaningful:
        path_to_key = sorted([ 
            (v.proj_path, k) for k, v in cls.__dict__.iteritems() if isinstance(v, ShapeItem)
        ])
        return [ i[1] for i in path_to_key ]
        
    def __init__(self, store_path, project_name):
        '''
        Use this shape for the given project.
        '''
        super(BaseShape, self).__init__()
        self.store = store_path
        self.proj = project_name
    
    def path(self, key):
        return getattr(self, key).get_path(self)
    
    def item_path(self, item):
        return os.path.join(self.store, self.proj, item.proj_path)
    
    def create(self):
        logger = log.getLogger()
        logger.info(
            "Creating Project Shape: {0} {1!r} {2!r}".format(
                self.__class__.__name__, self.store, self.proj
            )
        )
        for i in self.__class__.items():
            logger.info(' '+(i.description or i.proj_path))
            if i.ensure_exists(self):
                logger.info('  existed')
            else:
                logger.info('  created')

    def to_dict(self):
        d = dict([
            (key, self.path(key)) for key in self.key_names()
        ])
        return d
    
# Shape Register:
_DEFAULT_SHAPE_NAME = 'Default Project Shape'
_SHAPES = {
    _DEFAULT_SHAPE_NAME: BaseShape,
}

def get(shape_name=None):
    '''
    Returns the project shape named 'shape_name'.
    If shape_name is None, the default shape is 
    returned.
    
    If the shape is unknown, a KeyError is raised.
    '''
    global _SHAPES
    global _DEFAULT_SHAPE_NAME
    
    shape_name = shape_name is None and _DEFAULT_SHAPE_NAME or shape_name
    return _SHAPES[shape_name]

def set(shape_name, shape, set_default=False):
    '''
    Set the shape that is named 'shape_name'.
    
    The given shape must be an instance of kabaret.core.project.shape.Shape
    
    If set_default is True, get() will return this
    shape.
    '''
    global _SHAPES
    _SHAPES[shape_name] = shape
    
    if set_default:
        global _DEFAULT_SHAPE_NAME
        _DEFAULT_SHAPE_NAME = shape_name

