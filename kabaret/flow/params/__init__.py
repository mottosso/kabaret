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

    The kabaret.flow.params package.
    Defines the base Param and sub-classes needed to build a great flow.
    
    A Node class contain one or more Param.
    It uses the Param to read or compute a value.
    A Param can use another Param as source so that
    a Node can affect another.
    
    A Param is a descriptor for a ParamValue. 
    To add a Param to a Node class, you must store a Param instance in
    the class definition:
        class MyNode(Node):
            my_param = Param()
    You can then access the ParamValue as an attribute of the node
    instance:
        param_value = my_node.my_param
        value = param_value.get()
    
'''