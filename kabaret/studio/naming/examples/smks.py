'''

    trying out the path and field classes.


'''

from kabaret.naming import (
    Field, ChoiceField, MultipleFields, CompoundField, IndexingField, FixedField,
    FieldValueError,
    PathItem
)

#
#
#                      FIELDS
#
#
class Extension(ChoiceField):
    choices = ['ma', 'nk', 'abc', 'py', 'txt']
    optional = True
    
class Type(Field):
    pass
    
class Types(MultipleFields):
    field_type = Type
    separator = '_'
    optional = True
    
class Dept(ChoiceField):
    choices = ['Mod', 'Setup', 'Shad', 'For', 'Anim', 'Lighting', 'Compo']

class AssetName(Field):
    pass

class Variation(Field):
    optional = True

class AssetFullName(CompoundField):
    fields = (AssetName, Variation)
    separator = '_'
    
class AssetTask(CompoundField):
    fields = (AssetFullName, Dept, Types)
    separator = '-'

class AssetTaskFileName(CompoundField):
    fields = (AssetTask, Extension)
    separator = '.'

class Seq(IndexingField):
    prefix = 'S'
    padding = '@@'

class Shot(IndexingField):
    prefix = 'P'
    padding = '@@@'

class Group(ChoiceField):
    KEY = None
    allow_None = True # we have no key so we use None until the path validates
    choices = ['3D', 'Export', 'Out', 'Paint', 'Edit', 'Image', 'Sound', 'Compo', 'Other']

    def set_config(self, config, allowed_index=None):
        self.set_value(None)
        return set()
    
class Film(Field):
    pass

class Id(CompoundField):
    fields = (Film, Seq, Shot)
    separator = '_'

class Task(CompoundField):
    fields = (Id, Dept, Types)
    separator = '-'

class TaskFileName(CompoundField):
    fields = (Task, Extension)
    separator = '.'

class Work(FixedField):
    KEY = None
    fixed_value = 'Workspace'
    def set_config(self, config, allowed_index=None):
        if 'Film' in config or 'Bank' in config or not config:
            self.set_value(self.fixed_value)
            return set()
        raise self.FieldConfigError(
            'No film or bank in this config, cannot be in Workspace '%(
                config
            )
        )

    
class Project(Field):
    pass

class Bank(Field):
    def validate(self):
        super(Bank, self).validate()
        if not self._value.startswith('Bank'):
            raise FieldValueError(
                'Value %r is invalid for %r: does not starts with "Bank"'%(
                    self._value, self.key
                )
            )


#
#
#        PATH ITEMS
#
#
class AssetTaskFile(PathItem):
    NAME = AssetTaskFileName
    CHILD_CLASSES = ()
    
class AssetTaskFolder(PathItem):
    NAME = AssetTask
    CHILD_CLASSES = (AssetTaskFile,)
    
class AssetDeptFolder(PathItem):
    NAME = Dept
    CHILD_CLASSES = (AssetTaskFolder,)

class AssetFolder(PathItem):
    NAME = AssetName
    CHILD_CLASSES = (AssetDeptFolder,)

class AssetGroupFolder(PathItem):
    NAME = Group
    CHILD_CLASSES = (AssetFolder,)

    DEPT_TO_GROUP = {
        'Anim': '3D',
        'Lighting': '3D',
        'Mod': '3D',
        'Setup': '3D',
        'Shad': '3D',
        'Comp': 'Compo',
        'Comp': 'Compo',
        'Matte': 'Paint',
        'For': 'Out',
    }
    TYPE_TO_GROUP = {
        'Export': 'Export',
    }
    @classmethod
    def _get_group(cls, types=None, dept=None):
        '''
        Returns the valid group for a path
        with types and dept.
        '''
        if types is None:
            return cls.DEPT_TO_GROUP.get(dept, None)
        
        for type in reversed(types.split('_')):
            try:
                return cls.TYPE_TO_GROUP[type]
            except KeyError:
                pass
        if dept:
            return cls._get_group(None, dept)
        return None
    
    def validate(self, leaf_config):
        super(AssetGroupFolder, self).validate(leaf_config)
        
        # Check the config's Dept and Types does not
        # give another group
        types = leaf_config.get('Types', None)
        dept = leaf_config.get('Dept', None)
        if not types and not dept:
            # we can't know, let's accept the value.
            return 
        
        current_group = self._name_field.value()
        valid_group = self._get_group(types, dept)
        
        if current_group is None:
            self._name_field.set_value(valid_group)
            return
         
        if current_group != valid_group:
            raise PathItem.PathValidationError(
                'Invalid Group %r for Dept %r and Types %r: should be %r'%(
                    current_group, dept, types, valid_group
                )
            )

class BankFolder(PathItem):
    NAME = Bank
    CHILD_CLASSES = (AssetGroupFolder,)

class TaskFile(PathItem):
    NAME = TaskFileName
    CHILD_CLASSES = ()
    
class TaskFolder(PathItem):
    NAME = Task
    CHILD_CLASSES = (TaskFile,)
    
class DeptFolder(PathItem):
    NAME = Dept
    CHILD_CLASSES = (TaskFolder,)
    
class ShotFolder(PathItem):
    NAME = Shot
    CHILD_CLASSES = (DeptFolder,)
    
class SeqFolder(PathItem):
    NAME = Seq
    CHILD_CLASSES = (ShotFolder,)

class FilmGroupFolder(PathItem):
    NAME = Group
    CHILD_CLASSES = (SeqFolder, ShotFolder)

    DEPT_TO_GROUP = {
        'Anim': '3D',
        'Lighting': '3D',
        'Mod': '3D',
        'Setup': '3D',
        'Shad': '3D',
        'Comp': 'Compo',
        'Comp': 'Compo',
        'Matte': 'Paint',
        'For': 'Out',
    }
    TYPE_TO_GROUP = {
        'Export': 'Export',
    }
    @classmethod
    def _get_group(cls, types=None, dept=None):
        '''
        Returns the valid group for a path
        with types and dept.
        '''
        if types is None:
            return cls.DEPT_TO_GROUP.get(dept, None)
        
        for type in reversed(types.split('_')):
            try:
                return cls.TYPE_TO_GROUP[type]
            except KeyError:
                pass
        if dept:
            return cls._get_group(None, dept)
        return None
    
    def validate(self, leaf_config):
        super(FilmGroupFolder, self).validate(leaf_config)
        
        # Check the config's Dept and Types does not
        # give another group
        types = leaf_config.get('Types', None)
        dept = leaf_config.get('Dept', None)
        if not types and not dept:
            # we can't know, let's accept the value.
            return 
        
        current_group = self._name_field.value()
        valid_group = self._get_group(types, dept)
        
        if current_group is None:
            self._name_field.set_value(valid_group)
            return
        
        if current_group != valid_group:
            raise PathItem.PathValidationError(
                'Invalid Group %r for Dept %r and Types %r: should be %r'%(
                    current_group, dept, types, valid_group
                )
            )
        
class FilmFolder(PathItem):
    NAME = Film
    CHILD_CLASSES = (FilmGroupFolder,)
    
class WorkFolder(PathItem):
    NAME = Work
    CHILD_CLASSES = (BankFolder, FilmFolder)

class ProjectFolder(PathItem):
    NAME = Project
    CHILD_CLASSES = (WorkFolder,)

class StoreFolder(PathItem):
    NAME = Field
    CHILD_CLASSES = (ProjectFolder,)
    
if __name__ == '__main__':
    if 0:
        if 0:
            s = Bank(None)
            s.set_value('Film')
        
        name = Task(None)
        name.set_value('FILM_S02_P006-Anim-Export_Cam')
        print name
        print name.value()
        print name.config()
        print name.Id.Film.value()
        print name.Id.Shot.value()
        print name.Id.Shot.index
        config = name.config()
        print config
        new_name = Task(None)
        new_name.set_config(config)
        print name.value()
        print new_name.value()
        assert name.value() == new_name.value()
        
    else:
        store = StoreFolder.from_name('X:/STORE')
        print store.path()
        project = store / 'PROJ'
        print project.path()
        project_subpath = 'Workspace/Film/Export/S01/P002/Anim/Film_S01_P002-Anim-Export_Cam'
        shot_item = project / project_subpath
        print shot_item.path()
        print project.path()+'/'+project_subpath
        print shot_item.pformat()
        config = shot_item.config()
        print config
        assert shot_item.path() == project.path()+'/'+project_subpath
        #shot_item.raise_wild()
        
        debug = True
        new_shot_item = project(debug=debug, **config)
        print new_shot_item.pformat()
        
        print shot_item.path()
        print new_shot_item.path()
        assert new_shot_item.path() == shot_item.path()
        
        if not new_shot_item.is_wild():
            for _ in range(10):
                Shot = new_shot_item.name_field.Id.Shot.next_value(offset=100)
                new_shot_item = new_shot_item.to(Shot=Shot)
                print new_shot_item.path()
            
        print 'Keys from Store to Task:', StoreFolder.get_keys_for('TaskFolder')
        print 'Keys from Store to AssetTask:', StoreFolder.get_keys_for('AssetTaskFolder')
        
        
        asset_mod = project.to(
            debug=True,
            #Bank='Bank', Dept='For', AssetName='MyAsset', Types='Anim', Extension='ma'
            **{'Shot': 'P002', 'Seq': 'S01', 'Project': 'TEST', 'Dept': 'Anim', 'Types': 'Export_Cam', 'Film': 'Film'}
            
        )
        print asset_mod.pformat()

        asset_mod_var = project.to(
            debug=True,
            Bank='Bank', Dept='For', AssetName='MyAsset', Variation='VAR', Types='Anim', Extension='ma'
            
        )
        print asset_mod_var.pformat()
        