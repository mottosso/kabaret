'''

    Reversion - A revision and version control filesystem.

    Reversion uses the fuse library to define a user space filesytem that
    automatically stores each revision of files (and optionally folders).
    It runs under Linux and is intended for windows and Linux users.
    
    A workspace is made available by a reversion.rvsfs.mount() call.
    It shadows a repository folder where actual files are stored.
    You use the 'umount' command to disable a workspace. 
    
    When a user accesses the workspace, its login is used to identify him.
    Every file is backup'ed before being truncated in a working folder 
    specific to the truncating user (Appending content to a file does
    not create a backup).
    
    Once a user created a working file, it obtains the lock for
    this file. Only the user with the lock can further modify the file.
    Other user have a read access to the content of the file before the
    lock got acquired.
    That is: the user with the lock is the only one able to see the new
    content of the locked file.
    
    In order to make the content modification available to other users, the 
    locker must 'publish' the file. This will create a new revision for the
    file and the user will lose the lock.
    The created revision is known as the 'current version' and is available
    for every users as the content of the file.
    
    Other content may be accessed. Every revision can be set as a version.
    Setting a revision as a version creates a new file beside the versioned
    one, will the naming convention:
        version_name=file_name
    
    A revision may have several version.
    A version gives access to a single revision.
    
    There are a bunch of automatic version that the user does not control:
        the current revision is the 'CURR' version.
        the previous revision is the 'PREV' version.
        the 'WORK' version point to the publishable revision or the CURR if
        noone has the lock.
    
    Reversion stores every working files and revision in readable state, under 
    a sibling folder of the managed file named '.rvs'.
    This folder is known as the 'reversion base', or 'rvs_base' folder.
    
    To publish a working file or set/remove a version on a revision, Reversion uses
    command files.
    This unusual proceeding let users control Reversion without any other need
    than write access to the filesystem.
    The command files are in the _COMMAND_ folder of the reversion base.
    There are three commands files available here:
        Publish: publish the user's working file using the command file content
                as publication message. If the message contains the 'VALIDATED'
                word, the 'VALID' version will point to the newly created revision.
                If the message contains some 'version:<version_name>' tokens, the
                corresponding version will point to the newly created revision.
        SetVersion: set a version on a revision. The command file content must be 
                in the form 'version_name:revision_name'.
                The version is created or moved from another revision if needed.
        RemoveVersion: removes a version from a revision. The content of the 
                command file must be in the form: 'revision_name'
    
    To trigger a command, one just need to save the file.
    The command will act depending on the content of the command file.
    The command will modify the content of the file.
    User can be sure the command succeed if the word 'failed' does not appear in
    the content of the file after saving it, closing it and opening it back.
    Nevertheless, the feedback of a command is not to be trusted since another
    command may have been triggered in-between.
    
    Reversion API is accessible with the reversion.client.Client() class.
    See the class documentation for details.
    
'''

from . import client
