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

    The kabaret.core.cmdln.apphost module:
        Defines the CLAppHost.
    
'''
import traceback

class CLAppHost(object):
    def __init__(self, project):
        super(CLAppHost, self).__init__()
        self.project = project
        self.running = False
        self.prompt = '{project}: '
        self._builtins = {
            'quit': self.stop,
            'help': self.help,
            'apps': self.list_apps,
            'menus': self.list_menus,
            'do_menu': self.do_menu,
        }
        self.global_ctx = self._init_context()
        self.local_ctx = {}
        
    def get_prompt(self):
        return self.prompt.format(
            project=self.project.name,
        )
    
    def _init_context(self):
        ctx = {'project':self.project}
        ctx.update(self.project.apps)
        ctx.update(self._builtins)
        return ctx 
       
    def run(self):
        self.running = True
        while self.running:
            cmd = raw_input(self.get_prompt())
            cmd = cmd.strip()
            if not cmd:
                continue
            if cmd in self._builtins:
                cmd = cmd+'()'
            if cmd.startswith('>'):
                args = cmd[1:].split()
                cmd = 'do_menu('+','.join(args)+')'
            elif cmd == '?':
                cmd = 'help()'
            try:
                result = eval(cmd, self.global_ctx, self.local_ctx)
            except:
                traceback.print_exc()
            else:
                if result is not None:
                    print result
            print '' 
            
    def stop(self):
        self.running = False
        return "CLI Stopped"
    
    def help(self):
        return '''
Commands:
    quit        : stop the CLI and quit
    ?, help     : show this help
    apps        : list project apps
    menus       : show project menus
    do_menu(0,1): run an action from menu
    > 0 1       : short for do_menu(0,1)
    cmd         : run the (python) cmd
        '''
        
    def list_apps(self):
        return self.project.apps.keys()
    
    def get_menus(self):
        menus = {}
        for app in self.project.apps.values():
            for this_menu in app._api.menus.values():
                m = menus.get(this_menu.name, [])
                m.extend([(a.name, a) for a in this_menu.actions])
                menus[this_menu.name] = m
        return menus
    
    def list_menus(self):
        menus = self.get_menus()
        mi = 0
        ai = 0
        for name, menu in menus.items():
            print '#---- ', mi, name
            mi += 1
            for name, action in menu:
                print ai, name
                ai += 1
        print ''
        print 'Enter "do: <menu_index> <action index>"'
    
    def do_menu(self, menu_index, action_index):
        menus = self.get_menus()
        