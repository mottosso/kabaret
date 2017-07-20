


def client_init():
    print "\n-= K a b a r e t  S t u d i o - M a y a =-\n"
        
    import maya.utils
    import maya.cmds

    if 1:
        is_batch = True
        try:
            is_batch = maya.cmds.about(batch=True)
        except AttributeError:
            print "Initializing Maya Standalone"
            import maya.standalone
            maya.standalone.initialize()
    else:
        is_batch = maya.cmds.about(batch=True)
        
    if is_batch:
        # Install our GUI in the maya batch
        print "Kabaret Studio Batch installation..."
        import pprint, sys
        pprint.pprint(sys.path)
        #import kabaret.studio.clients.maya.gui as gui; gui.install_batch()
    else:
        # Install Kabaret inside Maya GUI:
        print "Deferred Kabaret Studio GUI installation..."
        maya.utils.executeDeferred('import kabaret.studio.clients.maya.gui as gui; gui.install()')


client_init()
