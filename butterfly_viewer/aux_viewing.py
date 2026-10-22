#!/usr/bin/env python3

"""QGraphicsView with synchronized pan and zoom functionality.

Not intended as a script.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt6 import QtCore, QtGui, QtWidgets



class SynchableGraphicsView(QtWidgets.QGraphicsView):
    """Extend QGraphicsView for synchronous panning and zooming between multiple instances."""

    def __init__(self, scene=None, parent=None):
        if scene:
            super(SynchableGraphicsView, self).__init__(scene, parent)
        else:
            super(SynchableGraphicsView, self).__init__(parent)
        
        self.scroll_to_zoom_always_on = True
        self._handDrag = False

        self.clearTransformChanges()
        self.connectSbarSignals(self.scrollChanged)
        
        self.setMouseTracking(True)
        self.right_clicked_is_pressed = False
        
        self.installEventFilter(self)
    

    transformChanged = QtCore.pyqtSignal()
    scrollChanged = QtCore.pyqtSignal()
    wheelNotches = QtCore.pyqtSignal(float)
    right_mouse_button_was_clicked = QtCore.pyqtSignal(QtCore.QPoint)
    
    def connectSbarSignals(self, slot):
        sbar = self.horizontalScrollBar()
        sbar.valueChanged.connect(slot, type=QtCore.Qt.ConnectionType.UniqueConnection)
        sbar.rangeChanged.connect(slot, type=QtCore.Qt.ConnectionType.UniqueConnection)

        sbar = self.verticalScrollBar()
        sbar.valueChanged.connect(slot, type=QtCore.Qt.ConnectionType.UniqueConnection)
        sbar.rangeChanged.connect(slot, type=QtCore.Qt.ConnectionType.UniqueConnection)

    def disconnectSbarSignals(self):
        sbar = self.horizontalScrollBar()
        sbar.valueChanged.disconnect()
        sbar.rangeChanged.disconnect()

        sbar = self.verticalScrollBar()
        sbar.valueChanged.disconnect()
        sbar.rangeChanged.disconnect()

    @property
    def handDragging(self):
        return self._handDrag

    @property
    def scrollState(self):
        centerPoint = self.mapToScene(self.viewport().width()//2,
                                      self.viewport().height()//2)
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
        return self.transform().m11()

    @zoomFactor.setter
    def zoomFactor(self, newZoomFactor):
        newZoomFactor = newZoomFactor / self.zoomFactor
        self.scale(newZoomFactor, newZoomFactor)
    
    def mouseMoveEvent(self, event):
        event.ignore()
        return super().mouseMoveEvent(event)

    def wheelEvent(self, wheelEvent):
        assert isinstance(wheelEvent, QtGui.QWheelEvent)
        if (wheelEvent.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier) or self.scroll_to_zoom_always_on:
            self.wheelNotches.emit(wheelEvent.angleDelta().y() / 240.0)
            wheelEvent.accept()
        else:
            super(SynchableGraphicsView, self).wheelEvent(wheelEvent)

    def keyReleaseEvent(self, keyEvent):
        assert isinstance(keyEvent, QtGui.QKeyEvent)
        keyEvent.ignore()

    def mousePressEvent(self, event):
        assert isinstance(event, QtGui.QMouseEvent)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.enableHandDrag(True)
            event.accept()
        if (not self.right_clicked_is_pressed) and (event.button() == QtCore.Qt.MouseButton.RightButton):
            self.right_clicked_is_pressed = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        assert isinstance(event, QtGui.QMouseEvent)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.enableHandDrag(False)
            event.accept()
        if (self.right_clicked_is_pressed) and (event.button() == QtCore.Qt.MouseButton.RightButton):
            self.right_clicked_is_pressed = False
            self.right_mouse_button_was_clicked.emit(event.position().toPoint())
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        event.ignore()

    def checkTransformChanged(self):
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
        self._transform = self.transform()

    def scrollToTop(self):
        sbar = self.verticalScrollBar()
        sbar.setValue(sbar.minimum())

    def scrollToBottom(self):
        sbar = self.verticalScrollBar()
        sbar.setValue(sbar.maximum())

    def scrollToBegin(self):
        sbar = self.horizontalScrollBar()
        sbar.setValue(sbar.minimum())

    def scrollToEnd(self):
        sbar = self.horizontalScrollBar()
        sbar.setValue(sbar.maximum())

    def centerView(self):
        sbar = self.verticalScrollBar()
        sbar.setValue((sbar.maximum() + sbar.minimum())//2)
        sbar = self.horizontalScrollBar()
        sbar.setValue((sbar.maximum() + sbar.minimum())//2)

    def enableScrollBars(self, enable):
        if enable:
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def enableHandDrag(self, enable):
        if enable:
            if not self._handDrag:
                self._handDrag = True
                self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        else:
            if self._handDrag:
                self._handDrag = False
                self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)

    def dumpTransform(self, t, padding=""):
        print("%s%5.3f %5.3f %5.3f" % (padding, t.m11(), t.m12(), t.m13()))
        print("%s%5.3f %5.3f %5.3f" % (padding, t.m21(), t.m22(), t.m23()))
        print("%s%5.3f %5.3f %5.3f" % (padding, t.m31(), t.m32(), t.m33()))