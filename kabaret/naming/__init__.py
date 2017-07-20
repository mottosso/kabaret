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
    The kabaret.naming package.
    
    This package let you describe path naming conventions and check for
    conformity against it.
    When a string is turned into a named path, it can generate a config 
    (a dict) that can later rebuilt an equivalent named path/string.
    This is thus easy to logically alter a path by changing the value of
    some keys in the config and build a new named path.
    
    The naming convention being build by subclassing, it is easy to 
    give each path type some specific functionalities.
    For example, if you described a path to a folder containing files
    under version control, you can add the check_in() and check_out()
    method to the class representing it.
    
    How to build up your naming convention:
    
    The kabaret.naming.PathItem represent a portion of a path (a 
    folder or a file).
    It has a name and knows what type of path item are allowed under
    it.
    
    By subclassing PathItem and restricting the list of possible contained
    PathItem you describe several valid file/folder path.
    
    The name of a PathItem is a kabaret.naming.Field.
    This class is able to validate or reject a string for its value.
    Subclasses add specific behavior, for example:
      - kabaret.naming.ChoiceField can accept several predefined values
      - kabaret.naming.IndexingField only accept value with a defined prefix
      followed by digits.
      - kabaret.naming.CompoundField is composed of several Fields.
    
    By setting the name field of your PathItem subclasses you describe
    how to identify this type of PathItem.
    
    The PathItem and the Field can produce a config that represent them
    under their root item.
    Each Field has a 'KEY' class attribute depicting the key they generate
    in the config.
    By subclassing a Field class you can control the key of the generated
    config.
    
    By using the same field in several PathItems you can ensure consistency
    in the redundant information found in the path.
    For example in:
        /my_project/user/topic/topic_user.txt
    The user folder would be described by a subclass 'UserFolder' of PathItem having
    a subclass 'UserName' of Field as name.
    The topic would do the same with classes 'TopicFolder' and 'TopicName'.
    The file would be describe in a class with a name using a CompoundField which
    contains a UserName and a TopicName separated by a '_'.
    So that those are not valid:
        /my_project/bob/summerjam/summerjam_bill.txt
        /my_project/bob/beachvoley/summerjam_bob.txt
    
    It is important to note that even not valid, those two paths will still 
    produce a functional PathItem.
    It will not be of the type you declared but it will be a WildItem.
    All PathItem have a is_wild() method returning True if they are WildItem.
    WildItem objects have a 'why' attribute that contains a exception describing
    why none of the known children PathItem types were acceptable for the given
    path or config.
    
    See kabaret.naming.examples for concrete example and tutorials.
'''

from .path import PathItem, FileOrFolder, WildItem
from .fields import * # yes, I know... :P


