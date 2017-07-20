'''

    The reversion Item is used by the reversion filesystem to
    manipulate files under reversion.
    

'''

import os
import re
import time
import shutil
import traceback
import datetime
#import pprint
from functools import wraps

class RvsError(Exception):
    pass

class LockError(RvsError):
    pass

class PropertyError(RvsError):
    pass

class LoggedObject(object):
    '''
    The LoggedObject defines a log behavior for its method calls.
    It is the base class for the reversion.item.Item class.
    '''
    LOGLVL_TOP = 100
    LOGLVL_HI  = 70
    LOGLVL_LOW = 30
    LOGLVL_OFF = 0
    

    @staticmethod
    def logged_meth(level=0):
        '''
        This method decorator will log the calls to the decorated 
        method with the given log level.
        '''
        def _logged_meth(f):
            @wraps(f)
            def wrapped(self, *args, **kwargs):
                fn = f.__name__
                self.log('%s(*%r,**%r)'%(fn, args, kwargs), level)
                self._log_indent += 1
                try:
                    ret = f(self, *args, **kwargs)
                except Exception, err:
                    self.log('FAILED %s%r: (*%r,**%r) %s'%(fn, args, kwargs, err, err), level=100)
                    self._log_indent += 1
                    self.log(traceback.format_exc(), level=100)
                    self._log_indent -= 1
                    raise
                finally:
                    self._log_indent -= 1
                self.log('---> %r'%ret, level)
                return ret
            return wrapped
        return _logged_meth

    def __init__(self, user_name):
        super(LoggedObject, self).__init__()
        self._log_file = None
        self._log_level_file = None
        self._log_level = self.LOGLVL_HI
        self._log_indent = 0
        self._log_on = False
        self.user = user_name
        
    def _setup_log(self, log_file, log_level_file=None):
        '''
        Configure and activate the log.
        '''
        self._log_file = log_file
        self._log_level_file = log_level_file
        self._log_on = os.path.isdir(os.path.dirname(self._log_file))
        if not self._log_on:
            return
            
        self.log('setting up log.')
        if self._log_level_file is not None:
            if os.path.exists(self._log_level_file):
                with open(self._log_level_file, 'r') as r:
                    lvl = r.read()
                try:
                    lvl = int(lvl)
                    self._log_level = lvl
                except ValueError:
                    pass
            else:
                with open(self._log_level_file, 'w') as w:
                    w.write('%i'%self._log_level)

                    
    def log(self, msg, level=0):
        '''
        Log the message if the log is set up and 
        if the given level is higher than self._log_level
        '''
        if not self._log_on or self._log_level > level:
            return
        with open(self._log_file, 'a') as w:
            indent_str = self._log_indent*'  '
            w.write('%s [%3i]%8s: %s%s\n'%(datetime.datetime.now().isoformat(), level, self.user, indent_str, msg))
        

class Item(LoggedObject):
    VALID = 'VALID'
    CURRENT = 'CURR'
    PREV = 'PREV'
    WORK = 'WORK'
    
    _auto_version_cap = re.compile('version:(\w+)')
    
    def __init__(self, user, dir, base):
        super(Item, self).__init__(user)

        self.dir = dir
        self.base = base
        
        self.rvs_base = '%s/.rvs/%s'%(self.dir,self.base)
        self.workspace = '%s/workspaces/%s'%(self.rvs_base, user)
        self.working_dir = '%s/working'%self.workspace
        self._setup_log()
    
    def _setup_log(self):
        super(Item, self)._setup_log('%s/log'%self.rvs_base, '%s/log_level'%self.rvs_base)
        
    @LoggedObject.logged_meth(LoggedObject.LOGLVL_LOW)
    def ensure_reversioned(self):
        '''
        Create the reversion file tree if needed.
        Returns True if the item was not yet reversioned.
        '''
        if not os.path.isdir(self.rvs_base):
            self.add_to_reversion()
            return True
        return False
    
    @LoggedObject.logged_meth(LoggedObject.LOGLVL_TOP)
    def add_to_reversion(self):
        # Create the .rvs tree
        os.makedirs(self.rvs_base)
        self._setup_log()
        
        os.mkdir('%s/workspaces'%self.rvs_base)
        os.mkdir('%s/lock'%self.rvs_base)
        #os.chmod(self.lock_path, 0555)
        os.mkdir('%s/revisions'%self.rvs_base)
        os.mkdir('%s/versions'%self.rvs_base)
        
        cmds_path = '%s/_COMMANDS_'%self.rvs_base
        os.mkdir(cmds_path)
        
        # Create templates for the commands:
        with open(cmds_path+'/Publish', 'w') as w:
            w.write('Write your publication message here and save the file.\n')
        with open(cmds_path+'/SetVersion', 'w') as w:
            w.write('Save this file with "version_name revision_name" to set a version on a revision.\n')
        with open(cmds_path+'/RemoveVersion', 'w') as w:
            w.write('Save this file with "version_name" to remove a version.\n')
        with open(cmds_path+'/Grab', 'w') as w:
            w.write('Save this file with "revision_name" to grab a revision or no content to grab empty.\n')
        with open(cmds_path+'/Steal', 'w') as w:
            w.write('Save this file with any content to steal the current working files.\n')
        with open(cmds_path+'/TrashWork', 'w') as w:
            w.write('Save this file with any content to trash your working copy and release the lock.\nIf the saved content is "[FORCE]", the files will be trashed event if the locker is not you.\n')
        
        # Create the first revision from the real file
        rev_path, rev = self.create_name(type='revisions')
        
        with open('%s/%s/message.rvs'%(rev_path,rev), 'w') as w:
            w.write("Initial revision created by %r."%self.user)
        
        prop_file = '%s/%s/properties.rvs'%(rev_path,rev)
        with open(prop_file, 'w') as w:
            w.write("# No property defined yet for %r."%self.base)
        
        # Move the file in the revision
        src = '%s/%s' % (self.dir, self.base)
        dst = '%s/%s/%s' % (rev_path, rev, self.base)
        os.rename(src, dst)
        
        # Make the created revision the current one
        # (this will update the main link)
        self.set_current(rev)
    
    def has_lock(self):
        '''
        Returns True if the user has the lock on this item.
        '''
        return os.path.exists('%s/lock/%s'%(self.rvs_base, self.user))

    def get_locker(self):
        '''
        Returns the name of the user having the lock or None if no user
        has it.
        '''
        if self.has_lock():
            return self.user
        lock_dir = '%s/.rvs/%s/lock'%(self.dir, self.base)
        lockers = os.listdir(lock_dir)
        if lockers:
            return lockers[0]
        return None
    
    def create_name(self, type, name=None):
        '''
        Creates a new name in the type folder, returns the
        absolute path of the type folder and the name.
        
        If name is None, the current time is used.
        
        '''
        if name is None:
            name = '%i'%time.time()
        
        parent_folder = '%s/%s'%(self.rvs_base, type)
        if not os.path.exists(parent_folder):
            os.makedirs(parent_folder)
        
        prefix = type[0]
        abs = '%s/%s%s'%(parent_folder, prefix, name)
        tries = 1
        subformat = '.%03i'
        while os.path.exists(abs):
            abs = '%s/%s%s%s'%(parent_folder, prefix, name, subformat%tries)
            tries += 1
            if tries > 999:
                raise RvsError('Unable to create name %r under %r'%(name, parent_folder))
        
        dir, base = os.path.split(abs.rstrip('/'))
        
        os.mkdir(abs)
        with open('%s/user.rvs'%abs, 'w') as w:
            w.write(self.user)
        with open('%s/revision.rvs'%abs, 'w') as w:
            w.write(base)
        
        return dir, base
    
    def get_names(self, type):
        '''
        Returns a time ordered list of the existing type name
        for this item. 
        '''
        try:
            return sorted(os.listdir('%s/%s'%(self.rvs_base,type)))
        except OSError:
            return []
    
    def resolve_name(self, type, name):
        '''
        Turns an int to a revision name:
            0 = first
            1 = second
            ...
            -1 = last
        
        If the given revision_name is not an int, it is
        returned unchanged.
        '''
        try:
            rev_index = int(name)
        except ValueError:
            return name
        names = self.get_names(type)
        try:
            return names[rev_index]
        except IndexError:
            raise NameError('%s index %r out of range in %r.'%(type, name, names))
    
    @LoggedObject.logged_meth(LoggedObject.LOGLVL_HI)
    def grab(self, revision, check_lock=True, empty=True):
        '''
        Grabs the revision or the current version if revision is None.
        If the revision contains a '/', it must be in the form:
            revision_type/revision_name
        '''
        if check_lock:
            locker = self.get_locker()
            if locker and locker != self.user:
                raise LockError('Cannot grab without lock or lockable.')
        
        # Mark locked
        open('%s/lock/%s'%(self.rvs_base, self.user), 'w').close()
        
        # Ensure working_dir exists
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
            with open('%s/revision.rvs'%self.working_dir, 'w') as w:
                w.write('%s/working'%self.user)
        
        # get the source revision
        rev_type = 'revisions'
        if revision is None:
            current_rev_link = '%s/versions/%s'%(self.rvs_base, self.CURRENT)
            rev = os.path.basename(os.readlink(current_rev_link)) #@UndefinedVariable under win
        else:
            if '/' in revision:
                # Use rsplit because workspaces revision contains a '/'!
                rev_type, revision = revision.rsplit('/', 1)
            rev = self.resolve_name(rev_type, revision)
            
        # Init the properties
        src_props = '%s/%s/%s/properties.rvs'%(self.rvs_base, rev_type, rev)
        shutil.copy2(src_props, '%s/properties.rvs'%self.working_dir)
        
        # Update the working timestamp
        with open('%s/timestamp.rvs'%self.working_dir, 'w') as w:
            w.write('%i'%time.time())
        
        if empty:
            # Initialize an empty file or folder
            working_file = '%s/%s'%(self.working_dir,self.base)
            if os.path.isdir('%s/%s'%(self.dir, self.base)):
                if os.path.exists(working_file):
                    os.rmdir(working_file)
                os.mkdir(working_file)
            else:
                open(working_file, 'w').close()
        else:
            # Initialize the file or folder from revision
            src_file =  '%s/%s/%s/%s'%(self.rvs_base, rev_type, rev, self.base)
            working_file = '%s/%s'%(self.working_dir,self.base)
            if os.path.isdir('%s/%s'%(self.dir, self.base)):
                if os.path.exists(working_file):
                    os.rmdir(working_file)
                shutil.copytree(src_file, working_file, symlinks=True)
            else:
                shutil.copyfile(src_file, working_file)
            
        # be sure the main link exists:
        src = '%s/%s' % (self.dir, self.base)
        if not os.path.exists(src):
            # the main link points to the current revision, not
            # the grabed one:
            dst = './%s=%s'%(self.CURRENT, self.base)
            os.symlink(dst, src) #@UndefinedVariable under win
            
        # Update the WORK version
        self.set_version(self.WORK, 'workspaces/'+self.user, 'working')
        
        return working_file
    
    @LoggedObject.logged_meth(LoggedObject.LOGLVL_HI)
    def push_working(self):
        '''
        Moves the item of the current working revision to 
        a revision of its own, then copies the rvs files to it.
        '''
        # get the time when we created this working 
        new_timestamp = '%i'%time.time()
        with open('%s/timestamp.rvs'%self.working_dir, 'r') as r:
            old_timestamp = int(r.read())
        
        # update it for next push:
        with open('%s/timestamp.rvs'%self.working_dir, 'w') as w:
            w.write(new_timestamp)
        
        # create the revision
        rev_path, rev = self.create_name('workspaces/%s'%self.user, old_timestamp)
        
        # move the reversion item to the new revision:
        working_file = '%s/%s'%(self.working_dir, self.base)
        is_dir = os.path.isdir(working_file)
        os.rename(working_file, '%s/%s/%s'%(rev_path, rev, self.base))
        
        # copy the properties file to the new revision
        shutil.copy2('%s/properties.rvs'%(self.working_dir), '%s/%s/properties.rvs'%(rev_path, rev))
        
        # init a new empty file in the working
        if is_dir:
            os.mkdir(working_file)
        else:
            open(working_file, 'w').close()
        
        return working_file
        
    @LoggedObject.logged_meth(LoggedObject.LOGLVL_HI)
    def publish(self, message, check_lock=True):
        '''
        Creates a new revision with (a copy of) the current user file.
        The user must have the lock.
                
        The current version is updated to point to the newly create revision.
        
        If the message contains 'VALIDATE', the VALID version will be set
        to the newly created revision.
        
        If the message contains 'version:XXXX', the version XXXX will
        be set to the newly created revision.
        
        '''
        if check_lock and not self.has_lock():
            raise LockError('Cannot publish without lock.')
        
        # create the revision
        rev_path, rev = self.create_name('revisions')
        
        # save the publication message
        with open('%s/%s/message.rvs'%(rev_path,rev), 'w') as w:
            w.write(message)
        
        # copy the properties file to the new resvision
        shutil.copy2('%s/properties.rvs'%(self.working_dir), '%s/%s/properties.rvs'%(rev_path, rev))
        
        # move the item to the revision
        src =  '%s/%s'%(self.working_dir, self.base)
        dst = '%s/%s/' % (rev_path, rev)
        shutil.move(src, dst)
        
        # Update the current version
        self.set_current(rev)
        
        # Update the VALID version if requested:
        if 'VALIDATE' in message:
            self.set_version(self.VALID, 'revisions', rev)
        
        # Update the some other versions if requested:
        for match in self._auto_version_cap.finditer(message):
            self.set_version(match.group(1), 'revisions', rev)
        
        if 0:
            # Remove the WORK version
            self.remove_version(self.WORK)
        else:
            # We used to delete the WORK version when
            # publishing. This was leading to errors
            # if someone add the WORK open and hit save.
            # We now set the WORK on the CURR so that
            # it always exists:
            self.set_version(self.WORK, 'revisions', rev)
            
        # Lose the lock:
        lock_file = '%s/lock/%s'%(self.rvs_base, self.user)
        if os.path.exists(lock_file):
            os.remove(lock_file)
        
        return rev
    
    def version_to_revision(self, version_name):
        current_rev_link = '%s/versions/%s'%(self.rvs_base, version_name)
        rev = None
        if os.path.islink(current_rev_link):
            rev = os.path.basename(os.readlink(current_rev_link)) #@UndefinedVariable under win
        return rev
    
    @LoggedObject.logged_meth(LoggedObject.LOGLVL_HI)
    def set_current(self, revision_name, update_prev=True):
        '''
        Update the current version to the given revision_name.
        The revision_name may be a revision index. 
        '''
        prev = None
        if update_prev:
            prev = self.version_to_revision(self.CURRENT)
            
        revision_name = self.resolve_name('revisions', revision_name)

        # Always update the main file:
        main_file = '%s/%s'%(self.dir, self.base)
        if os.path.islink(main_file):
            os.unlink(main_file)
        elif os.path.exists(main_file):
            raise RvsError("Cannot update main file: it is not a link. (%r)"%main_file)
        os.symlink('./CURR=%s'%self.base, main_file) #@UndefinedVariable under win
        
        self.set_version(self.CURRENT, 'revisions', revision_name)
        
        if prev is not None:
            self.set_version(self.PREV, 'revisions', prev)
        elif update_prev:
            self.set_version(self.PREV, 'revisions', revision_name)
    
    @LoggedObject.logged_meth(LoggedObject.LOGLVL_HI)
    def set_version(self, version_name, type, name):
        name = self.resolve_name(type, name)
        
        # Check the revision name
        vers_to_rev_path = '../../%s/%s/%s'%(self.base, type, name)
        if not os.path.isdir('%s/versions/%s'%(self.rvs_base, vers_to_rev_path)):
            raise RvsError("%r is not a valid %s name. (%s/versions/%s)"%(name, type, self.rvs_base, vers_to_rev_path))
        
        # Check the version name
        if not version_name:
            raise RvsError("%r is not a valid %s name (empty?!?)."%(version_name, type))
        
        # Update the version link
        ver_path = '%s/versions/%s'%(self.rvs_base, version_name)
        if os.path.islink(ver_path):
            os.unlink(ver_path)
        elif os.path.exists(ver_path):
            raise RvsError("%r is not a valid %s name (a file exists: %r)."%(version_name, type, ver_path))
        os.symlink(vers_to_rev_path, ver_path) #@UndefinedVariable under win
        
        # Create the version shortcut if needed
        ver_shortcut_name = '%s/%s=%s'%(self.dir, version_name, self.base)
        if not os.path.islink(ver_shortcut_name) and not os.path.exists(ver_shortcut_name):
            ver_shortcut_trgt = './.rvs/%s/versions/%s/%s'%(self.base, version_name, self.base)
            os.symlink(ver_shortcut_trgt, ver_shortcut_name) #@UndefinedVariable under win
    
    @LoggedObject.logged_meth(LoggedObject.LOGLVL_HI)
    def remove_version(self, name):
        ver_path = '%s/versions/%s'%(self.rvs_base, name)
        if os.path.islink(ver_path):
            os.remove(ver_path)
        
        ver_shortcut_name = '%s/%s=%s'%(self.dir, name, self.base)
        if os.path.islink(ver_shortcut_name):
            os.remove(ver_shortcut_name)

    def steal_working(self):
        '''
        Get the lock and the working content from the current locker.
        '''
        locker = self.get_locker()
        if not locker:
            raise LockError('Cannot steal if not locked.')
        if locker == self.user:
            raise LockError('Cannot steal if already have the lock.')
        
        # Steal the lock:
        open('%s/lock/%s'%(self.rvs_base, self.user), 'w').close()
        os.remove('%s/lock/%s'%(self.rvs_base, locker))
        
        # Ensure working_dir exists
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
            with open('%s/revision.rvs'%self.working_dir, 'w') as w:
                w.write('%s/working'%self.user)
        
        # get the source revision
        src_rev_path = '%s/workspaces/%s/working'%(self.rvs_base, locker)
            
        # Steal the properties
        src_props = '%s/properties.rvs'%(src_rev_path)
        os.rename(src_props, '%s/properties.rvs'%self.working_dir)

        # Steal the timestamp
        src_props = '%s/timestamp.rvs'%(src_rev_path)
        os.rename(src_props, '%s/timestamp.rvs'%self.working_dir)
                
        # Initialize the file or folder from revision
        src_file =  '%s/%s'%(src_rev_path, self.base)
        working_file = '%s/%s'%(self.working_dir,self.base)
        if os.path.isdir(src_file):
            if os.path.exists(working_file):
                os.rmdir(working_file)
        os.rename(src_file, working_file)
            
        # Update the WORK version
        self.set_version(self.WORK, 'workspaces/'+self.user, 'working')

        # Remove the source working dir
        shutil.rmtree(src_rev_path, ignore_errors=True, onerror=None)

        return working_file

    def drop_working(self, force=False):
        '''
        Drop the current lock.
        The current working files will be overwritten when the current
        locker re-grabs the item.
        
        If force is not True, the user must have the lock.
        '''
        locker = self.get_locker()
        if not locker:
            raise LockError('Cannot drop working if not locked.')
        if not force and locker != self.user:
            raise LockError('Cannot drop working without having the lock (Use "[FORCE]").')

        # Push the current working so that nothing is never lost
        self.push_working()
        
        # Remove the WORK version
        if 0:
            self.remove_version(self.WORK)
        else:
            # We used to delete the WORK version when
            # publishing. This was leading to errors
            # if someone add the WORK open and hit save.
            # We now set the WORK on the CURR so that
            # it always exists:
            self.set_version(self.WORK, 'revisions', self.version_to_revision(self.CURRENT))

        # Remove the working dir
        shutil.rmtree(self.working_dir, ignore_errors=True, onerror=None)
        
        # Release the lock:
        os.remove('%s/lock/%s'%(self.rvs_base, locker))


        
