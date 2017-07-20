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
    The kabaret.naming.path module.
    
    Defines the PathItem, FileOrFolder and WildPath classes.
    
'''



import os
import stat

from . fields import Field, FieldValueError, FieldConfigError


class PathItem(object):
    class PathValueError(ValueError):
        pass
    
    class PathValidationError(PathValueError):
        pass
    
    class PathConfigError(PathValueError):
        def __init__(self, path_item, config, messages):
            super(PathItem.PathConfigError, self).__init__(
                'Unable to get %r under %r (%s). Error(s): \n  '%(
                    config, path_item.path(), path_item.__class__.__name__
                )+'  \n'.join(messages)
            )
    
    class PathChildError(PathValueError):
        def __init__(self, path_item, value, errors):
            super(PathItem.PathChildError, self).__init__(
                'Unable to get %r under %r (%s). Error(s): \n  '%(
                    value, path_item.path(), path_item.__class__.__name__
                )+'  \n'.join([ err.message for err in errors ])
            )

    SEP = '/'
    NAME = Field
    CHILD_CLASSES = ()
    
    @classmethod
    def from_name(cls, name):
        pi = cls()
        pi._name_field.set_value(name)
        return pi
    
    def __init__(self):
        super(PathItem, self).__init__()
        self._parent = None
        self._name_field = self.NAME(None)

    def _set_parent(self, parent):
        self._parent = parent
        
    def _get_depth(self):
        if self._parent is None:
            return 0
        return self._parent._get_depth() + 1
    
    def pformat(self, indent=None):
        if indent is None:
            indent = self._get_depth()
        ret = ''
        if self._parent is not None:
            ret = self._parent.pformat(indent-1)
        slash = indent and '/' or ''
        return (
            ret
            +('    '*indent)
            +slash
            +'%s (%s):\n%s\n'%(
                self._name_field.value(),
                self.__class__.__name__,
                self._name_field.pformat(indent+2)
            )
        )

    def __div__(self, str_path):
        try:
            name, remaining_path = str_path.split(self.SEP, 1)
        except ValueError:
            return self._get_child_from_name(str_path, validated=True)
        else:
            return self._get_child_from_name(name, validated=False) / remaining_path

    def _get_child_from_name(self, name, validated=True, allow_wild=True):
        child = None
        errs = []
        for child_class in self.CHILD_CLASSES:
            try:
                child = child_class.from_name(name)
            except FieldValueError, err:
#                print '###############', err
#                import traceback
#                traceback.print_exc()
                errs.append(err)
                child = None
                continue
            child._set_parent(self)  # must set parent before validating
            if validated:
                try:
                    child.validated()
                except PathItem.PathValueError, err:
#                    print '###############', err
#                    import traceback
#                    traceback.print_exc()
                    errs.append(err)
                    child = None
                    continue
            break
  
        if child is None:
            err = PathItem.PathChildError(self, name, errs)
            if not allow_wild:
                raise err
            # Build a WildItem and set why
            child = WildItem.from_name(name)
            child.set_why(err)
            child._set_parent(self)
            
        return child

    def to(self, **new_config):
        return self.to_config(new_config)
    
    def to_config(self, new_config):
        config = self.config()
        for key, new_value in new_config.items():
            if new_value is None:
                del config[key]
            else:
                config[key] = new_value
        return self(**config)
    
    def __call__(self, **config):
        debug = config.pop('debug', False)
        
        item = None
        next = self.root()
        consumed_keys = set()
        
        # The root is not re-created so we must ensure
        # this config points to it and mark its keys as
        # consumed:
        root_config = next.config()
        for k, v in root_config.items():
            if config.get(k) not in (None, v):
                raise self.PathConfigError(
                    next, config, [
                        'Config keys %r does not match root config: %r != %r. Cannot create this config.'%(
                            k, config[k], v
                        )
                    ]
                )
            consumed_keys.add(k)
            
        key_set = set()
        while next is not None:
            item = next
            consumed_keys.update(key_set)
            if debug:
                print '#######', item.path()
            key_set, next = item._get_child_from_config(config, debug=debug)
        
        remaining_keys = set(config.keys()).difference(consumed_keys)
        if debug:
            print '###-- consumed keys:', consumed_keys
            print '###-- config keys were:', config.keys()
            print '###-- remaing keys:', remaining_keys
        
        if remaining_keys:
            raise self.PathConfigError(
                item, config, [
                    'Config keys %r were not consumed from %r to build %r from %r (%s)'%(
                        list(remaining_keys), config.keys(), item.path(), self.path(), self.__class__.__name__
                    )
                ]
            )
            
        return item.validated()
    
    def _get_child_from_config(self, config, debug=False):
        child = None
        consumed_keys = set()
        child_depth = self._get_depth()+1
        for child_class in list(self.CHILD_CLASSES)+[WildItem]:
            if debug:
                print '#####----- child from config: trying %r'%(child_class,)
            try:
                child = child_class()
                consumed_keys = child._name_field.set_config(config, allowed_index=child_depth)
            except FieldConfigError:
                if debug:
                    import traceback
                    traceback.print_exc()
                child = None
                consumed_keys = set()
                continue
            child._set_parent(self)
            if debug:
                print '##### Got Child!', child, child.path(), 'used keys:', consumed_keys
                print '##### try validation'
            try:
                child.validate(config)
            except self.PathValidationError:
                if debug:
                    import traceback
                    traceback.print_exc()
                child = None
                consumed_keys = set()
                continue
            if debug:
                print '##### Validation done for', child, child.path()
            break
                    
        return consumed_keys, child
              
    def validated(self):
        '''
        Checks that this PathItem is a valid
        leaf. 
        Returns self or raises a PathItem.PathValidationError
        '''
        self.validate(self.config())
        return self
    
    def validate(self, leaf_config):
        '''
        Validate the config of this PathItem when
        it is an ancestor of a PathItem having 'leaf_config'
        as config.

        The default implementation checks that no key in this
        path item's config clashes with leaf_config.
        Subclasses can override here to add special validation.
        It should always call the base class' implementation
        and must raises a PathItem.PathValidationError when something 
        does not validate. 
        '''
        if self._parent:
            self._parent.validate(leaf_config)
            
        config = self._name_field.config()
        for key, local_value in config.items():
            try: 
                leaf_value = leaf_config[key]
            except KeyError:
                continue
            #print '???', self, key, local_value, leaf_value
            if leaf_value != local_value:
                raise PathItem.PathValidationError(
                    'Invalid name %r for %r (%s): %s should be %r and not %r'%(
                        self._name_field.value(), self.__class__.__name__, self.path(),
                        key, leaf_value, local_value
                    )
                )
                
    def parent(self):
        return self._parent
    
    @property
    def name_field(self):
        return self._name_field
    
    def value(self):
        return self._name_field.value()
    
    def root(self):
        if self._parent is None:
            return self
        return self._parent.root()
    
    def path(self):
        l = self._parent is not None and [self._parent.path()] or []
        l.append(str(self._name_field.value()))
        return self.SEP.join(l)

    def is_wild(self):
        return isinstance(self, WildItem)
    
    def raise_wild(self):
        if self.is_wild():
            raise self.why()
        
    def config(self, relative_to=None):
        config = {}
        if self._parent is not None and relative_to != self:
            config = self._parent.config(relative_to)
        config.update(self._name_field.config())
        return config
    
    @classmethod
    def get_keys_for(cls, path_item_type_name, up_keys=[]):
        '''
        Returns a (somewhat ordered) list of keys 
        needed to go from this item type to the first 
        child item type named 'path_item_type_name'
        '''
        here_keys = up_keys+cls.NAME.get_config_keys()
        
        if cls.__name__ == path_item_type_name:
            # remove duplicates, preserving order:
            seen = set()
            seen_add = seen.add
            return [ x for x in here_keys if x not in seen and not seen_add(x)]
        
        for child_class in cls.CHILD_CLASSES:
            if child_class == cls:
                continue
            keys = child_class.get_keys_for(path_item_type_name, up_keys=here_keys)
            if keys is not None:
                return keys
        return None

    def mtime(self):
        try:
            return os.stat(self.path())[stat.ST_MTIME]
        except:
            return 0
        
    def exists(self):
        return os.path.exists(self.path())
    
    def isfile(self):
        return os.path.isfile(self.path())
    
    def isdir(self):
        return os.path.isdir(self.path())

    def create(self):
        '''
        Create the path if it does not exists.
        If this PathItem value does not contain a '.'
        a directory is created. If it has a '.', an empty file
        is created.
        '''
        path = self.path()
        if os.path.exists(path):
            return
        dir, base = os.path.split(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        elif not os.path.isdir(dir):
            raise Exception('Cannot create PathItem on disk, Parent is not a directory.')
        if '.' in base:
            with open(path, 'w') as w:
                w.write('# Kabaret named file initialized: '+path+'\n')
        else:
            os.mkdir(path)
            
class AnyName(Field):
    KEY = 'name'

class FileOrFolder(PathItem):
    SEP = '/'
    NAME = AnyName
    CHILD_CLASSES = ()
    def _set_parent(self, parent):
        super(FileOrFolder, self)._set_parent(parent)
        self._name_field.key_override = self._name_field.make_indexed_key(
            self._name_field.key, self._get_depth()
        )   
FileOrFolder.CHILD_CLASSES = (FileOrFolder,)



class WildField(Field):
    KEY = 'wild'
    
class WildItem(PathItem):
    SEP = '/'
    NAME = WildField
    CHILD_CLASSES = ()

    def __init__(self):
        super(WildItem, self).__init__()
        self._why = None
    
    def set_why(self, exception):
        self._why = exception
    
    def why(self):
        if self._why is not None:
            return self._why
        if self._parent is not None:
            return self._parent.why()
        return Exception('Sorry, Wild path with no known reason.')

    def _set_parent(self, parent):
        super(WildItem, self)._set_parent(parent)
        self._name_field.key_override = self._name_field.make_indexed_key(
            self._name_field.key, self._get_depth()
        )
        
WildItem.CHILD_CLASSES = (WildItem,)

