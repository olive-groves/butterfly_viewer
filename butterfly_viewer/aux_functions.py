#!/usr/bin/env python3

"""Functions without a specific category for Butterfly Viewer and Registrator.

Not intended as a script.

Credits:
    PyQt MDI Image Viewer by tpgit (http://tpgit.github.io/MDIImageViewer/) for sync pan and zoom.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt5 import QtCore



def strippedName(fullFilename):
    """Get filename from a filepath.

    Legacy function from PyQt MDI Image Viewer by tpgit.

    Args:
        fullFilename (str): The filepath (the "full" filename).
    
    Returns:
        value (str): The filename as stripped from the filepath.
    """
    return QtCore.QFileInfo(fullFilename).fileName()



def toBool(value):
    """Convert string value to bool.

    Legacy function from PyQt MDI Image Viewer by tpgit.

    Args:
        value (any)
    
    Returns:
        value (bool)
    """
    if value in ["true", "1", "True"]:
        return True
    elif value in ["false", "0", "False"]:
        return False
    else:
        return bool(value)