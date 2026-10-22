#!/usr/bin/env python3

"""Widget layouts for Butterfly Viewer.

Not intended as a script.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt6 import QtWidgets, QtCore, QtGui



class GridLayoutFloatingShadow(QtWidgets.QGridLayout):
    """Custom QGridLayout which adds a dropshadow effect to each added widget."""

    def __init__(self):
        super().__init__()

        margin = 20
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(0)

    def addWidget(self, widget, row_i, col_i, row_span=1, col_span=1, alignment=QtCore.Qt.AlignmentFlag.AlignCenter):
        shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=16, color=QtGui.QColor(0, 0, 0, 255), xOffset=0, yOffset=0)
        widget.setGraphicsEffect(shadow)
        super().addWidget(widget, row_i, col_i, row_span, col_span, alignment)