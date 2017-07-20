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

    The kabaret.core.syscmd module:
        Defines the SysCmd class, a utility to run 
        system commands.
    

'''

import os
import subprocess

class SysCmd(object):
    def __init__(self, executable, args=[], env=None, additional_env={}):
        super(SysCmd, self).__init__()

        self.executable = executable
        self.args = args
        self.env = env
        self.additional_env = additional_env
        
        
        self.stdout = None
        self.stderr = None
        self.cwd = None
        self.wait = False
        self.popen = None
        
    def execute(self):
        stdout = self.stdout
        stderr = self.stderr
        
        env = self.env or dict(os.environ)
        env.update(self.additional_env)
        
        executable = self.executable
        if isinstance(executable, basestring):
            executable = [executable]
        
        args = executable+self.args
        #print '----->', args, self.env, self.additional_env
        if self.wait:
            self.popen = subprocess.call(
                args=args, stdout=stdout, stderr=stderr, cwd=self.cwd,
                env=env
            )
        else:
            self.popen = subprocess.Popen(
                args=args, stdout=stdout, stderr=stderr, cwd=self.cwd,
                env=env
            )

    