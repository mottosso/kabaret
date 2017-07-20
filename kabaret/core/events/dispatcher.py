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

    The kabaret.core.event.dispatcher package:
        Defines the EventDispatcher class used by
        Client and AppHost to dispatch events to 
        registered handlers.
    
'''
#from kabaret.core.utils.callbacks import weak_ref

#TODO: find a way to get ride of dead weak refs

#TODO: decide if we should use weak refs here or if the 
# event handlers should de-register themselves
# (de-registering should be possible anyway since it would
# speed up the dipatch...)

class EventDispatcher(object):
    def __init__(self):
        super(EventDispatcher, self).__init__()
        self._event_handlers = {} # path_string: (etype or None, [list of weak_ref(handler)])
        
        self._depth = 0
        
    def add_handler(self, handler, app_key, path, etype):
        '''
        If app_key and path are empty, all etype events match.
        If app_key and path are empty and etype is None, all event
        match.
        '''
        path_str = (app_key and app_key+'|' or '')+('^'.join(path))
        etype_to_handlers = self._event_handlers.get(path_str, {})
        handlers = etype_to_handlers.get(etype, set())
        handlers.add(handler)
        etype_to_handlers[etype] = handlers
        self._event_handlers[path_str] = etype_to_handlers

    def remove_handler(self, handler):
        for etype_to_handlers in self._event_handlers.itervalues():
            for handlers in etype_to_handlers.itervalues():
                if handler in handlers:
                    handlers.remove(handler)
                
    def dispatch(self, event):
        # Filter event handler that match
        # the app_key, the event path and the etype if provided
        path = event.path
        path_str = event.app_key+'|'+('^'.join([str(v) for v in path]))
        etype = event.etype

        path_and_handlers = []
        for eh_path_str in self._event_handlers.iterkeys():
            if not eh_path_str or path_str == eh_path_str or path_str.startswith(eh_path_str+'^'):
                eth = self._event_handlers[eh_path_str]
                path_and_handlers.append((eh_path_str, eth.get(etype, set())))
                path_and_handlers.append((eh_path_str, eth.get(None, set())))
        
        path_and_handlers.sort() # be sure to send to roots first
        
        if 1:
            # Trigger all event handlers until
            # the event does not propagate.
            #
            # This code seams odd but is ultra fast:
            try:
                [ 
                    1/0
                    for _path, ehs in path_and_handlers 
                    for eh in ehs 
                    if (eh(event) or True) and not event.propagating 
                ]
            except ZeroDivisionError:
                # the event does not propagate
                # anymore.
                pass
        else:
            # same code but with verbose
            print '++HANDLERS:', path_and_handlers
            self._depth += 1
            s = self._depth*'  '
            print s, 'DISPATCH Start'
            for _path , ehs in path_and_handlers:
                for eh in ehs:
                    print s, '>>', eh
                    eh(event)
                    if not event.propagating:
                        break
            print s, 'DISPATCH End'
            self._depth -= 1