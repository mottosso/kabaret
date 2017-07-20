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

    The kabaret.gui package.

'''
import os

_ENV_QT_WRAPPER = 'KABARET_QT_WRAPPER'
_QTS = None

def import_qt():
    global _QTS
    if _QTS is not None:
        return _QTS
    
    global _ENV_QT_WRAPPER
    
    wrapper = os.environ.get(_ENV_QT_WRAPPER, 'PyQt4')
    
    if wrapper == 'PyQt4':
        try:
            from PyQt4 import QtCore, QtGui
        except ImportError:
            import traceback
            traceback.print_exc()
            raise ImportError(
                'kabaret.gui could not import PyQt4 (The env var %r is unset or set to PyQt4).'%(
                    _ENV_QT_WRAPPER,
                )
            )
            
    elif wrapper == 'PySide':
        try:
            from PySide import QtCore, QtGui
        except ImportError:
            raise ImportError(
                'kabaret.gui could not import PySide (The env var %r is set to PySide).'%(
                    _ENV_QT_WRAPPER,
                )
            )
    
    else:
        try:
            from PyQt4 import QtCore, QtGui
        except ImportError:
            try:
                from PySide import QtCore, QtGui
            except ImportError:
                raise ImportError('kabaret.gui requires either PyQt4 or PySide to be installed.')
    
    _QTS = QtCore, QtGui
    return _QTS
