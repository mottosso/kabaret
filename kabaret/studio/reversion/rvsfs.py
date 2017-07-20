'''

    reversion.rvsfs - ReVerSion FileSystem
    
    Use the reversion/mount.py script to make a repository 
    accessible as a workspace.
    
    This code only runs on Linux.
    
'''

#    error text:
#    import pprint, os, errno
#    pprint.pprint([(k, os.strerror(k)) for k in errno.errorcode.keys()])



from __future__ import with_statement

from errno import EACCES
from os.path import realpath
from threading import Lock
import os
import pwd #@UnresolvedImport not available on windows
import StringIO
import traceback

# Repo Cmds:
import datetime
import glob

from ._fuse import FUSE, FuseOSError, Operations, fuse_get_context, LoggingMixIn

from . import item

def _log(*args):
    print '====>', args

#class ReversionFileSystem(LoggingMixIn, Operations):
class ReversionFileSystem(Operations):
    _LOGIN_CACHE = {}
    
    def __init__(self, repo, mountpoint, verbose=False):
        self.verbose = verbose
            
        self._FH_TO_UPDATE = {}
        self._FH_TO_CMD = {}
        
        self.repo = realpath(repo)
        self.mountpoint = mountpoint
        
        self.repo_cmds_dir = self.repo+'/.REPO_COMMANDS'
        if not os.path.exists(self.repo_cmds_dir):
            os.mkdir(self.repo_cmds_dir)
        print 'Using repo command directory:', self.repo_cmds_dir
        
        self.rwlock = Lock()
    
    def __call__(self, op, path, *args):
        if self.verbose:
            return self.__call__verbose(op, path, *args)
        else:
            return self.__call__std(op, path, *args)

    def __call__std(self, op, path, *args):
        repo_path = self.repo + path
        try:
            return super(ReversionFileSystem, self).__call__(op, repo_path, *args)
        except OSError:
            #print op, type(op), repr(op), str(op), op == 'getattr'
            if op != 'getattr':
                print '\n\nEXCEPTION in op %r, path %r, args %r'%(op, repo_path, args)
                traceback.print_exc()
                print '\n\n'
            raise

    def __call__verbose(self, op, path, *args):
        repo_path = self.repo + path
        print '---->', op, repo_path, repr(args)
        ret = '[Unhandled Exception]'
        try:
            ret = getattr(self, op)(repo_path, *args)
            return ret
        except OSError, e:
            ret = str(e)
            traceback.print_exc()
            raise
        finally:
            print '<----', op, repr(ret)
            print ''
            
    def _check_fh(self, path, fi):
        if not self._FH_TO_UPDATE:
            return
        #print '####---- check fh', path
        alias_path = self._FH_TO_UPDATE.get(path)
        if alias_path is None:
            #print '    None..., keeping', fi.fh
            return
        del self._FH_TO_UPDATE[path]
        old = fi.fh
        os.close(fi.fh)
        fi.fh = os.open(alias_path, fi.flags)
        #print '    Using', old, fi.fh, alias_path
    
    def _get_cmd(self, fi):
        '''
        Returns the cmd associated with fi or None.
        '''
        return self._FH_TO_CMD.get(fi.fh)
    
    def _set_cmd(self, fi, cmd):
        self._FH_TO_CMD[fi.fh] = cmd
    
    def _del_cmd(self, fi):
        del self._FH_TO_CMD[fi.fh]
    
    def should_add_to_rvs(self, dir, base):
        # any dotted folder disables reversioning:
        for i in dir.split(os.path.sep):
            if i and i[0] == '.':
                return False
        
        # more complexe rules apply to basename
        return (
            base
            and base[0] not in ('.~![') 
            and '=' not in base 
            and not base.endswith('.tmp')
            and not base.startswith('AEtemp-')
        )
        
    def get_user(self):
        '''
        Returns the user of the current fuse context.
        '''
        uid, unused, unused = fuse_get_context()
        user = self._LOGIN_CACHE.get(uid)
        if not user:
            user = pwd.getpwuid(uid).pw_name
            self._LOGIN_CACHE[uid] = user
        return user
    
    def has_lock(self, dir, base):
        '''
        Returns (user_login, True) if the context user has the lock for 
        the given Reversion Item.
        Returns (user_login, False) if the user does not have the lock.
        Returns (None, False) if the given item is not reversioned.
        '''
        lock_dir = '%s/.rvs/%s/lock'%(dir, base)
        if not os.path.isdir(lock_dir):
            # Not Reversioned:
            return None, None
        user = self.get_user()
        if os.path.exists('%s/%s'%(lock_dir,user)):
            # He has the lock:
            return user, True
        # He does not have the lock
        return user, False
    
    def get_lock(self, dir, base):
        '''
        Returns 3 values:
            user, locked, was_already_locked
        
        The user string is the login of the user having the lock after the call.
        It will be None if the item is not reversioned.
        
        The locked boolean is True if the current user has the lock after the 
        call.
        
        The was_already_locked booolean is True if the current user already had
        the lock before the call.
        '''
        user, has_lock = self.has_lock(dir, base)
        if user is None:
            # Not reversioned:
            return None, False, False
            
        if has_lock:
            # He already has the lock:
            return user, True, True
            
        lock_dir = '%s/.rvs/%s/lock'%(dir, base)
        lockers = os.listdir(lock_dir)
        if lockers:
            # Lock belongs to someone else:
            return lockers[0], False, False
        
        # Take the lock:
        open('%s/%s'%(lock_dir, user), 'w').close()
        return user, True, False
        
    def access(self, path, mode):
        if not os.access(path, mode):
            raise FuseOSError(EACCES)
    
    chmod = os.chmod
    chown = os.chown #@UndefinedVariable under win
    
    def create(self, path, mode, fi):
        if '/.rvs/' in path:
            raise FuseOSError(EACCES) # Cannot create file inside /.rvs/
        if '=' in os.path.basename(path):
            raise FuseOSError(EACCES) # Cannot create file with '=' in name
        
        fi.fh = os.open(path, os.O_WRONLY | os.O_CREAT, mode)
        return 0
    
    def flush(self, path, fi):
        return os.fsync(fi.fh)
    
    def fsync(self, path, datasync, fi):
        return os.fsync(fi.fh)
    
    def getattr(self, path, fi=None):
        if path == '%s/[REVERSION_ROOT]'%self.repo:
            return dict(
                st_mode=33060, 
                st_nlink=1, 
                st_uid=0, 
                st_gid=0, 
                st_size=0, 
                st_atime=1312297386, 
                st_mtime=1311780228, 
                st_ctime=1312309053
            )
        alias_path = self._FH_TO_UPDATE.get(path)
        if alias_path is not None:
            # right after a add_to_reversion, the file turns into
            # a link and the kernel does not like it.
            # We must stat the linked file:
            path = alias_path
        st = os.lstat(path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
    
    listxattr = None
    getxattr = None
    setxattr = None
    removexattr = None
    
    def link(self, target, source):
        return os.link(source, target) #@UndefinedVariable under win
    
    def mkdir(self, path, mode):
        if os.path.exists(path):
            # Let use the default error
            return os.mkdir(path, mode)
        
        if path.startswith(self.repo_cmds_dir):
            if path == self.repo_cmds_dir:
                # Let use the default error
                return os.mkdir(path, mode)
            
            rest = path.split('/.REPO_COMMANDS')[-1]
            rest = [ i for i in rest.split('/') if i.strip() ]
            if len(rest) > 1:
                raise FuseOSError(EACCES) # Cannot create a folder in .../.REPO_COMMANDS/<user>/
            ret = os.mkdir(path, mode)
            for name in RepoCmd._registry.keys():
                with open(path+'/'+name, 'w'):
                    pass
            return ret
        
        dir, base = os.path.split(path)
        if base in ('.rvs', '.no_rvs'):
            if '/.rvs' in dir:
                raise FuseOSError(EACCES) # Cannot create .rvs inside a .rvs
            return os.mkdir(path, mode)
        
        if dir.endswith('/.rvs'):
            # This is a 'add to reversion' request
            dir, rvs = os.path.split(dir)
            if not os.path.isdir('%s/%s'%(dir, base)):
                raise FuseOSError(EACCES) # Cannot add to reversion if item is not a folder or doesnt exists.
            
            # Add the folder to reversion:
            # TODO: Ensure there is no /.rvs/ under dir/base!!!
            self.item = item.Item(self.get_user(), dir, base)
            self.item.ensure_reversioned()
        elif dir.endswith('/.no_rvs'):
            # This is a 'prevent add to reversion' request
            dir, no_rvs = os.path.split(dir)
            source = '%s/%s'%(dir, base)
            if not os.path.isdir(source):
                print 'ERROR: path is not dir:', source
                raise FuseOSError(EACCES) # Cannot prevent add to reversion if item is not a folder or doesnt exists.
            # Replace the folder by a link in the no_rvs folder:
            # TODO: Ensure there is no /.rvs/ under dir/base!!!
            print 'PREVENT ADD TO REVERSION: source=%s, dir=%s'%(source, dir)
            os.rename(source, path)
            os.symlink('./.no_rvs/%s'%base, source) #@UndefinedVariable under win
        elif '/.rvs/' in dir:
            raise FuseOSError(EACCES) # Cannot create folder inside a .rvs
        else:
            os.mkdir(path, mode)
    
    mknod = os.mknod #@UndefinedVariable under win
    
    def open(self, path, fi):
        # This can't be useful here: self._check_fh(path, fi)
        cmd = None
        if fi.flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR) != os.O_RDONLY:
            # Find out if this is a Cmd, and make it damn quick:
            if path.startswith(self.repo_cmds_dir):
                rest = path.split('/.REPO_COMMANDS/')[-1]
                print ' ----------- REPO CMD', rest
                user = self.get_user()
                u, cmd_name = rest.split('/')
                if u != user:
                    raise FuseOSError(EACCES) # Cannot run cmd of another user folder
                cmd = RepoCmd(user, cmd_name, self.mountpoint, self.repo)

            # Or find out if this is a RvsCmd, and make it quick:
            if cmd is None and '/.rvs/' in path:
                dir, more = path.split('/.rvs/')
                chunks = more.split('/')
                base = chunks.pop(0)
                sub_type = chunks.pop(0)
                if sub_type == '_COMMANDS_':
                    # It is a cmd file, bind the cmd class to the fi
                    cmd_name = chunks.pop(0)
                    if chunks:
                        # No subfolders in the _COMMANDS_ dir.
                        raise FuseOSError(EACCES) # => cmd path too long
                    cmd_class = RvsCmd.get(cmd_name)
                    if cmd_class is None:
                        # Unknown cmd
                        raise FuseOSError(EACCES) # => unknown cmd name
                    cmd = cmd_class(self.get_user(), dir, base)
                    if not cmd.allowed():
                        # Cmd needs lock but the user does not have it.
                        raise FuseOSError(EACCES) # => not cmd.allowed()
        
        fi.fh = os.open(path, fi.flags)
        if cmd:
            self._set_cmd(fi, cmd)
        return 0
    
    def read(self, path, size, offset, fi):
        self._check_fh(path, fi)
        with self.rwlock:
            os.lseek(fi.fh, offset, 0)
            return os.read(fi.fh, size)
    
    def readdir(self, path, fi):
        ret = ['.', '..'] + os.listdir(path)
        if path == '%s/'%self.repo:
            ret.append('[REVERSION_ROOT]')
        return ret
    
    def readlink(self, path):
        dir, base = os.path.split(path)
        src = os.readlink(path) #@UndefinedVariable under win
        if src == './CURR='+base:
            unused, has_lock = self.has_lock(dir, base)
            if has_lock:
                src = './WORK='+base
        return src
    
    def release(self, path, fi):
        cmd = self._get_cmd(fi)
        if cmd is not None:
            print ' -------------------- RUN', cmd
            # This file is a command.
            # We execute it before closing, and store the report in
            # the file.
            try:
                report = cmd.execute()
            except Exception, err:
                trace = traceback.format_exc()
                report = '\n# %r by %r failed: %s\n%s'%(cmd.name, cmd.user, err, trace)
            os.write(fi.fh, report)
            self._del_cmd(fi)
            
        ret = os.close(fi.fh)
            
        return ret
    
    def rename(self, old, new):
        print '#######-----######-----#### RENAME\n'*5
        print '   ==>', old, new
        # TODO: check if the links in the old and new path are resolved.
        # (we assume they are) and use abs_new = realpath(abs_new) if not.
        abs_new = '%s/%s'%(self.repo, new)
        if '/.rvs/' in old:
            # You can't rename inside the .rvs  unless the
            # user has the lock and the file is inside the 
            # working reversioned folder
            dir, more = old.split('/.rvs/')
            base, more = more.split('/',1)
            user, has_lock = self.has_lock(dir, base)
            if not has_lock:
                raise FuseOSError(EACCES) # => can't rename inside .rvs w/o having the lock.
            if not more.startswith('workspaces/%s/working/%s/'%(user, base)):
                raise FuseOSError(EACCES) # => can't rename inside .rvs if it's not a subfile inside working.

        elif os.path.exists('%s/.rvs/%s'%os.path.split(old)):
            # You can't rename a reversioned item
            raise FuseOSError(EACCES) # => can't rename a reversioned item.
        
        elif '=' in new:
            # You can't rename to a version:
            raise FuseOSError(EACCES) # => can't rename to a version file (dir/VERSION=base.ext).
        
        elif not os.path.exists(abs_new) and not os.path.exists('%s/.rvs/%s'%os.path.split(abs_new)):
            # The target does not exists, rename accepted:
            return os.rename(old, abs_new)
            
        elif '/.rvs/' in abs_new:
            # You can't rename to a reversioned file:
            raise FuseOSError(EACCES) # => can't rename to a file inside .rvs
        
        else:
            # If the new name is reversioned (is a link pointing to ./.rvs/something/:
            dir, base = os.path.split(abs_new)
            if os.path.exists('%s/.rvs/%s'%(dir,base)):
                print '    >>>>>>\n'*5, '   TARGET IS REVERSIONED'
                user, gotit, was_already_locked = self.get_lock(dir, base)
                if not gotit:
                    # Cannot get the lock = cannot overwrite the file:
                    raise FuseOSError(EACCES) # => can't rename to a reversioned item without getting the lock
                if not was_already_locked:
                    # The user just acquired the lock, we must grab empty before
                    # overwriting the file.
                    # We grab the CURRENT since you cannot overwrite a version:
                    rvs_item = item.Item(user, dir, base)
                    abs_new = rvs_item.grab(None, check_lock=False, empty=True)
                else:
                    # The user already had the lock, we must overwrite the
                    # working file.
                    if os.path.exists(abs_new):
                        # If the main file exists, it is a link:
                        abs_new = realpath(abs_new)
                    else:
                        # It the main file does not exists, someone (nuke, after FX?)
                        # probably delete it before renaming to it.
                        # We must recreate the link to CURR and use WORK:
                        os.symlink('./CURR=%s'%base, abs_new) #@UndefinedVariable on windows
                        abs_new = realpath('%s/.rvs/%s/versions/WORK/%s'%(dir,base,base))
                    # Be sure to create a new working copy before 
                    # writing to the WORK version:
                    self.truncate(abs_new, 0, None)
                # The user has the lock, let's overwrite:
                # (I do hope the kernel does not cache the attributes of the 
                # rename destination since we changed it :/)
                return os.rename(old, abs_new)

        # The new file exists but is not reversioned, we must add it to
        # reversion (unless its name prevents it) and grab it empty before
        # overwriting:
        if '/.no_rvs/' not in abs_new:
            dir, base = os.path.split(abs_new)
            if self.should_add_to_rvs(dir, base):
                user = self.get_user()
                rvs_item = item.Item(user, dir, base)
                rvs_item.add_to_reversion()
                abs_new = rvs_item.grab(None, check_lock=False, empty=True)
                # The user has the lock, let's overwrite:
                # (I do hope the kernel does not cache the attributes of the 
                # rename destination since we chenged it :/)
                return os.rename(old, abs_new)
        
        # Other cases use the default behavior:
        return os.rename(old, abs_new)
    
    def rmdir(self, path):
        if '/.rvs/' in path:
            raise FuseOSError(EACCES) # Delete inside .rvs is not allowed
        os.rmdir(path)
    
    def statfs(self, path):
        stv = os.statvfs(path) #@UndefinedVariable under win
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))
    
    def symlink(self, target, source):
        return os.symlink(source, target) #@UndefinedVariable under win
    
    def truncate(self, path, length, fi=None):
        if fi is not None:
            # This seems to never happen
            self._check_fh(path, fi)

        #print '##########################'
        #print '########################## TRUNCATE @', length 
        #print '##########################'
        if length != 0:
            # Rvs special care is only when
            # we truncate the whole file.
            with open(path, 'r+') as f:
                f.truncate(length)
            return
        
        if '/.rvs/' in path:
            # It is a reversion file, we get the dir and base
            dir, more = path.split('/.rvs/')
            chunks = more.split('/')
            base = chunks.pop(0)
            sub_type = chunks.pop(0)
            
            if sub_type in ('revisions', 'workspaces') and chunks[-1] != 'properties.rvs':
                # It is a published file (maybe inside a versionned folder)
                # This is not editable but triggers a grab when 
                # the lock can be acquired.
                user, gotit, was_already_locked = self.get_lock(dir, base)
                if gotit:
                    rvs_item = item.Item(user, dir, base)
                    if was_already_locked:
                        # The user already had the lock, this means
                        # he has a working file (and it can't be this one)
                        # so we push it before grabbing:
                        work_file = rvs_item.push_working()
                        # If it was already locked, the properties are to
                        # be kept, so we stop here and don't do the grab
                        # (Which is convenient since it prevents us to 
                        # check if this rev is the user's working (as it
                        # would grab itself))
                        #
                        # We still want to write in the new file so:
                        self._FH_TO_UPDATE[path] = work_file
                        return
                    # We must grab empty the exact revision of this path:
                    if sub_type == 'revisions':
                        revision = chunks.pop(0)
                    elif sub_type == 'workspaces':
                        revision = 'workspaces/%s/%s'%(chunks[0], chunks[1])
                    work_file = rvs_item.grab(revision, check_lock=False, empty=True)
                    # Changing the file to a link is not kool for the kernel
                    # so we keep track of the real file and use it in
                    # getattr() instead of the turned path:
                    self._FH_TO_UPDATE[path] = work_file
                    return
                else:
                    raise FuseOSError(EACCES) # cannot grab when someone else has the lock.
                    
            elif sub_type == 'workspaces':
                # It is a working file, the user must have the lock
                # and the revision must be his own working:
                workspace_user = chunks.pop(0)
                rev = chunks.pop(0)
                
                # Only the 'working' revision is editable:
                if rev != 'working':
                    raise FuseOSError(EACCES)
                
                # The workspace must match the user and the user
                # must have the lock:
                user, has_lock = self.has_lock(dir, base)
                if user != workspace_user:
                    # The user cannot modify someone else file:
                    raise FuseOSError(EACCES) # => can't edit in someone else workspace
                if not has_lock:
                    # The user does not have the lock.
                    # As this is a workspace file, we can't try to get
                    # the lock:
                    raise FuseOSError(EACCES) # => can't edit without lock

                # Only the properties.rvs file and the base are writable
                # in the user working:
                # properties.rvs is used as a standar file:
                if chunks[0] == 'properties.rvs':
                    with open(path, 'r+') as f:
                        f.truncate(length)
                    return
                    
                # base is more complex, but is required:
                if chunks[0] != base:
                    raise FuseOSError(EACCES)
                                
                if len(chunks) > 1: # more than ['file.ext']
                    # This file is part of a reversioned folder, we
                    # cannot auto-push this so we allow modification
                    # of the user's versionned folder content
                    with open(path, 'r+') as f:
                        f.truncate(length)
                    return
                
                # This is a single file reversion item, we push the 
                # current file and create an empty one instead of truncating:
                rvs_item = item.Item(user, dir, base)
                rvs_item.push_working()
                self._FH_TO_UPDATE[path] = path # no alias, type did not change...
                return
            
            elif sub_type in ('_COMMANDS_', 'log_level'):
                # It is a cmd file, let the user do what he wants
                with open(path, 'r+') as f:
                    f.truncate(length)
                return
            
            else:
                # The file is reversioned but not a workspace 
                # file nor a command file, there is no way
                # to edit it.
                raise FuseOSError(EACCES)
        
        elif '/.no_rvs/' not in path and not path.startswith(self.repo_cmds_dir):
            # This file is not reversioned.
            # It can't be part of a reversioned folder because
            # the symlinks path are resolved before getting here.
            # So we add it to reversion and grab it empty.
            dir, base = os.path.split(path)
            if self.should_add_to_rvs(dir, base):
                user = self.get_user()
                rvs_item = item.Item(user, dir, base)
                rvs_item.add_to_reversion()
                work_file = rvs_item.grab(None, check_lock=False, empty=True)
                # Changing the file to a link is not kool for the kernel
                # so we keep track of the real file and use it in
                # getattr() instead of the turned path:
                self._FH_TO_UPDATE[path] = work_file
                return 
        
        with open(path, 'r+') as f:
            f.truncate(length)
        
    def unlink(self, path):
        print '#######-----######-----#### DELETE\n'*5
        print '   ==>', path
        if '/.rvs/' in path:
            raise FuseOSError(EACCES) # Delete inside .rvs is not allowed
        
        dir, base = os.path.split(path)
        if '=' in base:
            raise FuseOSError(EACCES) # Delete reversion version file is not allowed
        
        # This was removed because afterfx (and maybe others) saves in a
        # temp file, deletes the actual file and then rename the temp file
        # (See rename on versioned target...)
        #if os.path.exists('%s/.rvs/%s'%(dir, base)):
        #    raise FuseOSError(EACCES) # Delete reversioned file is not allowed
        
        # BUT: When afterFx (and maybe others) save, they delete the file
        # and rename, but the rename will not be allowed if the user does not 
        # have the lock.
        # but the main file has been deleted already.
        # So we must allow delete only if the used can get lock
        if os.path.exists('%s/.rvs/%s'%(dir, base)):
            print '   ==> Try to Get Lock...'
            user, gotit, was_already_locked = self.get_lock(dir, base)
            print '   ==> user:%r, gotit:%r, was_already_locked:%r'%(user, gotit, was_already_locked)
            if not gotit:
                # Cannot get the lock = cannot delete the file:
                raise FuseOSError(EACCES) # => can't delete a reversioned item without getting the lock
            if not was_already_locked:
                # The user just acquired the lock, we must grab empty before
                # deleting the file so that he really has the lock
                # We grab the CURRENT since you cannot overwrite a version:
                rvs_item = item.Item(user, dir, base)
                abs_new = rvs_item.grab(None, check_lock=False, empty=True)

        print '  deleting it'
        os.unlink(path)

    utimens = os.utime
    
    def write(self, path, data, offset, fi):
        cmd = self._get_cmd(fi)
        if cmd is not None:
            cmd.buff.seek(offset, 0)
            cmd.buff.write(data)
            # We must also write in the file to prevent
            # the kernel to report IO Error..
        else:
            self._check_fh(path, fi)
        
        with self.rwlock:
            os.lseek(fi.fh, offset, 0)
            return os.write(fi.fh, data)


class _BaseCmd(object):
    def __init__(self, user):
        self.name = self.__class__.__name__
        self.user = user 
        self.buff = StringIO.StringIO()

    def execute(self):
        content = self.buff.getvalue()
        self.buff.close()
        return self._execute(content)
    
    def _execute(self, content):
        raise NotImplementedError

class RvsCmd(_BaseCmd):
    NEEDS_LOCK = True
    NEEDS_LOCKABLE = False
    _registry = {}
    
    @classmethod
    def register(cls, cmd_class):
        '''
        Class decorator for RvsCmd subclass that make
        them available.
        '''
        cls._registry[cmd_class.__name__] = cmd_class
        return cmd_class
    
    @classmethod
    def get(cls, cmd_name):
        return cls._registry.get(cmd_name)
    
    def __init__(self, user, dir, base):
        super(RvsCmd, self).__init__(user)
        self.item = None
        if None not in (dir, base):
            self.item = item.Item(user, dir, base)
        
    def allowed(self):
        '''
        Returns True if having the lock is not required to
        run thid cmd or if the user has the lock.
        '''
        if not self.NEEDS_LOCK and not self.NEEDS_LOCKABLE:
            return True
        
        has_lock = self.item.has_lock()
        if self.NEEDS_LOCKABLE:
            locker = self.item.get_locker()
            if has_lock:
                return False
            return (not locker and True or False)
        
        if self.NEEDS_LOCK:
            return has_lock
        
        return True
    
# ??? OBSOLET ???
#    def set_content(self, text):
#        self.buf = StringIO.StringIO(text)
    
    def execute(self):
        content = self.buff.getvalue()
        self.buff.close()
        return self._execute(content)
    
    def _execute(self, content):
        raise NotImplementedError


@RvsCmd.register
class Publish(RvsCmd):
    NEEDS_LOCK = True
    def _execute(self, msg):
        rev = self.item.publish(msg, check_lock=False)
        return ('\n# %s\n## Publish done by %s in revision %r'
                %
                (self.item.base, self.item.user, rev)
            )

@RvsCmd.register
class SetVersion(RvsCmd):
    NEEDS_LOCK = False
    def _execute(self, ver_rev):
        ver, rev = [ i.strip() for i in ver_rev.strip().split() ]
        self.item.set_version(ver, 'revisions', rev)
        return ('\n# %s\n## Version %r set on rev %r by %s'
                %
                (self.item.base, ver, rev, self.item.user)
            )

@RvsCmd.register
class SetCurrent(RvsCmd):
    NEEDS_LOCK = False
    def _execute(self, revision_name):
        revision_name = revision_name.strip()
        self.item.set_current(revision_name, update_prev=False)
        return ('\n# %s\n## Current version set to %r by %s'
                %
                (self.item.base, revision_name, self.item.user)
            )

@RvsCmd.register
class RemoveVersion(RvsCmd):
    NEEDS_LOCK = False
    def _execute(self, version_name):
        version_name = version_name.strip()
        self.item.remove_version(version_name)
        return ('\n# %s\n## Version %r removed by %s'
                %
                (self.item.base, version_name, self.item.user)
            )

@RvsCmd.register
class Grab(RvsCmd):
    NEEDS_LOCK = False
    NEEDS_LOCKABLE = True
    def _execute(self, rev_empty):
        rev, empty = rev_empty.strip().rsplit(' ', 1)
        if empty.strip() == '[EMPTY]':
            empty = True
        else:
            empty = False
        rev = rev.strip()
        if rev == 'None':
            rev = None
        self.item.grab(rev, check_lock=True, empty=empty) # check_lock might not be useful here...
        return ('\n# %s\n## Revision %r grabed by %s'
                %
                (self.item.base, rev, self.item.user)
            )

@RvsCmd.register
class TrashWork(RvsCmd):
    NEEDS_LOCK = False
    def _execute(self, option):
        force = False
        if option.strip() == '[FORCE]':
            force = True
        self.item.drop_working(force=force)
        return ('\n# %s\n## Working revision trashed by %s'
                %
                (self.item.base, self.item.user)
            )

@RvsCmd.register
class Steal(RvsCmd):
    def _execute(self, not_used_arg):
        self.item.steal_working()
        return ('\n# %s\n## Working revision stolen by %s'
                %
                (self.item.base, self.item.user)
            )

    def allowed(self):
        '''
        Returns True if the lock is owned by someone else.
        '''
        if self.item.has_lock():
            return False
        return self.item.get_locker() is not None

class RepoCmd(_BaseCmd):
    _registry = {}
    
    @classmethod
    def register(cls, cmd_class):
        '''
        Class decorator for RepoCmd classes that make
        them available.
        cmd_class should be a subclass of _RepoCmdClass.
        '''
        cls._registry[cmd_class.__name__] = cmd_class
        return cmd_class
    
    @classmethod
    def get(cls, cmd_name):
        return cls._registry.get(cmd_name)
    
    def __init__(self, user, cmd_name, mountpoint, repo):
        super(RepoCmd, self).__init__(user)
        self.cmd_name = cmd_name
        self.mountpoint = mountpoint
        self.repo = repo
        
    def _execute(self, arg_string):
        cmd_class = self.__class__.get(self.cmd_name)
        if cmd_class is None:
            raise Exception('Command failed: Unknown command %r.'%(self.cmd_name,))
        cmd = cmd_class(self.user, self.mountpoint, self.repo)
        args = eval(arg_string)
        if isinstance(args, basestring):
            args = (args,)
        return cmd.do(*args)

class _RepoCmdBase(object):
    def __init__(self, user, mountpoint, repo):
        self.user = user
        self.mountpoint = mountpoint
        self.repo = repo
        
    def do(self, *args):
        '''
        Raise an Exception or returns a string describing
        what happent.
        If the returned string contains the word 'failed', 
        the caller will consider the job not done and
        should be able to guess why it is so by reading the
        returned string in its whole.
        '''
        raise NotImplementedError

@RepoCmd.register
class RepoCmdTest(_RepoCmdBase):
    def do(self, *args):
        print 'new repo cmd', args
        return 'This is the test command\nArgs were: %r'%(args,)


def mount(repo, mountpoint, verbose=False):
    FUSE(
        ReversionFileSystem(repo, mountpoint, verbose=verbose), 
        mountpoint, 
        raw_fi=True, 
        foreground=True, 
        allow_other=True, 
        debug=False
    )
        
