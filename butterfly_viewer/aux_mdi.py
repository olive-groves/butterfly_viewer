#!/usr/bin/env python3

"""QMdiArea with drag-and-drop functions, vertical/horizontal window tiling, and keyboard shortcuts.

Not intended as a script.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt6 import QtWidgets, QtCore, QtGui



class QMdiAreaWithCustomSignals(QtWidgets.QMdiArea):
    """Extend QMdiArea with drag-and-drop functions, vertical/horizontal window tiling, and keyboard shortcuts."""

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

        self.escape_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.shortcut_escape_was_activated)

        self.f_shortcut = QtGui.QShortcut(QtGui.QKeySequence("f"), self)
        self.f_shortcut.activated.connect(self.shortcut_f_was_activated)

        self.h_shortcut = QtGui.QShortcut(QtGui.QKeySequence("h"), self)
        self.h_shortcut.activated.connect(self.shortcut_h_was_activated)

        self.ctrl_c_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+c"), self)
        self.ctrl_c_shortcut.activated.connect(self.shortcut_ctrl_c_was_activated)

        self.tile_subwindows_horizontally()

    def tile_subwindows_vertically(self, button_input=None):
        windows = self.subWindowList()
        if not windows:
            self.last_tile_method = "vertically"
            return
        position = QtCore.QPoint()
        tile_height = int(self.height() / len(windows))
        for window in windows:
            rect = QtCore.QRect(0, 0, self.width(), tile_height)
            window.setGeometry(rect)
            window.move(position)
            position.setY(position.y() + window.height())
        self.last_tile_method = "vertically"

    def tile_subwindows_horizontally(self, button_input=None):
        windows = self.subWindowList()
        if not windows:
            self.last_tile_method = "horizontally"
            return
        position = QtCore.QPoint()
        tile_width = int(self.width() / len(windows))
        for window in windows:
            rect = QtCore.QRect(0, 0, tile_width, self.height())
            window.setGeometry(rect)
            window.move(position)
            position.setX(position.x() + window.width())
        self.last_tile_method = "horizontally"
    
    def tileSubWindows(self, button_input=None):
        super().tileSubWindows()
        self.last_tile_method = "grid"

    def tile_what_was_done_last_time(self):
        if self.last_tile_method == "horizontally":
            self.tile_subwindows_horizontally()
        elif self.last_tile_method == "vertically":
            self.tile_subwindows_vertically()
        else:
            self.tileSubWindows()

    def dragEnterEvent(self, event):
        self.file_path_dragged.emit(True)
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dragLeaveEvent(self, event):
        self.file_path_dragged.emit(False)
        event.accept()

    def dropEvent(self, event):
        event.setDropAction(QtCore.Qt.DropAction.CopyAction)

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
        if not window:
            self.are_there_any_subwindows_open = False
            self.last_remaining_subwindow_was_closed.emit()
        elif not self.are_there_any_subwindows_open:
            self.are_there_any_subwindows_open = True
            self.first_subwindow_was_opened.emit()
            self.most_recently_activated_subwindow = window
        return

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.last_tile_method == "horizontally":
            self.tile_subwindows_horizontally()
        elif self.last_tile_method == "vertically":
            self.tile_subwindows_vertically()
        else:
            return