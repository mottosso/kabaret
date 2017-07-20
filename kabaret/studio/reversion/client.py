'''


'''

import os
import datetime
import pprint
from functools import wraps
from collections import defaultdict


#TOTO: All this should be in a separate package "kabaret.reversion"


class Error(Exception):
    pass

class PathError(Error):
    pass

class LockError(Error):
    pass

class InvalidClientError(Error):
    def __init__(self, client):
        msg = (
            'This client is invalid:',
            '    dir = %r'%client.dir,
            '    base = %r'%client.base,
        )
        super(InvalidClientError, self).__init__('\n'.join(msg))

class UnreversionedError(Error):
    def __init__(self, client):
        msg = (
            'This client iten is not reversioned:',
            '    dir = %r'%client.dir ,
            '    base = %r'%client.base,
        )
        super(UnreversionedError, self).__init__('\n'.join(msg))

class Entry:
    '''
    An Entry represents a revision or a work of an reversion item.
    '''
    def __init__(self, timestamp, name, rev_type, owner, message, versions):
        self.name = name
        self.time = datetime.datetime.fromtimestamp(timestamp)
        self.rev_type = rev_type
        self.owner = owner
        self.message = message
        self.versions = versions
        
    def __len__(self):
        return 3+len(self.props)

    def to_dict(self):
        return {
            'name':self.name,
            'time':self.time,
            'rev_type':self.rev_type,
            'owner':self.owner,
            'message':self.message,
            'versions':self.versions
        }
        
def _needs_valid(f):
    '''
    This decorator ensures the wrapped Client method
    will not be called if the client is not valid.
    '''
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        if not self.is_valid():
            raise InvalidClientError(self)
        return f(self, *args, **kwargs)
    return wrapped

def _needs_reversioned(f):
    '''
    This decorator ensures the wrapped Client method
    will not be called if the client item is not
    reversioned.
    '''
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        if not self.is_reversioned:
            raise UnreversionedError(self)
        return f(self, *args, **kwargs)
    wrapped.__doc__ += '''
    
        The current item must be reversioned or a UnreversionedError will
        raise.
'''
    return wrapped

class Client(object):
    '''
    The Client is used to access and manipulate a reversion item.
    
    In order to operate, the client must be configured to point on
    an item with one of the convenient methods:
        set_path(item_path)
        set_item(item_dir, item_base)
        
    '''
    VALID = 'VALID'
    CURRENT = 'CURR'
    PREV = 'PREV'
    WORK = 'WORK'
    DYNAMIC_VERSIONS = ( # ordered by prefered usage when several vers on single rev
        WORK,
        CURRENT, 
        VALID, 
        PREV,
    )

    def __init__(self, user=None):
        self.user = user or os.environ['USERNAME']
        self.clear_item()
        
    def clear_item(self):
        self.dir = None
        self.base = None
        self.is_reversioned = False
        self._setup_item(False)
           
    def set_path(self, path):
        '''
        Change the item to operate on.
        
        The given path may be inside the reversion folder,
        or contain a version tag ('version=file.ext')
        
        If you know the dir and base of the item, consider using the 
        set_item() method which is faster and does not require filesystem
        access.
        '''
        self.dir = None 
        self.base = None
        self.is_reversioned = False
        
        self.dir, self.base, self.is_reversioned = cut_path(path)
        self._setup_item(False)
        
    def set_item(self, dir, base):
        '''
        Change the item to operate on.
        '''
        self.dir = dir
        self.base = base
        self._setup_item()
    
    def _setup_item(self, update_is_reversioned=True):
        self.rvs_base = '%s/.rvs/%s'%(self.dir, self.base)
        self.work_path = '%s/workspaces'%self.rvs_base
        self.workspace = '%s/%s'%(self.work_path, self.user)
        self.working_dir = '%s/working'%self.workspace
        self.lock_path = '%s/lock'%self.rvs_base
        self.lock_file = '%s/lock/%s'%(self.rvs_base, self.user)
        self.revs_path = '%s/revisions'%self.rvs_base
        self.vers_path = '%s/versions'%self.rvs_base
        self.cmds_path = '%s/_COMMANDS_'%self.rvs_base
        self.log_file = '%s/log'%self.rvs_base
        self.log_level_file = '%s/log_level'%self.rvs_base
        self.item_path = '%s/%s'%(self.dir, self.base)
        
        self._locker = None
        if update_is_reversioned:
            self.is_reversioned = os.path.exists(self.rvs_base)
        
    def is_valid(self):
        '''
        Returns True if the client has an item configured.
        '''
        return self.dir is not None and self.base is not None

    def exists(self):
        return os.path.exists(self.item_path)
    
    def _get_properties_from_file(self, path):
        properties = {}
        if not os.path.exists(path):
            return properties

        #execfile(self.prop_file, map)
        # execfile does not work :/
        # so
        with open(path, 'r') as r:
            code = r.read()
        exec(code)
        return properties
    
    @_needs_valid
    def add_to_reversion(self):
        '''
        Setup the client path (which must be a folder) to be  managed
        by reversion.
        The client is_reversioned attribute must be False before calling 
        this.
        '''
        os.makedirs(self.rvs_base)
        self.is_reversioned = True
        
    @_needs_valid
    def prevent_reversion(self):
        '''
        Setup the client path (which must be a folder) to be  managed
        by reversion.
        The client is_reversioned attribute must be False before calling 
        this.
        '''
        if self.is_reversioned:
            raise Error('Cannot prevent_reversion on reversioned path: %s'%self.item_path)
        os.makedirs('%s/.no_rvs/%s'%(self.dir, self.base))
        self.is_reversioned = False
        
    @_needs_reversioned
    def get_entries(self, versions_only):
        '''
        Return a list of Entry().

        If versions_only is True, only the revisions having a
        version are returned.
        
        '''
                    
        locker = self.get_locker(force_read=True)
        entries = []
        
        # get rev to versions
        rev_to_vers = defaultdict(list)
        for ver in os.listdir(self.vers_path):
            with open('%s/%s/revision.rvs'%(self.vers_path,ver), 'r') as r:
                rev = r.read().strip()
                rev_to_vers[rev].append(ver)

        #(timestamp, 'r000000', 'r', 'llt', 'the message', ['TEST', _rvs_item.Item.VALID], {}),
        data = []
        if not versions_only:
            # get workings
            for user in os.listdir(self.work_path):
                for w in os.listdir('%s/%s'%(self.work_path, user)):
                    if not os.path.exists('%s/%s/%s/%s'%(self.work_path, user, w, self.base)):
                        # this is a working without the base, probably published (moved to a rev)
                        continue
                    #props = self._get_properties_from_file('%s/%s/%s/properties.rvs'%(self.work_path, user, w))
                    if w == 'working':
                        timestamp_file = '%s/%s/%s/timestamp.rvs'%(self.work_path, user, w)
                        if os.path.exists(timestamp_file):
                            with open(timestamp_file, 'r') as r:
                                timestamp = int(r.read())
                        else:
                            # This is a broken revision (might be a stolen one...)
                            # We just skip it.
                            continue
                    else:
                        timestamp = int(w[1:].split('.',1)[0])
                    rev = '%s/%s'%(user,w)
                    row = [timestamp, rev, 'w', user, '', rev_to_vers[rev], ]#props]
                    data.append(row)
                    
            # get revisions 
            for rev in os.listdir(self.revs_path):
                with open('%s/%s/message.rvs'%(self.revs_path, rev), 'r') as r:
                    msg = r.read().strip()
                with open('%s/%s/user.rvs'%(self.revs_path, rev), 'r') as r:
                    user = r.read().strip()
                #props = self._get_properties_from_file('%s/%s/properties.rvs'%(self.revs_path, rev))
                timestamp = int(rev[1:].split('.',1)[0])
                row = [timestamp, rev, 'r', user, msg, rev_to_vers[rev], ]#props]
                data.append(row)
        
        else:
            # versions_only is True
            for rev, vers in rev_to_vers.items():
                try:
                    # Most chance are that it's a version on a revision: 
                    with open('%s/%s/message.rvs'%(self.revs_path, rev), 'r') as r:
                        msg = r.read().strip()
                except IOError:
                    # It it's not on a revision, it's on the current worked file
                    type = 'w'
                    msg = ''
                    user = rev.split('/', 1)[0]
                    with open('%s/%s/timestamp.rvs'%(self.work_path, rev), 'r') as r:
                        timestamp = int(r.read())
                else:
                    type = 'r'
                    with open('%s/%s/user.rvs'%(self.revs_path, rev), 'r') as r:
                        user = r.read().strip()
                    timestamp = int(rev[1:].split('.',1)[0])
                #props = self._get_properties_from_file('%s/%s/properties.rvs'%(self.revs_path, rev))
                row = [timestamp, rev, type, user, msg, vers, ]#props]
                data.append(row)


        data.sort(cmp=lambda a,b:cmp(b[0],a[0]))
        
        for d in data:
            if d[1] == 'working':
                if d[3] != locker:
                    continue
            elif versions_only and not d[5]:
                continue
            r = Entry(*d)
            entries.append(r)
        
        return entries

    @_needs_reversioned
    def has_lock(self):
        '''
        Returns True if the current user has the lock.
        '''
        return os.path.exists(self.lock_file)

    @_needs_reversioned
    def get_locker(self, force_read=False):
        '''
        Returns the login of the user having the lock on the client item.
        If no one is working on it, an empty string is returned.
        
        The result is cached so that only first call has a
        cost.
        
        '''
        if not force_read and self._locker is not None:
            return self._locker
        lock_files = os.listdir(self.lock_path)
        self._locker = lock_files and lock_files[0] or ''
        return self._locker

    @_needs_reversioned
    def get_log_file(self):
        '''
        Returns the path of the log file for the current item.
        '''
        return self.log_file
    
    @_needs_reversioned
    def get_log_level(self):
        '''
        Returns the log level of the current item.
        The log level is an integer threshold for the item events to be logged:
            the higher, less message in the log file.
        '''
        with open(self.log_level_file, 'r') as r:
            lvl = r.read()
            try:
                lvl = int(lvl)
            except ValueError:
                lvl = 0
        return lvl

    @_needs_reversioned
    def set_log_level(self, lvl):
        '''
        Change the log level of the current item.
        The log level is an integer threshold for the item events to be logged:
            the higher, less message in the log file.
        '''
        with open(self.log_level_file, 'w') as w:
            w.write(`lvl`)

    @_needs_reversioned
    def get_version(self, version_name=None):
        '''
        Returns the revision type and name of the given
        version.
        
        If the version is None, the current version is y used
        (which may be the work version, depending on the user)
        
        If the version does not exists, (None, None) is 
        returned.
        '''
        if version_name is None:
            if self.has_lock():
                version_name = self.WORK
            else:
                version_name = self.CURR
                
        revision_file = '%s/%s/revision.rvs'%(self.vers_path,version_name)
        if not os.path.exists(revision_file):
            return None, None
        
        with open(revision_file, 'r') as r:
            name = r.read().strip()
        if name.endswith('/working'):
            user, working = name.split('/', 1)
            type = 'workspaces/%s'%user
            name = working
        else:
            type = 'revisions'
        return type, name
    
    @_needs_reversioned
    def read_properties(self, version_name=None):
        '''
        Returns the properties (a dict) of the current item.
        If the version_name is None, the current version is used.
        '''
        properties = {}
        
        type, name = self.get_version(version_name)
        if type is None:
            return properties
        
        prop_file = '%s/%s/%s/properties.rvs'%(self.rvs_base, type, name)
        if not os.path.exists(prop_file):
            return properties

        #execfile(self.prop_file, map)
        # execfile does not work :/
        # so
        with open(prop_file, 'r') as r:
            code = r.read()
        exec(code)
        return properties
    
    @_needs_reversioned
    def write_properties(self, properties):
        '''
        Change the properties of the 'WORK' version.
        '''
        if not self.has_lock():
            raise LockError('You can\'t write properties without having the lock')
        
        type, name = self.get_version('WORK')
        prop_file = '%s/%s/%s/properties.rvs'%(self.rvs_base, type, name)
        with open(prop_file, 'w') as w:
            w.write('properties = '+pprint.pformat(properties))
    
    @_needs_reversioned
    def set_version(self, version_name, revision_name):
        '''
        Sets the given version on the given revision.
        The version is created if needed.
        
        Returns a human readable string telling what happened
        and a boolean which is False if something went 
        wrong.
        '''
        cmd_file = '%s/SetVersion'%self.cmds_path
        with open(cmd_file, 'w') as w:
            w.write('%s %s'%(version_name, revision_name))
        with open(cmd_file, 'r') as r:
            ret = r.read()
        return ret, 'failed' not in ret
        
    @_needs_reversioned
    def remove_version(self, version_name):
        '''
        Remove the given version from the given revision.
        
        Returns a human readable string telling what happened
        and a boolean which is False if something went 
        wrong.
        '''
        cmd_file = '%s/RemoveVersion'%self.cmds_path
        with open(cmd_file, 'w') as w:
            w.write(version_name)
        with open(cmd_file, 'r') as r:
            ret = r.read()
        return ret, 'failed' not in ret
        
    @_needs_reversioned
    def publish(self, msg):
        '''
        Publish the item with the given message.
        '''
        cmd_file = '%s/Publish'%self.cmds_path
        with open(cmd_file, 'w') as w:
            w.write(msg)
        with open(cmd_file, 'r') as r:
            ret = r.read()
        return ret, 'failed' not in ret
        
    @_needs_reversioned
    def grab(self, revision_name=None, empty=True):
        '''
        Grabs a revision to creates a new working copy.
        
        Returns a string and a bool:
            message, ok
        If ok is False, you should inspect the message.
        
        The given revision_name may be the name of a revision or its index in 
        the revision list. (0 is first, -1 is last)
        See self.get_version() to get the revision of a version.
        If the given revision_name is None, the CURR version is used.
        If the given revision_name contains a '/', it must be in the
        form revision_type/revision_name.
        
        If empty is True, the grab will be empty.
        (The properties are always copied)
        '''
        cmd_file = '%s/Grab'%self.cmds_path
        with open(cmd_file, 'w') as w:
            w.write('%s %s'%(revision_name, empty and '[EMPTY]' or 'not_empty'))
        with open(cmd_file, 'r') as r:
            ret = r.read()
        return ret, 'failed' not in ret

    @_needs_reversioned
    def trash(self, force_user=False):
        '''
        Release the lock to let someone else modify the current version.
        This means all modifications will be lost.

        If force_user is False, the user calling this must match
        the user having the lock.
        
        Returns a human readable string telling what happened
        and a boolean which is False if something went 
        wrong.
        '''
        cmd_file = '%s/TrashWork'%self.cmds_path
        with open(cmd_file, 'w') as w:
            w.write('%s'%(force_user and '[FORCE]' or 'do_not_force'))
        with open(cmd_file, 'r') as r:
            ret = r.read()
        return ret, 'failed' not in ret
        
    @_needs_reversioned
    def steal(self):
        '''
        Transfers the current WORK to the current user.

        Returns a human readable string telling what happened
        and a boolean which is False if something went 
        wrong.
        '''
        cmd_file = '%s/Steal'%self.cmds_path
        with open(cmd_file, 'w') as w:
            w.write('just do it!')
        with open(cmd_file, 'r') as r:
            ret = r.read()
        return ret, 'failed' not in ret
        

def cut_path(path):
    '''
    Return the dir and base of the item pointed by the
    given path, and a boolean telling if the item is 
    reversioned.
    '''
    # If path is inside the rvs folder, use it to get dir and base:
    rvs = '/.rvs/'
    if rvs in path:
        dir, more = path.split(rvs)
        base, more = more.split('/',1)
        if not os.path.exists('%s/%s'%(dir, base)):
            raise PathError('Path inside /.rvs/ but item does not exists: %r'%path)
        return dir, base, True
        
    # If path has a version (possibly in the middle of it),
    # we use it to know where the rvs folder should be:
    if '=' in path:
#        print 'cutting with version', path
        dir_ver, base_sub = path.split('=',1)
#        print 'dir_ver, base_sub', dir_ver, base_sub
        dir, version = os.path.split(dir_ver)
#        print 'dir, version', dir, version
        if '/' in base_sub:
            base, subpath = base_sub.split('/', 1)
        else:
            base, subpath = base_sub, None
#        print 'base, subpath', base, subpath
        if not os.path.isdir('%s/.rvs/%s'%(dir, base)):
            raise PathError('Path has a version but item is not reversioned: %r'%path)
        return dir, base, True
    
    # Last chance: seek the rvs folder along the path.
    reversioned = False
    base = None
    d, n = os.path.split(path)
    drive, d = os.path.splitdrive(d)
    while d.strip('/'):
#        print '--------?', d
        if os.path.exists('%s%s/[REVERSION_ROOT]'%(drive,d)):
#            print '  Reached Workspace Root'
            break
        if os.path.exists(drive+d+rvs+n):
#            print '------------ YES'
            dir = drive+d
            base = n
            reversioned = True
            break
        d, n = os.path.split(d)
        
    if not reversioned:
        # no rvs folder found: the path is not yet reversioned
        dir, base = os.path.split(path)
    
    return dir, base, reversioned
    