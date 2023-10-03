#!/usr/bin/env python3

"""Widget layouts for Butterfly Viewer.

Not intended as a script.

GridLayoutFloatingShadow extends QGridLayout by adding a dropshadow effect for added widgets.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt5 import QtWidgets, QtCore, QtGui



class GridLayoutFloatingShadow(QtWidgets.QGridLayout):
    """Custom QGridLayout which adds a dropshadow effect to each added widget.

    Instantiate without input. Add widgets only with addWidget(). Does not support addLayout().
    
    Dropshadow makes interface widgets more distinguishable as overlayed elements.
    """

    def __init__(self):
        super().__init__()

        margin = 20
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(0)

    def addWidget(self, widget, row_i, col_i, row_span=1, col_span=1, alignment=QtCore.Qt.AlignCenter):
        """Override addWidget() to add widget to layout with dropshadow graphics effect.
        
        Args:
            widget (QWidget or child class thereof): The widget to add to the layout.
            row_i (int): The row location of the widget.
            col_i (int): The column location of the widget.
            row_span (int): The number of rows the widget spans.
            col_span (int): The number of columns the widget spans.
            alignment (AlignmentFlag): The alignment of the widget in the designated layout location.
        """
        shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=16, color=QtGui.QColor(0, 0, 0, 255), xOffset=0, yOffset=0)
        widget.setGraphicsEffect(shadow)
        super().addWidget(widget, row_i, col_i, row_span, col_span, alignment)