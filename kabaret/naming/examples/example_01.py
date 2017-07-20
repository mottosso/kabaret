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

    This kabaret.naming.example shows how to create a simple naming 
    convention, convert from and to string, and basic use of config.

    The valid names described here are like:
        my_root/<user>/<filename>.<extension>
    where:
        <user> can be one of 'bill', 'bob', 'joe'
        <filename> must any string without a '.'
        <extension> must be one of 'doc', 'txt', 'rtf'
        
'''
import kabaret.naming

# In order to describe your naming convention you need to 
# subclass PathItem and Field classes and tie them together.
# Because each parent class will know its potential child
# class, you need to describe the child class first.
# So we start by describing the file <topic>_<version>.<extension>

'''
#----- The file.
# It has two fields separated by a '.' and cannot have any
# children.
# We will subclass CompoundField to compose the filename and
# the extension.
#
'''
#--- <filename>
# can be anything so we just subclass the basic Field 
class Basename(kabaret.naming.Field):
    pass
# We could use the kabaret.naming.Field directly but by
# using our class it conveniently sets the config key
# for this field to 'Basename' (the class name).
# Plus, we could add some specialized method here like
# for example copy_to_user(other_user_name).
# This will be covered in next examples, we will just
# add a dummy tool called 'my_tool'
#
#--- <extension>
# It must be one of 'doc', 'txt', 'rtf'
# So we subclass the ChoiceField and override the 'choices'
# class attribute:
class Extension(kabaret.naming.ChoiceField):
    choices = ['doc', 'txt', 'rtf']
# As for the Basename field, the config key will be
# the class name 'Extension' which is fine.
#
# Now we need to declare a CompoundField using those new
# fields:
class Filename(kabaret.naming.CompoundField):
    fields = (Basename, Extension)
    separator = '.'
# That's it for the file name field.
# Now we need a PathItem that uses this field and accepts
# no children:
class File(kabaret.naming.PathItem):
    NAME = Filename     # The name must match what is described by the Filename field.
    CHILD_CLASSES = ()  # There is no acceptable children for this PathItem.

    def my_tool(self):
        return 'This a File and it is awesome!'

'''
#----- The user folder.
# It has a restricted list of valid string as name and can only have
# children of the File type.
# We will subclass ChoiceField for the name and declare a new
# FileType using this Field and accepting File type children.
#
'''
#--- <user>
# It must be one of 'bill', 'bob', 'joe'
# So we subclass the ChoiceField and override the 'choices'
# class attribute.
# For this time we will pretend the default config key
# is not kool enough a specify one.
class User(kabaret.naming.ChoiceField):
    KEY = 'login'                       # specified config key
    choices = ['bill', 'bob', 'joe']    # acceptable value
# Now we define a PathItem using User as name and accepting
# File child items:
class UserFolder(kabaret.naming.PathItem):
    NAME = User
    CHILD_CLASSES = (File,) # don't forget the comma here :P

'''
#----- The root folder.
# It is a folder with the fixed name 'my_root' that
# can only contain user folders.
# We will use a FixedField for the name of our PathItem.
'''
class RootName(kabaret.naming.FixedField):
    fixed_value = 'my_root'

class Root(kabaret.naming.PathItem):
    NAME = RootName
    CHILD_CLASSES = (UserFolder,)


'''
That's it.
We described this very simple naming convention.

Now what?

Now we use it to validate some strings:
'''
#------- The root folder.
# it must be named 'my_root' do 'some_root' should fail:
try:
    root = Root.from_name('some_root')
except kabaret.naming.FieldValueError, err:
    print 'Test correctly fail using "some_root" as root name'
    print 'Reported error was:'
    print '  ', err
    
# let's create our root:
root = Root.from_name('my_root')
print 'Root created:', root.path(), root

# now that we have a root, we can test some path
print '\n\n', 10*'#', 'TESTING VALID PATHS'
valid_paths = [
    'bill/TheFileName.doc',
    'bob/The_File_Name.txt',
    'joe/blah.rtf',
]
for path in valid_paths:
    print '#'+(10*'-')
    print '  ', path
    # You can use / to create a named item from a relative path:
    named = root / path
    print '  ->', named

    # The name of a PathItem is available with value():    
    print '  name:', named.value()
    
    # The full path of a PathItem is available with path():
    print '  full path:', named.path()
    
    # If the path is not valid for the convention described by 
    # our root, the type of the returned object is WildItem
    # and is_wild() returns True
    print '  is wild?', named.is_wild()
    # When a PathItem is Wild, calling raise_wild() will raise
    # an exception explaining why it did not match any of the
    # possible types. If not Wild, raise_wild() will do nothing:
    print '  raising wild error...'
    named.raise_wild()
    
    # The PathItem can generate a config.
    # The config is a dict with all key needed to generate it
    # with a call like:
    #    root(**config)
    # As you can see we have a 'login' key in this config.
    # This is the one we specified instead of the default one
    # for the User field.
    print '  config:', named.config()
    
    # You can debug a named path with its pformat() method.
    # It shows the types and value of every PathItem and Field
    # in the path.
    print '  details:\n', named.pformat(indent=3)
    
    # You can access the PathItem field values with
    # the 'name_field' attribute of a PathItem, and
    # the parent PathItem with the parent() method.
    print '  user:', named.parent().name_field.value()
    
    # For compound fields, the subfields are accessible
    # in a instance attribute named from the sub-field key.
    print '  basename:', named.name_field.Basename.value()
    print '  extension:', named.name_field.Extension.value()
    # Also, notice that the compound field did not generate
    # a key in the config. It let its component fields provide
    # there key and value.
    
    # We can use the default PathItem tool now.
    print '  exists:', named.exists()
    
    # And the ones we defined in the File class:
    print '  my_tool:', named.my_tool()
    

# now let's see how to handle bad paths
print '\n\n', 10*'#', 'TESTING INVALID PATHS'
invalid_paths = [
    'will/TheFileName.doc',
    'bob/The_File_Name.readme',
]
for path in invalid_paths:
    print '#'+(10*'-')
    print '  ', path
    
    # If you use / to create a named item from an invalid path,
    # it will generate a WildItem
    named = root / path
    print '  ->', named
    print '  is wild:', named.is_wild()
    
    # You can learn why it is a wild path:
    print '  why?:', named.why()
    
    # The path is correct but is wild from the item
    # that did not accept any child:
    print '  details:\n', named.pformat(indent=3)
    
    # You may notice in the config that the WildItem
    # produce a 'wild@<int>' key. This is because
    # you may have several WildItem is a single path
    # with each one having a different value. It is 
    # called an indexed key. This will be covered in
    # another tutorial.
    print '  config:', named.config()


'''
Now that we know how to convert strings to named paths
and named paths to strings, let's deal with configs.

The config is more convenient than a string:
 - You can change a key and be sure each affected part of
 the path will be updated. This ensure consistency.
 - You can change the naming convention and keep the same
 keys. Every stored config will still be valid and all
 path will be updated automatically. If you store string
 paths, you cannot change them all at once.
 
We will now see how to builds named path from config
and modify a named path by changing the value of a 
config key.

'''
# To create from config keys, you simply call a named
# path and give the value for the keys you want to set:
named = root(login='bill')
print '-> bill folder:', named.path()
named = root(login='bill', Basename='the_basename', Extension='doc')
print '-> a file in bill folder:', named.path()

# If no named path can be found, an FieldValueError is raised:
try:
    named = root(login='not_valid_login')
except kabaret.naming.FieldValueError, err:
    print '-> error in given values:', err

# If some keys were not used to create the named path, an PathItem.PathConfigError
# is raised:
try:
    named = root(login='bob', more_key='test')
except kabaret.naming.PathItem.PathConfigError, err:
    print '-> error in given keys:', err

# If you have a config in a dict and want to get a named path
# you can use the ** notation:
config = {'login':'bob', 'Basename':'basename', 'Extension':'doc'}
named = root(**config)

# If you want to alter a path instead of constructing a sub-path,
# you can get the config, alter it and request the root to construct
# a sub-path:
config = named.config()
config.update({'login':'joe'})
joes_file = named.root()(**config)
print '-> altered path:', joes_file.path()
# But you will probably use the convenient to() and to_config() methods
# which does it all for you:
joes_file = named.to(login='joe')
print '-> to path:', joes_file.path()
joes_file = named.to_config(config)
print '-> to_config path:', joes_file.path()


'''
Well, that's all for this tutorial!

You now know how to define a simple named convention that
will help your users to construct and alter valid paths.
They will have meaningful error messages when some path
does not meet the convention, but will still be able to
use them.

'''