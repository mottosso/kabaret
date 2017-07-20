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

    The kabaret.core.utils package:
        This is the place for all stuffs not quite fitting
        anywhere else...
    
''' 
import os
import platform


def get_user_name():
    system = platform.system()
    if system == 'Linux':
        return os.environ['USER']
    if system == 'Windows':
        return os.environ['USERNAME']

def get_core_script(script_name):
    import kabaret.core

    if not script_name.endswith('.py'):
        script_name += '.py'
    
    path = kabaret.core.__file__
    path = os.path.normpath(path+'/../../../scripts/'+script_name)
    
    return path

def get_kababatch_script():
    return get_core_script('kababatch')

def get_kabadmin_script():
    return get_core_script('kabadmin')
