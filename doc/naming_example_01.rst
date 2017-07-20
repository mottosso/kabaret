
######
Basics
######

This example shows how to create a simple naming 
convention, convert from and to string, and the basic use of config.

.. note:: This tutorial is available in the module kabaret.naming.examples.example_01
		  and can be run directly to see the outputs.

We are going to model a naming convention that describes file names like::

    my_root/<user>/<filename>.<extension>

where:
	=========  ========================
	Field      Possible value
	=========  ========================
	user       'bill', 'bob' or 'joe'
	filename   any string without a '.'
	extension  'doc', 'txt' or 'rtf'
	=========  ========================

examples::

	my_root/bill/the_file.doc
	my_root/bob/readme.txt
	my_root/joe/todo.doc
	

**********************************
How to define a set of valid names
**********************************

The class kabaret.naming.PathItem represents a part in a path. It knows its name and its parent PathItem.
So when you hold a PathItem, you have access to informations on the full path.

We call this a **named path**.

Each kabaret.naming.PathItem subclass knows what name is valid for it and what kind of children it 
can have. The name is stored in a kabaret.naming.Field instance which validate a string value.

Thus, by subclassing PathItem and Field you define a list of possible paths under a known
root subclass. 

***********
Let's do it
***********

First of all, import the naming::

	import kabaret.naming

Since each PathItem subclass class needs to know its potential child
classes, you need to describe the child classes first.

So we start by describing the file *<topic>_<version>.<extension>*.

The file
========
It has two fields separated by a '.' and cannot have any children.


We will subclass CompoundField to compose the filename and the extension.

Basename
--------
The value can be anything so we just subclass the basic Field::

	class Basename(kabaret.naming.Field):
	    pass

We could use the kabaret.naming.Field directly but by using our own class conveniently sets the config key
for this field to *Basename* (the class name).

extension
---------
It must be one of 'doc', 'txt', 'rtf' so we subclass the ChoiceField and override the 'choices'
class attribute::

	class Extension(kabaret.naming.ChoiceField):
	    choices = ['doc', 'txt', 'rtf']

As for the Basename field, the config key will be the class name 'Extension' which is fine.

Filename
--------
Now we need to declare a CompoundField using those fields and a '.' to joins them::

	class Filename(kabaret.naming.CompoundField):
	    fields = (Basename, Extension) # Ordered list of fields composing this one
	    separator = '.'				   # The character used to join the field values

That's it for the file name field.
Now we need a PathItem that uses this field and accepts no children::

	class File(kabaret.naming.PathItem):
	    NAME = Filename     # The name must match what is described by the *Filename* field.
	    CHILD_CLASSES = ()  # There is no acceptable children for this PathItem.
	
	    def my_tool(self):
	    	'''
	    	This class is a great place to provide 
	    	tools for every packages dealing with
	    	this files :)
	    	'''
	        return 'This is a *File* and it is awesome!'

Now that we have a class that represents all the files in our system, we could add some specialized method 
like for example *copy_to_user(other_user_name)* and everyone validating a filename could now use this tool.
This will be covered in another tutorial, we just added a dummy tool called 'my_tool' here.

The user folder
===============

It accepts a restricted list of string and can only have children of the *File* type.

We will subclass ChoiceField for the name and declare a new PathItem using this Field 
and accepting only *File* children.

user
----

It must be one of 'bill', 'bob', 'joe', so we subclass the ChoiceField and override the 'choices'
class attribute.

This time we will pretend that the default config key is not kool enough and specify one::

	class User(kabaret.naming.ChoiceField):
	    KEY = 'login'                       # specified config key
	    choices = ['bill', 'bob', 'joe']    # acceptable value

Now we define a PathItem using User as name and accepting *File* child items::

	class UserFolder(kabaret.naming.PathItem):
	    NAME = User
	    CHILD_CLASSES = (File,) # don't forget the comma here :P


The root folder
---------------

It is a folder with the fixed name 'my_root' that can only contain user folders.
We will use a FixedField for the name of our PathItem::

	class RootName(kabaret.naming.FixedField):
	    fixed_value = 'my_root'
	
	class Root(kabaret.naming.PathItem):
	    NAME = RootName
	    CHILD_CLASSES = (UserFolder,)


*********
Now what?
*********

That's it!

We described this very simple naming convention.

Now we use it to validate some strings.

The root folder
===============

We need create a root instance.

It must be named 'my_root' so 'some_root' should fail::
	
	try:
	    root = Root.from_name('some_root')
	except kabaret.naming.FieldValueError, err:
	    print 'Test correctly fail using "some_root" as root name'
	    print 'Reported error was:'
	    print '  ', err

outputs::

	Test correctly fail using "some_root" as root name
	Reported error was:
	   Value 'some_root' does not match the computed value 'my_root' in field 'RootName'


Let's create our root::

	root = Root.from_name('my_root')
	print 'Root created:', root.path(), root

outputs::

	Root created: my_root <__main__.Root object at 0x01F0F6B0>


Test Paths
==========

Now that we have a root, we can test some path::

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
    
outputs::

	########## TESTING VALID PATHS
	#----------
	   bill/TheFileName.doc
	  -> <__main__.File object at 0x01F0F7F0>
	  name: TheFileName.doc
	  full path: my_root/bill/TheFileName.doc
	  is wild? False
	  raising wild error...
	  config: {'RootName': 'my_root', 'login': 'bill', 'Basename': 'TheFileName', 'Extension': 'doc'}
	  details:
	    /my_root (Root):
	            RootName='my_root' (Computed) (Fixed to 'my_root')
	        /bill (UserFolder):
	                login='bill' (Choices: ['bill', 'bob', 'joe'])
	            /TheFileName.doc (File):
	                    Filename='TheFileName.doc' (Compound sep='.')
	                    Filename.Basename='TheFileName'
	                    Filename.Extension='doc' (Choices: ['doc', 'txt', 'rtf'])
	
	  user: bill
	  basename: TheFileName
	  extension: doc
	  exists: False
	  my_tool: This a File and it is awesome!
	#----------
	   bob/The_File_Name.txt
	  -> <__main__.File object at 0x01F0F8F0>
	  name: The_File_Name.txt
	  full path: my_root/bob/The_File_Name.txt
	  is wild? False
	  raising wild error...
	  config: {'RootName': 'my_root', 'login': 'bob', 'Basename': 'The_File_Name', 'Extension': 'txt'}
	  details:
	    /my_root (Root):
	            RootName='my_root' (Computed) (Fixed to 'my_root')
	        /bob (UserFolder):
	                login='bob' (Choices: ['bill', 'bob', 'joe'])
	            /The_File_Name.txt (File):
	                    Filename='The_File_Name.txt' (Compound sep='.')
	                    Filename.Basename='The_File_Name'
	                    Filename.Extension='txt' (Choices: ['doc', 'txt', 'rtf'])
	
	  user: bob
	  basename: The_File_Name
	  extension: txt
	  exists: False
	  my_tool: This a File and it is awesome!
	#----------
	   joe/blah.rtf
	  -> <__main__.File object at 0x01F0F7F0>
	  name: blah.rtf
	  full path: my_root/joe/blah.rtf
	  is wild? False
	  raising wild error...
	  config: {'RootName': 'my_root', 'login': 'joe', 'Basename': 'blah', 'Extension': 'rtf'}
	  details:
	    /my_root (Root):
	            RootName='my_root' (Computed) (Fixed to 'my_root')
	        /joe (UserFolder):
	                login='joe' (Choices: ['bill', 'bob', 'joe'])
	            /blah.rtf (File):
	                    Filename='blah.rtf' (Compound sep='.')
	                    Filename.Basename='blah'
	                    Filename.Extension='rtf' (Choices: ['doc', 'txt', 'rtf'])
	
	  user: joe
	  basename: blah
	  extension: rtf
	  exists: False
	  my_tool: This a File and it is awesome!

Now let's see how to handle bad paths::
	
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

outputs::

	########## TESTING INVALID PATHS
	#----------
	   will/TheFileName.doc
	  -> <kabaret.naming.path.WildItem object at 0x01F0F890>
	  is wild: True
	  why?: Unable to get 'will' under 'my_root' (Root). Error(s): 
	  Value 'will' is invalid for 'login': should be one of ['bill', 'bob', 'joe']
	  details:
	    /my_root (Root):
	            RootName='my_root' (Computed) (Fixed to 'my_root')
	        /will (WildItem):
	                wild@1='will'
	            /TheFileName.doc (WildItem):
	                    wild@2='TheFileName.doc'
	
	  config: {'wild@2': 'TheFileName.doc', 'RootName': 'my_root', 'wild@1': 'will'}
	#----------
	   bob/The_File_Name.readme
	  -> <kabaret.naming.path.WildItem object at 0x01F0F7F0>
	  is wild: True
	  why?: Unable to get 'The_File_Name.readme' under 'my_root/bob' (UserFolder). Error(s): 
	  Value 'readme' is invalid for 'Extension': should be one of ['doc', 'txt', 'rtf']
	  details:
	    /my_root (Root):
	            RootName='my_root' (Computed) (Fixed to 'my_root')
	        /bob (UserFolder):
	                login='bob' (Choices: ['bill', 'bob', 'joe'])
	            /The_File_Name.readme (WildItem):
	                    wild@2='The_File_Name.readme'
	
	  config: {'wild@2': 'The_File_Name.readme', 'RootName': 'my_root', 'login': 'bob'}
	  
Config
======

Now that we know how to convert strings to named paths
and named paths to strings, let's deal with configs.

The config is more convenient than a string:
	* You can change a key and be sure each affected part of
	  the path will be updated. This ensure consistency.
	* You can change the naming convention and keep the same
	  keys. Every stored config will still be valid and all
	  path will be updated automatically. If you store string
	  paths, you cannot change them all at once.
 
We will now see how to builds named path from config
and modify a named path by changing the value of a 
config key.


To create a named path from config values, you simply call a named
path and give the value for the keys you want to set::

	named = root(login='bill')
	print '-> bill folder:', named.path()
	named = root(login='bill', Basename='the_basename', Extension='doc')
	print '-> a file in bill folder:', named.path()

outputs::

	-> bill folder: my_root/bill
	-> a file in bill folder: my_root/bill/the_basename.doc


If no named path can be found, an FieldValueError is raised::

	try:
	    named = root(login='not_valid_login')
	except kabaret.naming.FieldValueError, err:
	    print '-> error in given values:', err

outputs::

	-> error in given values: Value 'not_valid_login' is invalid for 'login': should be one of ['bill', 'bob', 'joe']

If some keys were not used to create the named path, an PathItem.PathConfigError
is raised::

	try:
	    named = root(login='bob', more_key='test')
	except kabaret.naming.PathItem.PathConfigError, err:
	    print '-> error in given keys:', err

outputs::

	-> error in given keys: Unable to get {'login': 'bob', 'more_key': 'test'} under 'my_root/bob' (UserFolder). Error(s): 
	  Config keys ['more_key'] were not consumed from ['login', 'more_key'] to build 'my_root/bob' from 'my_root' (Root)


If you have a config in a dict and want to get a named path
you can use the ** notation::

	config = {'login':'bob', 'Basename':'basename', 'Extension':'doc'}
	named = root(**config)

If you want to alter (modify) a path instead of accessing a sub-path,
you can get the config, alter it and request the root to construct
a sub-path::

	config = named.config()
	config.update({'login':'joe'})
	joes_file = named.root()(**config)
	print '-> altered path:', joes_file.path()

outputs::

	-> altered path: my_root/joe/basename.doc

But you will probably want to use the convenient to() and to_config() methods
which does it all for you::

	joes_file = named.to(login='joe')
	print '-> to path:', joes_file.path()
	joes_file = named.to_config(config)
	print '-> to_config path:', joes_file.path()

outputs::

	-> to path: my_root/joe/basename.doc
	-> to_config path: my_root/joe/basename.doc

**********
Conclusion
**********

Well, that's all for this tutorial!

You now know how to define a simple naming convention that
will help your users to construct and alter valid paths.
They will have meaningful error messages when some path
does not meet the convention, but will still be able to
use them.

