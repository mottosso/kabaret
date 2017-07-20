

import os

from kabaret.gui import import_qt
QtCore, QtGui = import_qt()

from .. import set_style_values, set_default_style_values

def apply(widget):
    
    # --- No palette setyp for neo-native style
    
    # --- Load and apply the css
    
    this_folder = os.path.dirname(__file__)
    css_file = os.path.join(this_folder,'neonative_style.css')
    with open(css_file, 'r') as r:
        css = r.read()
    widget = widget or QtGui.QApplication.instance()
    widget.setStyleSheet(css)

    # --- Update some kabaret style values

    set_default_style_values()