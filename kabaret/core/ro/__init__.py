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

    The kabaret.core.ro package:
        Define all remote object related
        stuffs.
    
'''
import socket
import md5

import Pyro4 as _Pyro4
from Pyro4.errors import CommunicationError

# Reset the pyro config without using env
# to avoid exploits:
_Pyro4.config.reset(useenvironment=False)

# Config pyro for kabaret
#TODO: doesn't this messes up the pyro env of other module?
_Pyro4.config.AUTOPROXY = True # needed for the callbacks
_Pyro4.config.NS_HOST = 'namesever' # do not prefer the localhost for name service

# Setup the HMAC_KEY.
# users w/o access to this code should not
# be able to reproduce this:
import hmac
import hashlib
import base64
hmac_key = base64.b64encode(
    hmac.new(
        b'dee909', msg='kabanet', digestmod=hashlib.sha256
    ).digest()
).decode()
_Pyro4.config.HMAC_KEY = str(hmac_key)

def this_host(name=True):
    '''
    Return the current host name if 'name' is True
    or its IP address if 'name' is False
    '''
    hostname = socket.gethostname()
    return name and hostname or socket.gethostbyname(hostname)


