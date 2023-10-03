#!/usr/bin/env python3

"""QGraphicsView with synchronized pan and zoom functionality.

Not intended as a script.

Creates the base (main) view of the SplitView for the Butterfly Viewer and Registrator.

Credits:
    PyQt MDI Image Viewer by tpgit (http://tpgit.github.io/MDIImageViewer/) for sync pan and zoom.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt5 import QtCore, QtGui, QtWidgets



class SynchableGraphicsView(QtWidgets.QGraphicsView):
    """Extend QGraphicsView for synchronous panning and zooming between multiple instances.

    Extends QGraphicsView:
        Pan and zoom signals.
        Scrolling operations and mouse wheel zooming.
        Mouse tracking.
        View shortcuts (for example, centering the view).

    Args:
        scene (QGraphicsScene)
        parent (QWidget or child class thereof)
    """


    def __init__(self, scene=None, parent=None):
        if scene:
            super(SynchableGraphicsView, self).__init__(scene, parent)
        else:
            super(SynchableGraphicsView, self).__init__(parent)
        
        self.scroll_to_zoom_always_on = True
        
        self._handDrag = False

        self.clearTransformChanges()
        self.connectSbarSignals(self.scrollChanged)
        
        self.setMouseTracking(True) # Allows split to follow the mouse cursor without needing to click the mouse (expected split behavior) 
        self.right_clicked_is_pressed = False
        
        self.installEventFilter(self)
    

    # Signals

    transformChanged = QtCore.pyqtSignal()
    """Transformed Changed **Signal**.

    Emitted whenever the |QGraphicsView| Transform matrix has been
    changed."""
    
    scrollChanged = QtCore.pyqtSignal()
    """Scroll Changed **Signal**.

    Emitted whenever the scrollbar position or range has changed."""
    
    wheelNotches = QtCore.pyqtSignal(float)
    """Wheel Notches **Signal** (*float*).

    Emitted whenever the mouse wheel has been rolled. A wheelnotch is
    equal to wheel delta / 240"""
    
    def connectSbarSignals(self, slot):
        """Connect to scrollbar changed signals to synchronize panning.

        :param slot: slot to connect scrollbar signals to."""
        sbar = self.horizontalScrollBar()
        sbar.valueChanged.connect(slot, type=QtCore.Qt.UniqueConnection)
        #sbar.sliderMoved.connect(slot, type=QtCore.Qt.UniqueConnection)
        sbar.rangeChanged.connect(slot, type=QtCore.Qt.UniqueConnection)

        sbar = self.verticalScrollBar()
        sbar.valueChanged.connect(slot, type=QtCore.Qt.UniqueConnection)
        #sbar.sliderMoved.connect(slot, type=QtCore.Qt.UniqueConnection)
        sbar.rangeChanged.connect(slot, type=QtCore.Qt.UniqueConnection)

        #self.scrollChanged.connect(slot, type=QtCore.Qt.UniqueConnection)

    def disconnectSbarSignals(self):
        """Disconnect from scrollbar changed signals."""
        sbar = self.horizontalScrollBar()
        sbar.valueChanged.disconnect()
        #sbar.sliderMoved.disconnect()
        sbar.rangeChanged.disconnect()

        sbar = self.verticalScrollBar()
        sbar.valueChanged.disconnect()
        #sbar.sliderMoved.disconnect()
        sbar.rangeChanged.disconnect()
    
    right_mouse_button_was_clicked = QtCore.pyqtSignal(QtCore.QPoint)

    # Properties

    @property
    def handDragging(self):
        """Hand dragging state (*bool*)"""
        return self._handDrag

    @property
    def scrollState(self):
        """Tuple of percentage of scene extents
        *(sceneWidthPercent, sceneHeightPercent)*"""
        centerPoint = self.mapToScene(self.viewport().width()/2,
                                      self.viewport().height()/2)
        sceneRect = self.sceneRect()
        centerWidth = centerPoint.x() - sceneRect.left()
        centerHeight = centerPoint.y() - sceneRect.top()
        sceneWidth =  sceneRect.width()
        sceneHeight = sceneRect.height()

        sceneWidthPercent = centerWidth / sceneWidth if sceneWidth != 0 else 0
        sceneHeightPercent = centerHeight / sceneHeight if sceneHeight != 0 else 0
        return (sceneWidthPercent, sceneHeightPercent)

    @scrollState.setter
    def scrollState(self, state):
        sceneWidthPercent, sceneHeightPercent = state
        x = (sceneWidthPercent * self.sceneRect().width() +
             self.sceneRect().left())
        y = (sceneHeightPercent * self.sceneRect().height() +
             self.sceneRect().top())
        self.centerOn(x, y)

    @property
    def zoomFactor(self):
        """Zoom scale factor (*float*)."""
        return self.transform().m11()

    @zoomFactor.setter
    def zoomFactor(self, newZoomFactor):
        newZoomFactor = newZoomFactor / self.zoomFactor
        self.scale(newZoomFactor, newZoomFactor)

    
    # Events

    def mouseMoveEvent(self, event):
        event.ignore()
        return super().mouseMoveEvent(event)

    def wheelEvent(self, wheelEvent):
        """Overrides the wheelEvent to handle zooming.

        :param QWheelEvent wheelEvent: instance of |QWheelEvent|"""
        assert isinstance(wheelEvent, QtGui.QWheelEvent)
        if (wheelEvent.modifiers() & QtCore.Qt.ControlModifier) or self.scroll_to_zoom_always_on:
            self.wheelNotches.emit(wheelEvent.angleDelta().y() / 240.0)
            wheelEvent.accept()
        else:
            super(SynchableGraphicsView, self).wheelEvent(wheelEvent)

    def keyReleaseEvent(self, keyEvent):
        """Overrides to make sure key release passed on to other classes.

        :param QKeyEvent keyEvent: instance of |QKeyEvent|"""
        assert isinstance(keyEvent, QtGui.QKeyEvent)
        #print("graphicsView keyRelease count=%d, autoRepeat=%s" %
              #(keyEvent.count(), keyEvent.isAutoRepeat()))
        keyEvent.ignore()
        #super(SynchableGraphicsView, self).keyReleaseEvent(keyEvent)

    def mousePressEvent(self, event):
        """Overrides to allow left-click for panning and limit repeat right-clicks.
        
        Enables hand dragging (panning) of the view by clicking left mouse button.
        
        Parameters:
        
        - event: [PtQt event]."""
        assert isinstance(event, QtGui.QMouseEvent)
        if event.button() == QtCore.Qt.LeftButton:  # Pan the image by clicking and dragging left mouse button
            self.enableHandDrag(True)
            event.accept()
        if (not self.right_clicked_is_pressed) and (event.button() == QtCore.Qt.RightButton): # Indicate right button is pressed to prevent rapid repeating release signals 
            self.right_clicked_is_pressed = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Overrides to disable panning left-click for panning and limit repeat right-clicks.
        
        Undoes the actions from mousePressEvent (release of mouse buttons).
        
        Parameters:
        
        - event: [PtQt event]."""
        assert isinstance(event, QtGui.QMouseEvent)
        if event.button() == QtCore.Qt.LeftButton:
            self.enableHandDrag(False)
            event.accept()
        if (self.right_clicked_is_pressed) and (event.button() == QtCore.Qt.RightButton):
            self.right_clicked_is_pressed = False
            self.right_mouse_button_was_clicked.emit(event.pos())
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        """Ignore drag event, thus passing it along to the parent widget.

        Allows for the drag-and-drop function in digitaltwin_imageviewer.py by 
        passing drag events to the underlying MDI area.
        
        Parameters:
        
        - event : [PyQt event]"""
        event.ignore() # Give the drag event to the parent widget (e.g., to allow drag-and-drop in multi-instance viewers)
    

    # Zoom and pan (scrolling) methods

    def checkTransformChanged(self):
        """Return True if view transform has changed.

        :rtype: bool"""
        delta = 0.001
        result = False

        def different(t, u):
            if u == 0.0:
                d = abs(t - u)
            else:
                d = abs((t - u) / u)
            return d > delta

        t = self.transform()
        u = self._transform

        if False:
            print("t = ")
            self.dumpTransform(t, "    ")
            print("u = ")
            self.dumpTransform(u, "    ")
            print("")

        if (different(t.m11(), u.m11()) or
            different(t.m22(), u.m22()) or
            different(t.m12(), u.m12()) or
            different(t.m21(), u.m21()) or
            different(t.m31(), u.m31()) or
            different(t.m32(), u.m32())):
            self._transform = t
            self.transformChanged.emit()
            result = True
        return result

    def clearTransformChanges(self):
        """Reset view transform changed info."""
        self._transform = self.transform()

    def scrollToTop(self):
        """Scroll view to top."""
        sbar = self.verticalScrollBar()
        sbar.setValue(sbar.minimum())

    def scrollToBottom(self):
        """Scroll view to bottom."""
        sbar = self.verticalScrollBar()
        sbar.setValue(sbar.maximum())

    def scrollToBegin(self):
        """Scroll view to left edge."""
        sbar = self.horizontalScrollBar()
        sbar.setValue(sbar.minimum())

    def scrollToEnd(self):
        """Scroll view to right edge."""
        sbar = self.horizontalScrollBar()
        sbar.setValue(sbar.maximum())

    def centerView(self):
        """Center view."""
        sbar = self.verticalScrollBar()
        sbar.setValue((sbar.maximum() + sbar.minimum())/2)
        sbar = self.horizontalScrollBar()
        sbar.setValue((sbar.maximum() + sbar.minimum())/2)

    def enableScrollBars(self, enable):
        """Set visibility of the view's scrollbars.

        :param bool enable: True to enable the scrollbars """
        if enable:
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def enableHandDrag(self, enable):
        """Set whether dragging the view with the hand cursor is allowed.

        :param bool enable: True to enable hand dragging """
        if enable:
            if not self._handDrag:
                self._handDrag = True
                self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        else:
            if self._handDrag:
                self._handDrag = False
                self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
    

    # Printing methods

    def dumpTransform(self, t, padding=""):
        """Dump the transform t to stdout.

        :param t: the transform to dump
        :param str padding: each line is preceded by padding"""
        print("%s%5.3f %5.3f %5.3f" % (padding, t.m11(), t.m12(), t.m13()))
        print("%s%5.3f %5.3f %5.3f" % (padding, t.m21(), t.m22(), t.m23()))
        print("%s%5.3f %5.3f %5.3f" % (padding, t.m31(), t.m32(), t.m33()))