#!/usr/bin/env python3

"""QLabel widgets for Butterfly Viewer and Registrator.

Not intended as a script.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt6 import QtCore, QtGui, QtWidgets



class FilenameLabel(QtWidgets.QLabel):
    """Styled label for overlaying filenames on viewers and image previews."""
    
    def __init__(self, text=None, remove_path=True, visibility_based_on_text=False, belongs_to_split=False):
        super().__init__()
        
        self.remove_path = remove_path
        self.visibility_based_on_text = visibility_based_on_text
        
        if text is not None:
            self.setText(text)

        self.make_visible_based_on_text()
            
        self.setFrameStyle(QtWidgets.QFrame.Shape.Panel)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setBackgroundRole(QtGui.QPalette.ColorRole.ToolTipBase)
        if belongs_to_split:
            self.setStyleSheet("QLabel {color: white; background-color: rgba(0, 0, 0, 191); border: 0px solid black; margin: 0.3em; font-size: 7.5pt; border-radius: 0px; }")
        else:
            self.setStyleSheet("QLabel {color: white; background-color: rgba(0, 0, 0, 191); border: 0px solid black; margin: 0.2em; font-size: 7.5pt; border-radius: 0px; }")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred)
        
    def setText(self, text):
        if text is not None:
            if self.remove_path:
                text = text.split("/")[-1]
        
        super().setText(text)

        self.make_visible_based_on_text()

    def make_visible_based_on_text(self, text=None):
        text = self.text()
        if text == "":
            text = None
        if self.visibility_based_on_text:
            if text is not None:
                self.setVisible(True)
            else:
                self.setVisible(False)

    def set_visible_based_on_text(self, value):
        text = self.text()
        if text == "":
            text = None
        if self.visibility_based_on_text:
            if text is None:
                value = False
        self.setVisible(value)