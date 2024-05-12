#!/usr/bin/env python3

"""Functions without a specific category for Butterfly Viewer and Registrator.

Not intended as a script.

Credits:
    PyQt MDI Image Viewer by tpgit (http://tpgit.github.io/MDIImageViewer/) for sync pan and zoom.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt5 import QtCore


def determineSyncSenderDimension(width: int,
                                 height: int,
                                 sync_by: str="box"):
    """Get the dimension of the sender image with which to synchronize zoom.
    
    Args:
        width (int): Width of sender in pixels.
        height (int): Height of sender in pixels.
        sync_by (str): Method by which to sync zoom ("box", "width", "height", "pixel").

    Returns:
        dimension (int, None): Dimension with which to synchronize zoom (None if sync by pixel).
    """

    if sync_by == "width":
        dimension = width
    elif sync_by == "height":
        dimension = height
    elif sync_by == "pixel":
        dimension = None
    else:  # Equivalent to sync_by == "box"
        # Tall image means the height dictates the size of the zoom box.
        # Wide image means the width dictates the size of the zoom box.
        if height >= width:
            dimension = height
        else:
            dimension = width

    return dimension



def determineSyncAdjustmentFactor(sync_by: str,
                                  sender_dimension: int,
                                  receiver_width: int,
                                  receiver_height: int):
    """Get the factor with which to multiply the zoom of the sender before giving it to the receiver to synchronize them.

    Returns 1 if receiver width or height are zero.
    
    Args:
        sync_by (str): Method by which to sync zoom ("box", "width", "height", "pixel").
        sender_dimension (int): Dimension of sender in pixels, as determined by determineSyncSenderDimension().
        receiver_width (int): Width of receiver in pixels.
        receiver_height (int): Height of sender in pixels.

    Returns:
        adjustment_factor (float): Factor with which to multiply the sender zoom to sync the receiver.
    """

    if (receiver_width == 0) or (receiver_height == 0):
        return 1

    if sync_by == "width":
        adjustment_factor = sender_dimension/receiver_width
    elif sync_by == "height":
        adjustment_factor = sender_dimension/receiver_height
    elif sync_by == "pixel":
        adjustment_factor = 1.0
    else: # "box"
        if receiver_width >= receiver_height:
            adjustment_factor = sender_dimension/receiver_width
        else:
            adjustment_factor = sender_dimension/receiver_height
    
    return adjustment_factor



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
