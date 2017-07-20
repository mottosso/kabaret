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

    The kabaret.core.log module:
        Defines the logger "Kabaret.core".
        You can access it with kabaret.core.log.getLogger()
    
'''
import sys
import logging
from logging import DEBUG, INFO, CRITICAL, ERROR, FATAL

import kabaret.core.log

def setup(stdout_level=CRITICAL, file_level=DEBUG, filename=None):
    '''
    Configures the kabaret.core logger.
    Only the first call is effective. 
    '''
    logger = getLogger()
    if logger.handlers:
        return
    logger.setLevel(max(stdout_level, file_level))
    if stdout_level is not None:
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(stdout_level)
        logger.addHandler(soh)
    if filename is not None:
        fh = logging.FileHandler(filename)
        fh.setLevel(file_level)
        logger.addHandler(fh)
    
def getLogger():
    return kabaret.core.log.getLogger('Kabaret.core')
    