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

    The kabaret.flow.relations package.
    Defines all the possible Relations between flow Nodes.
    
    The flow is composed of nodes related which each others.
    
    The simplest relation is 'Child'.
    A Child node is 'contained' in the parent node and is created
    as soon as the parent is created.
    This relation is useful to package some behavior in specialized
    Node class so that you can reuse it somewhere else.
    It can also be used to simply group things together. 
    
    The 'One' and 'Many' relations are related to the 'case' concept.
    For example, a Film contains several Shots.
    You don't want to write a specific Node class for each film, you
    want to write a Film Node that contains several (one per case)
    Shots Nodes.
    This is a Many relation.
    The One and Many related nodes are lazily created.
    That means you can build a huge flow using those relations.
    
'''