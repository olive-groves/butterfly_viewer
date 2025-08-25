#!/usr/bin/env python3

"""Functions which use image EXIF for Butterfly Viewer and Registrator.

Not intended as a script.
"""
# SPDX-License-Identifier: GPL-3.0-or-later

import piexif



def get_exif_rotation_angle(filepath):
    """Get rotation angle from EXIF of image file.
    
    Credit: tutuDajuju

    Args:
        filepath (str): Absolute path of image file.

    Returns:
        orientation (int or None): Image orientation as integer angle if exists; None if does not exist.
    """
    try:
        exif_dict = piexif.load(filepath)
    except:
        return None
    else:
        try:
            exif_dict["0th"]
        except:
            return None
        else:
            if piexif.ImageIFD.Orientation in exif_dict["0th"]:
                orientation = exif_dict["0th"][piexif.ImageIFD.Orientation]
                if orientation == 3:
                    return 180
                elif orientation == 6:
                    return 90
                elif orientation == 8:
                    return 270
                else:
                    return None
            else:
                return None