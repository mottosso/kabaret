.. _install:

************
Installation
************

.. _prerequisites:

Prerequisites
=============
You will need setuptools (or compatible) to install kabaret packages.
If you don't already use it, you should head to  
the `setuptools on pypi <http://pypi.python.org/pypi/setuptools>`_ and 
follow the installation instructions.


You also probably need a valid python wrapper for Qt4 (>4.7): 
`PyQt <http://www.riverbankcomputing.co.uk/software/pyqt/download>`_
or `PySide <http://qt-project.org/downloads>`_.


Any other dependency will be auto-fulfilled when installing kabaret packages.

Easy Install
============

On linux::

	easy_install <kabaret_package>

On windows::

	easy_install.exe <kabaret_package>

.. note:: replace *<kabaret_package>* by the name of a package listed in the *Packages* section.


Update
======

Add the -U or --upgrade option::

	easy_install -U <kabaret_package>


Uninstall
=========

There is no uninstall script but getting ride of all kabaret packages is quite easy:

Go to your python site package (for example *C:/Python26/Lib/site-packages*),
remove all .egg files and folders with a name related to kabaret, and edit the easy-install.pth 
file to remove the lines referencing kabaret packages.


.. _packages:

Packages
========
Installing the "kabaret" package will not provide much as it is almost only a 
documentation holder.
Instead you will want to install one of the framework sub packages:

* **kabaret.core**

  The framework core library. 
  
  Let you build your own studio solutions.

* **kabaret.gui**

  The framework GUI library.
  
  Let you build standalone and DCC embedded application for 
  your own studio solution.
  Requires PyQt or PySide (see Prerequisites_).

* **kabaret.studio**

  A complete studio solution implemented for the Supamonks Studio.
  
  You can configure it to suit your need and run a fully featured studio in a matter of hours,
  or simply browse its code to learn how you could create your own studio solution.

* **kabaret.flow**

  DataFlow+WorkFlow modeling and enactment.
  
  It does not rely on other kabaret package and can be used directly.

* **kabaret.naming**

  File and Folder naming convention modeling and exploitation.
  
  It does not rely on other kabaret package and can be used directly.

Those packages may require other python packages that will be 
installed along.

If you look for a overview of the whole kabaret framework you should 
install *kabaret.studio* as it requires (and will install) most of the sub-packages.