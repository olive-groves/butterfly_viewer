#!/usr/bin/env python3

"""QLabel widgets for Butterfly Viewer and Registrator.

Not intended as a script.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt5 import QtCore, QtGui, QtWidgets



class FilenameLabel(QtWidgets.QLabel):
    """Styled label for overlaying filenames on viewers and image previews.
    
    Args:
        text (str): The text to show (the filename).
        remove_path (bool): True to remove path from the filename (filepath).
        visibilty_based_on_text (bool): True to hide label when text is None; False to always show.
        belongs_to_split (bool): True for improved style for sliding overlays in SplitView; False as default.
    """
    
    def __init__(self, text=None, remove_path=True, visibility_based_on_text=False, belongs_to_split=False):
        super().__init__()
        
        self.remove_path = remove_path
        self.visibility_based_on_text = visibility_based_on_text
        
        if text is not None:
            self.setText(text)

        self.make_visible_based_on_text()
            
        self.setFrameStyle(QtWidgets.QFrame.Panel)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setBackgroundRole(QtGui.QPalette.ToolTipBase)
        if belongs_to_split:
            self.setStyleSheet("QLabel {color: white; background-color: rgba(0, 0, 0, 191); border: 0px solid black; margin: 0.3em; font-size: 7.5pt; border-radius: 0px; }")
        else:
            self.setStyleSheet("QLabel {color: white; background-color: rgba(0, 0, 0, 191); border: 0px solid black; margin: 0.2em; font-size: 7.5pt; border-radius: 0px; }")
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        
    def setText(self, text):
        """str: Override setText to remove path in filename and set visibilty as specified."""
        if text is not None:
            if self.remove_path:
                text = text.split("/")[-1]
        
        super().setText(text)

        self.make_visible_based_on_text()

    def make_visible_based_on_text(self, text=None):
        """Make label visible if label has text; hide label if no text (only if set to do so).
        
        Only call with no arguments (for example, make_visible_based_on_text()).
        """
        text = self.text()
        if text is "":
            text = None
        if self.visibility_based_on_text:
            if text is not None:
                self.setVisible(True)
            else:
                self.setVisible(False)

    def set_visible_based_on_text(self, value):
        """bool: Set visibilty of label but take into account the setting for visibilty based on text."""
        text = self.text()
        if text is "":
            text = None
        if self.visibility_based_on_text:
            if text is None:
                value = False
        self.setVisible(value)