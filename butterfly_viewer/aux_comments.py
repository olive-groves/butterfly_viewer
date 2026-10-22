#!/usr/bin/env python3

"""Comment items for CustomQGraphicsScene.

Not intended as a script. Used in Butterfly Viewer.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt6 import QtWidgets, QtCore, QtGui



class CommentItem(QtWidgets.QGraphicsRectItem):
    """Create an editable and movable comment for QGraphicsScene."""

    def __init__(self, initial_scene_pos=None, color="white", comment_text="Text", set_cursor_on_creation=False):
        super().__init__()

        self.comment_text = comment_text
        self.pos_on_scene = initial_scene_pos
        self.color = color

        pen = QtGui.QPen() 
        pen.setCosmetic(True)
        pen.setWidth(2)
        pen.setColor(QtGui.QColor(QtCore.Qt.GlobalColor.white))
        pen.setCapStyle(QtCore.Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
            
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor(QtCore.Qt.GlobalColor.white))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)

        width = 4
        height = 4

        ellipse_pos_topleft = QtCore.QPointF(-width/2, -height/2)
        ellipse_pos_bottomright = QtCore.QPointF(width/2,height/2)

        ellipse_rect = QtCore.QRectF(ellipse_pos_topleft, ellipse_pos_bottomright)
        self.ellipse_item = QtWidgets.QGraphicsEllipseItem(ellipse_rect)

        self.ellipse_item.setPos(0,0)
        self.ellipse_item.setBrush(brush)
        self.ellipse_item.setPen(pen)
        self.ellipse_item.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)

        self.shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=8, color=QtGui.QColor(0, 0, 0, 255), xOffset=0, yOffset=0)

        dx = 30
        dy = -30
        point_p1 = QtCore.QPointF(0,0)
        point_p2 = QtCore.QPointF(dx,dy)
        line = QtCore.QLineF(point_p1, point_p2)
        self.line_item = QtWidgets.QGraphicsLineItem(line)
        pen = QtGui.QPen() 
        pen.setWidth(2)
        pen.setColor(QtGui.QColor(QtCore.Qt.GlobalColor.white))
        pen.setCapStyle(QtCore.Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
        self.line_item.setPen(pen)
        self.line_item.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.line_item.setPos(0,0)
        self.line_item.setGraphicsEffect(self.shadow)

        self.line_item_bounding_box = QtWidgets.QGraphicsLineItem(line)
        pen = QtGui.QPen() 
        pen.setWidth(20)
        pen.setColor(QtGui.QColor(QtCore.Qt.GlobalColor.transparent))
        pen.setCapStyle(QtCore.Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
        self.line_item_bounding_box.setPen(pen)
        self.line_item_bounding_box.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.line_item_bounding_box.setPos(self.pos_on_scene.x(), self.pos_on_scene.y())

        self.text_item = QtWidgets.QGraphicsTextItem()
        self.text_item.setHtml("<div style='background:rgba(0, 0, 0, 31);'>" + "" + "</div>")
        self.text_item.setPlainText(self.comment_text)
        font = self.text_item.font()
        font.setPointSize(12)
        self.text_item.setFont(font)
        self.text_item.setPos(dx+1,dy-14)
        self.text_item.setDefaultTextColor(QtGui.QColor(QtCore.Qt.GlobalColor.white))
        self.text_item.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations |
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        self.text_item.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextEditorInteraction)

        self.text_item.setParentItem(self.line_item)
        self.ellipse_item.setParentItem(self.line_item)
        self.line_item.setParentItem(self.line_item_bounding_box)

        self.line_item_bounding_box.setParentItem(self)

        self.set_color(self.color)

        if set_cursor_on_creation:
            self.set_cursor()

    def set_cursor(self):
        self.text_item.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
        self.text_item.setSelected(True)
        cursor = self.text_item.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.Document)
        self.text_item.setTextCursor(cursor)

    def get_scene_pos(self):
        scene_pos = self.line_item_bounding_box.pos()
        return scene_pos

    def get_comment_text_qstring(self):
        text_qstring = self.text_item.toPlainText()
        return text_qstring

    def get_comment_text_str(self):
        text_qstring = self.get_comment_text_qstring()
        text_str = str(text_qstring)
        return text_str

    def get_color(self):
        color = self.color
        return color

    def set_color(self, color="white"):
        pen_ellipse = self.ellipse_item.pen()
        pen_line = self.line_item.pen()

        self.color = color
        needs_background = "dark"
        color_code = QtGui.QColor(QtCore.Qt.GlobalColor.white)

        if color == "red":
            color_code = QtGui.QColor(QtCore.Qt.GlobalColor.red)
            needs_background = "light"
        elif color == "blue":
            color_code = QtGui.QColor(QtCore.Qt.GlobalColor.blue)
            needs_background = "light"
        elif color == "black":
            color_code = QtGui.QColor(QtCore.Qt.GlobalColor.black)
            needs_background = "light"
            self.text_item.setHtml("<div style='background:rgba(255, 255, 255, 255);'>" + str(self.text_item.toPlainText()).replace("\n","<br>") + "</div>")
            self.shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=8, color=QtGui.QColor(255, 255, 255, 255), xOffset=0, yOffset=0)
            self.line_item.setGraphicsEffect(self.shadow)
        elif color == "yellow":
            needs_background = "dark"
            color_code = QtGui.QColor(QtCore.Qt.GlobalColor.yellow)
        elif color == "green":
            needs_background = "dark"
            color_code = QtGui.QColor(QtCore.Qt.GlobalColor.green)

        if needs_background == "light":
            self.text_item.setHtml("<div style='background:rgba(255, 255, 255, 123);'>" + str(self.text_item.toPlainText()).replace("\n","<br>") + "</div>")
            self.shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=8, color=QtGui.QColor(255, 255, 255, 255), xOffset=0, yOffset=0)
        elif needs_background == "dark":
            self.text_item.setHtml("<div style='background:rgba(0, 0, 0, 31);'>" + str(self.text_item.toPlainText()).replace("\n","<br>") + "</div>")
            self.shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=8, color=QtGui.QColor(0, 0, 0, 255), xOffset=0, yOffset=0)
        
        self.line_item.setGraphicsEffect(self.shadow)

        pen_ellipse.setColor(color_code)
        pen_line.setColor(color_code)

        self.ellipse_item.setPen(pen_ellipse)
        self.line_item.setPen(pen_line)
        self.text_item.setDefaultTextColor(color_code)