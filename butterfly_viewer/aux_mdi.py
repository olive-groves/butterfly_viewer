#!/usr/bin/env python3

"""QMdiArea with drag-and-drop functions, vertical/horizontal window tiling, and keyboard shortcuts.

Not intended as a script.

Creates the multi document interface (MDI) widget for the Butterfly Viewer.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt5 import QtWidgets, QtCore, QtGui



class QMdiAreaWithCustomSignals(QtWidgets.QMdiArea):
    """Extend QMdiArea with drag-and-drop functions, vertical/horizontal window tiling, and keyboard shortcuts.

    Instantiate without input.
    
    Features:
        Signals for drag-and-drop, subwindow events, shortcut keys.
        Methods for arranging the subwindows vertically and horizontally, and to track the history of the arrangement.
    """

    file_path_dragged_and_dropped = QtCore.pyqtSignal(str)
    file_path_dragged = QtCore.pyqtSignal(bool)
    shortcut_escape_was_activated = QtCore.pyqtSignal()
    shortcut_f_was_activated = QtCore.pyqtSignal()
    shortcut_h_was_activated = QtCore.pyqtSignal()
    shortcut_ctrl_c_was_activated = QtCore.pyqtSignal()

    first_subwindow_was_opened = QtCore.pyqtSignal()
    last_remaining_subwindow_was_closed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.setAcceptDrops(True)
        self.subWindowActivated.connect(self.subwindow_was_activated)
        self.last_tile_method = None
        self.are_there_any_subwindows_open = False
        self.most_recently_activated_subwindow = None

        self.escape_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.shortcut_escape_was_activated)

        self.f_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("f"), self)
        self.f_shortcut.activated.connect(self.shortcut_f_was_activated)

        self.h_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("h"), self)
        self.h_shortcut.activated.connect(self.shortcut_h_was_activated)

        self.ctrl_c_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+c"), self)
        self.ctrl_c_shortcut.activated.connect(self.shortcut_ctrl_c_was_activated)

    def tile_subwindows_vertically(self, button_input=None):
        """Arrange subwindows vertically as a single column.

        Arranges subwindows top to bottom in order of when they were added (oldest to newest).
        
        Args:
            button_input: Always set as None (kept for legacy purposes).
        """
        windows = self.subWindowList()
        position = QtCore.QPoint()
        for window in windows:
            rect = QtCore.QRect(0, 0, self.width(), self.height()/len(windows))
            window.setGeometry(rect)
            window.move(position)
            position.setY(position.y() + window.height())
        self.last_tile_method = "vertically"

    def tile_subwindows_horizontally(self, button_input=None):
        """Arrange subwindows horizontally as a single row.

        Arranges subwindows left to right in order of when they were added (oldest to newest).
        
        Args:
            button_input: Always set as None (kept for legacy purposes).
        """
        windows = self.subWindowList()
        position = QtCore.QPoint()
        for window in windows:
            rect = QtCore.QRect(0, 0, self.width()/len(windows), self.height())
            window.setGeometry(rect)
            window.move(position)
            position.setX(position.x() + window.width())
        self.last_tile_method = "horizontally"
    
    def tileSubWindows(self, button_input=None):
        """Arrange subwindows as tiles (override).
        
        Args:
            button_input: Always set as None (kept for legacy purposes).
        """
        super().tileSubWindows()
        self.last_tile_method = "grid"

    def tile_what_was_done_last_time(self):
        """Arrange subwindows based on previous arrangement.
        
        Needed to arrange windows in the last arranged method during events like resizing.
        """
        if self.last_tile_method == "horizontally":
            self.tile_subwindows_horizontally()
        elif self.last_tile_method == "vertically":
            self.tile_subwindows_vertically()
        else:
            self.tileSubWindows()

    def dragEnterEvent(self, event):
        """event: Signal that one or more files have been dragged into the area."""
        self.file_path_dragged.emit(True)
        event.accept()

    def dragMoveEvent(self, event):
        """event: Signal that one or more files are being dragged in the area."""
        event.accept()

    def dragLeaveEvent(self, event):
        """event: Signal that one or more files have been dragged out of the area."""
        self.file_path_dragged.emit(False)
        event.accept()

    def dropEvent(self, event):
        """event: Signal that one or more files have been dropped into the area."""
        event.setDropAction(QtCore.Qt.CopyAction)

        self.file_path_dragged.emit(False)

        urls = event.mimeData().urls()

        if urls:
            for url in urls:
                file_path = url.toLocalFile()
                self.file_path_dragged_and_dropped.emit(file_path)
            event.accept()
        else:
            event.ignore()

    def subwindow_was_activated(self, window): 
        """Signal if first subwindow has been activated or if last remaining subwindow has been closed.

        Triggered when subwindow activated signal of area is emitted.
        Fixes issues with improper subwindow activation behavior.

        Args:
            window (QMdiSubWindow)
        """
        
        if not window: #  When the last remaining subwindow is closed, subWindowActivated throws Null window
            self.are_there_any_subwindows_open = False
            self.last_remaining_subwindow_was_closed.emit()
        elif not self.are_there_any_subwindows_open: # If there is indeed a window but the boolean still shows there are none open, then change the boolean
            self.are_there_any_subwindows_open = True
            self.first_subwindow_was_opened.emit()
            self.most_recently_activated_subwindow = window
        return

    def resizeEvent(self, event):
        """Override resizeEvent() to maintain horizontal and vertical arrangement of subwindows during resizing.
        
        Fixes shuffling of subwindows when area is resized in vertical and horizontal arrangements.
        """
        super().resizeEvent(event)

        if self.last_tile_method == "horizontally":
            self.tile_subwindows_horizontally()
        elif self.last_tile_method == "vertically":
            self.tile_subwindows_vertically()
        else:
            return