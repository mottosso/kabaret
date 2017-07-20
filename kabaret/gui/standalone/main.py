
import sys

from kabaret.core.utils import resources

from kabaret.gui import import_qt
QtCore, QtGui = import_qt()

from kabaret.gui.widgets.views import (
    ConsoleView, ListenerView, ConnectionView, CommandHistoryView, ScriptView, 
    WorkersView, WorkQueueView
)
from kabaret.gui.widgets.main_window_manager import MainWindowManager


def show_ui(client, app_name, ui_setup=None, **options):        
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName(app_name)
    w = QtGui.QMainWindow(None)
    w.setWindowIcon(resources.get_icon(('gui.icons', 'kabaret_logo_32x32')))
    main_window_manager = MainWindowManager(w, client)
    main_window_manager.install_standalone()
    w.setWindowTitle('Kabaret') # temporary title, will be updated after connection    
    
    connection = main_window_manager.create_docked_view(
        u"\u20AD", 'Connection', ConnectionView, QtCore.Qt.RightDockWidgetArea, 
        options.get('Connection'), None
    )
    work_queue = main_window_manager.create_docked_view(
        u"\u20AD", 'Work Queue', WorkQueueView, QtCore.Qt.RightDockWidgetArea, 
        options.get('WorkQueue'), None
    )
    main_window_manager.tabify_docked_view(connection, work_queue)

    console = main_window_manager.create_docked_view(
        u"\u20AD", 'Console', ConsoleView, QtCore.Qt.BottomDockWidgetArea, 
        options.get('Console'), None
    )
    listener = main_window_manager.create_docked_view(
        u"\u20AD", 'Listener', ListenerView, QtCore.Qt.BottomDockWidgetArea, 
        options.get('Listener'), None
    )
    history = main_window_manager.create_docked_view(
        u"\u20AD", 'History', CommandHistoryView, QtCore.Qt.BottomDockWidgetArea, 
        options.get('History'), None
    )
    script = main_window_manager.create_docked_view(
        u"\u20AD", 'Script', ScriptView, QtCore.Qt.BottomDockWidgetArea, 
        options.get('Script'), None
    )
    workers = main_window_manager.create_docked_view(
        u"\u20AD", 'Workers', WorkersView, QtCore.Qt.BottomDockWidgetArea, 
        options.get('Workers'), None
    )
    main_window_manager.tabify_docked_view(console, listener, history, script, workers)
    
    
    if ui_setup is not None:
        ui_setup(main_window_manager)
    
    w.resize(800, 600)
    w.show()
    try:
        client.connect_from_env()
    except ValueError, err:
        print err, 'Showing Connection Dialog...'
        main_window_manager.show_connect_dialog()
    else:
        main_window_manager.update_window_title()
    app.exec_()


def startup(app_name, project_name, ui_setup, verbose, **options):
    import kabaret.core.ro.url
    import kabaret.core.ro.apphost
    import kabaret.core.ro.client
    import traceback
    client = None
    
    try:
        print
        print 'Initializing Kabaret Client'
        client = kabaret.core.ro.client.Client(project_name)
        print 'Ok.'
        
        try:
            ret_code = show_ui(client, app_name, ui_setup, **options)
        except Exception, err:
            msg = 'There was an unhandled error in GUI: %s\nClosing GUI.'%(err,)
            if verbose:
                msg += '\n'+traceback.format_exc()
            else:
                msg += '\nUse -v or --verbose to see the traceback\n'
            print msg
            ret_code = 1
            
    except Exception, err:
        msg = 'There was an error while starting a service: %s'%(err,)
        if verbose:
            msg += '\n'+traceback.format_exc()
        else:
            msg += '\nUse -v or --verbose to see the traceback\n'
        print msg
        ret_code = 2
        
    finally:
        if client is not None:
            client.shutdown()
    
    return ret_code


if __name__ == '__main__':
    import sys
    
    print 'Launching Kabaret.'
    sys.exit(startup('Kabaret', project_name=None, ui_setup=None, verbose=True))
