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

    The kabaret.version module:
    Use kabaret.version.get() to find out the version you have installed.
'''

raise Exception('This module is obslolete. sorry.')

# (
#    (Major, Minor, [Micros]),
#    [(Alpha/Beta/rc marker, version)],
# )
__version_info__ = ((0, 1, 0), ('b', 2))

def get():
    global __version_info__
    return (
        '.'.join(str(x) for x in __version_info__[0]) 
        +''.join(str(x) for x in __version_info__[1])
    )
