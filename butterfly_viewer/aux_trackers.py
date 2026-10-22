#!/usr/bin/env python3

"""Trackers and signalers for SplitView.

Not intended as a script. Used in Butterfly Viewer and Registrator.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt6 import QtCore, QtGui



class EventTracker(QtCore.QObject):
    """Track and signal mouse movement and clicks."""

    mouse_position_changed = QtCore.pyqtSignal(QtCore.QPoint)
    mouse_leaved = QtCore.pyqtSignal()
    mouse_entered = QtCore.pyqtSignal()

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, source, event):
        if source is self.widget and event.type() == QtCore.QEvent.Type.MouseMove:
            self.mouse_position_changed.emit(event.position().toPoint())
        if source is self.widget and event.type() == QtCore.QEvent.Type.Leave:
            self.mouse_leaved.emit()
        if source is self.widget and event.type() == QtCore.QEvent.Type.Enter:
            self.mouse_entered.emit()
        return super().eventFilter(source, event)



class EventTrackerSplitBypassDeadzone(QtCore.QObject):
    """Limit the reported global position of the mouse to within a widget's bounds."""

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    mouse_position_changed_global = QtCore.pyqtSignal(QtCore.QPoint)

    @property
    def widget(self):
        return self._widget

    def width(self):
        return self.widget.width()

    def height(self):
        return self.widget.height()

    def eventFilter(self, source, event):
        pos = QtGui.QCursor.pos()
        if event.type() == QtCore.QEvent.Type.MouseMove:
            pos = self.limit_mouse_position_to_within_widget_bounds(pos)
            self.mouse_position_changed_global.emit(pos)

        return super().eventFilter(source, event)


    def limit_mouse_position_to_within_widget_bounds(self, pos):
        pos_global = pos
        pos_widget = self.widget.mapFromGlobal(pos_global)
        x_bounded = max(min(pos_widget.x(), self.width()), 0)
        y_bounded = max(min(pos_widget.y(), self.height()), 0)
        pos_widget.setX(x_bounded)
        pos_widget.setY(y_bounded)
        pos_global_bounded = self.widget.mapToGlobal(pos_widget)
        return pos_global_bounded



class EventTrackerSplitBypassInterface(QtCore.QObject):
    """Track mouse events while over widgets (for example, interface elements)."""

    mouse_position_changed = QtCore.pyqtSignal()
    propagate_mouse_press_event = QtCore.pyqtSignal(QtCore.QEvent)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.Type.MouseMove:
            self.mouse_position_changed.emit()
        if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            self.propagate_mouse_press_event.emit(event)
        return super().eventFilter(source, event)