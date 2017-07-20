'''



'''

import kabaret.core.apps.base

from kabaret.studio import reversion

#
#    APP
#
class VersionsApp(kabaret.core.apps.base.App):
    APP_KEY = 'VERSIONS'
    REQ_APPS = []

    def __init__(self, host):
        super(VersionsApp, self).__init__(host)

    def _host_init_done(self):
        print '#---    VERSIONS APP READY.'
        
    def get_file_history(self, filename, for_user, versions_only=True):
        client = reversion.client.Client(for_user)
        client.set_path(filename)
        try:
            return client.get_entries(versions_only=versions_only)
        except reversion.client.UnreversionedError:
            return None
    
#
#    APP Commands
#
from kabaret.core.apps.command import Command, CommandError, Arg

@VersionsApp.cmds.register
class GetHistory(Command):
    '''
    Returns a time ordered list of the revisions existing on the file.
    
    If the file is not under version control, None is returned.
    '''
    filename=Arg()
    for_user=Arg()
    versions_only=Arg(True)
    def doit(self):
        history = self.app.get_file_history(self.filename, self.for_user, self.versions_only)
        if history is None:
            return None
        ret = [ entry.to_dict() for entry in history ]
        return ret

            
            