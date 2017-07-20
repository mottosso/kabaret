

import os

from kabaret.gui import import_qt
QtCore, QtGui = import_qt()

from .. import set_style_values, set_default_style_values

def apply(widget=None):
    
    # --- Change palette only for app wide apply:

    if widget is None:
        # setup the palette
        palette = QtGui.QApplication.palette()
        
        # A general background color.
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(60, 60, 60))
        
        # A general foreground color.
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(185, 185, 185))
        
        # Used mostly as the background color for text entry widgets, but can also be used for other painting -
        # such as the background of combobox drop down lists and toolbar handles. It is usually white or another light color.
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(42, 42, 42))
        
        # Used as the alternate background color in views with alternating row colors (see QAbstractItemView.setAlternatingRowColors()).
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(64, 64, 64))
        
        # Used as the background color for QToolTip and QWhatsThis. Tool tips use the Inactive color group of QPalette, because tool tips are not active windows.
        palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(117, 77, 77))
        
        # Used as the foreground color for QToolTip and QWhatsThis. Tool tips use the Inactive color group of QPalette, because tool tips are not active windows.
        palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(255, 0, 0))
        
        # The foreground color used with Base. This is usually the same as the WindowText, in which case it must provide good contrast with Window and Base.
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(128, 128, 128))
        
        # The general button background color. This background can be different from Window as some styles require a different background color for buttons.
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(64, 64, 64))
        
        # A foreground color used with the Button color.
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(185, 185, 185))
        
        # A text color that is very different from WindowText, and contrasts well with e.g. Dark. Typically used for text that needs to be drawn where Text
        # or WindowText would give poor contrast, such as on pressed push buttons. Note that text colors can be used for things other than just words; text
        # colors are usually used for text, but it's quite common to use the text color roles for lines, icons, etc.
        palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 255, 255))
        
        # Lighter than Button color.
        palette.setColor(QtGui.QPalette.Light, QtGui.QColor(200, 200, 200))
        
        # Between Button and Light.
        palette.setColor(QtGui.QPalette.Midlight, QtGui.QColor(100, 100, 100))
    
        # Between Button and Dark.
        palette.setColor(QtGui.QPalette.Mid, QtGui.QColor(40, 40, 40))
    
        # Darker than Button.
        palette.setColor(QtGui.QPalette.Dark, QtGui.QColor(25, 25, 25))
    
        # A very dark color. By default, the shadow color is Qt.black.
        palette.setColor(QtGui.QPalette.Shadow, QtGui.QColor(10, 10, 0))
    
        # A color to indicate a selected item or the current item. By default, the highlight color is Qt.darkBlue.
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(80, 0, 0))
    
        # A text color that contrasts with Highlight. By default, the highlighted text color is Qt.white.
        palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(188, 128, 128))

        QtGui.QApplication.setPalette(palette)
    
    # --- Load and apply the css
    
    this_folder = os.path.dirname(__file__)
    css_file = os.path.join(this_folder,'dark_style.css')
    with open(css_file, 'r') as r:
        css = r.read()
    widget = widget or QtGui.QApplication.instance()
    widget.setStyleSheet(css)

    # --- Set some kabaret style values
    
    set_default_style_values()
    
    
    
    