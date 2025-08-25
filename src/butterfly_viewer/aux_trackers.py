#!/usr/bin/env python3

"""Trackers and signalers for SplitView.

Not intended as a script. Used in Butterfly Viewer and Registrator.

Creates widgets to track and signal events in SplitView, primarily for mouse movement.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt5 import QtCore, QtGui



class EventTracker(QtCore.QObject):
    """Track and signal mouse movement and clicks.
    
    Args:
        widget (QWidget or child class thereof): Widget of which to track and signal mouse events.
    """

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
        if source is self.widget and event.type() == QtCore.QEvent.MouseMove:
            self.mouse_position_changed.emit(event.pos())
        if source is self.widget and event.type() == QtCore.QEvent.Leave:
            self.mouse_leaved.emit()
        if source is self.widget and event.type() == QtCore.QEvent.Enter:
            self.mouse_entered.emit()
        return super().eventFilter(source, event)



class EventTrackerSplitBypassDeadzone(QtCore.QObject):
    """Limit the reported global position of the mouse to within a widget's bounds.
    
    This class is intended to help track mouse movement in the deadzones along the SplitView's borders.
    These deadzones fix the issue of resize handles appearing in QMdiArea; however, 
    these deadzones hide the mouse from the view, so the mouse must be separately tracked 
    to ensure the split is updated.
    The mouse position is bounded to include only positions within the widget to fix issues with positions 
    reported as outside the bounds.

    Args:
        widget (QWidget or child class thereof): Widget of which to track and signal mouse events (intended to be the resize_deadzone in SplitView).
    """

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
        """Override eventFilter to limit the reported position of mouse movement.
        
        Args:
            source (PyQt source)
            event (PyQt event)

        Returns:
            The base eventFilter using source and event (passes it along to PyQt).
        """
        pos = QtGui.QCursor.pos()
        if event.type() == QtCore.QEvent.MouseMove:
            pos = self.limit_mouse_position_to_within_widget_bounds(pos) # Prevent erroneous mouse tracking outside the widget
            self.mouse_position_changed_global.emit(pos)

        return super().eventFilter(source, event)


    def limit_mouse_position_to_within_widget_bounds(self, pos):
        """Return a given global mouse position which is limited to within the widget's borders.
        
        Args:
            pos (QPoint): The position of the mouse in global coordinates.

        Returns:
            pos_global_bounded (QPoint): The position of the mouse in global coordinates limited ("floored") to within the widget borders.
        """
        pos_global = pos
        pos_widget = self.widget.mapFromGlobal(pos_global)
        x_bounded = max(min(pos_widget.x(), self.width()), 0)
        y_bounded = max(min(pos_widget.y(), self.height()), 0)
        pos_widget.setX(x_bounded)
        pos_widget.setY(y_bounded)
        pos_global_bounded = self.widget.mapToGlobal(pos_widget)
        return pos_global_bounded



class EventTrackerSplitBypassInterface(QtCore.QObject):
    """Track mouse events while over widgets (for example, interface elements).

    Needed to track the split of the sliding overlay while mouse is hovering over interface widgets.
    Prevents the split from skipping and stopping when entering and exiting interface elements.
    
    Args:
        widget (QWidget or child class thereof): The widget over which to track mouse movement.
    """

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
        """"Override event filter to emit mouse movement and button press events.
                
        See parent method for full documentation.
        
        Args:
            source (PyQt source)
            event (PyQt event)

        Returns:
            The base eventFilter using source and event (passes it along to PyQt).
        """
        if event.type() == QtCore.QEvent.MouseMove:
            self.mouse_position_changed.emit() # Emits position when mouse moves
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.propagate_mouse_press_event.emit(event)
        return super().eventFilter(source, event)