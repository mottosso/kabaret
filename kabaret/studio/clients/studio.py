


import kabaret.gui.standalone.main

from kabaret.studio.clients import flow_gui, naming_gui, system_cmds_gui, versions_gui


def ui_setup(main_window_manager):
    naming_gui.install(main_window_manager)
    system_cmds_gui.install(main_window_manager)
    versions_gui.install(main_window_manager)
    flow_gui.install(main_window_manager)

def main(project_name=None, **options):
    kwargs = {
        'verbose':True,
        'Connection':False,
        'History':False,
        'Listener':False,
        'Script':False,
    }
    kwargs.update(options)
    kabaret.gui.standalone.main.startup(
        'Kabaret Studio', project_name, ui_setup, **kwargs
    )

if __name__ == '__main__':
    main()
