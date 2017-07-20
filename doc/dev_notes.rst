.. _dev-notes:


***************
Developer Setup
***************

Python
======
* Prefer python2.7
* Install distribute from `distribute_setup.py <http://pypi.python.org/pypi/distribute#distribute-setup-py>`_
* Install sphinx: easy_install.exe sphinx
* Install sphinx pypi upload: easy_install.exe sphinx-pypi-upload

IDE
====
* Install eclipse
* Use eclipse Help > Install New Software to install PyDev and Svn 
* Use the subversion repository from the google project http://code.google.com/p/kabaret/

DOC
====
* there is a bug in the upload_sphinx command used to upload the doc to pypi: it does not work if
  an empty folder (sub-folder does not count) exists under doc/_build/html.
  So the folder doc/_build/html/_modules/kabaret is an issue, you must create an empty file in it
  or the updload will not be done.
  