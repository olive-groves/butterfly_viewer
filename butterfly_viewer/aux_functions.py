#!/usr/bin/env python3

"""Functions without a specific category for Butterfly Viewer and Registrator.

Not intended as a script.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



import psutil
from PyQt6 import QtCore, QtGui


def determineSyncSenderDimension(width: int,
                                 height: int,
                                 sync_by: str="box"):
    if sync_by == "width":
        dimension = width
    elif sync_by == "height":
        dimension = height
    elif sync_by == "pixel":
        dimension = None
    else:
        if height >= width:
            dimension = height
        else:
            dimension = width

    return dimension



def determineSyncAdjustmentFactor(sync_by: str,
                                  sender_dimension: int,
                                  receiver_width: int,
                                  receiver_height: int):
    if (receiver_width == 0) or (receiver_height == 0):
        return 1

    if sync_by == "width":
        adjustment_factor = sender_dimension/receiver_width
    elif sync_by == "height":
        adjustment_factor = sender_dimension/receiver_height
    elif sync_by == "pixel":
        adjustment_factor = 1.0
    else:
        if receiver_width >= receiver_height:
            adjustment_factor = sender_dimension/receiver_width
        else:
            adjustment_factor = sender_dimension/receiver_height
    
    return adjustment_factor


def strippedName(fullFilename):
    return QtCore.QFileInfo(fullFilename).fileName()


def toBool(value):
    if value in ["true", "1", "True"]:
        return True
    elif value in ["false", "0", "False"]:
        return False
    else:
        return bool(value)


def size_format(size: int) -> str:
    """Formats a size in bytes into a human-readable string."""
    for unit, factor in (("GB", 1024**3), ("MB", 1024**2), ("KB", 1024)):
        if size >= factor:
            return f" {size / factor:.1f} {unit} "
    return f" {size:d} Bytes "


def setAvailableMemory():
    """Sets a Qt allocation limit to 98% of available memory"""
    avail_ram = psutil.virtual_memory().available
    QtGui.QImageReader.setAllocationLimit(int(avail_ram * 0.98 / 1024))
