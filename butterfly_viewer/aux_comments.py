#!/usr/bin/env python3

"""Comment items for CustomQGraphicsScene.

Not intended as a script. Used in Butterfly Viewer.

Creates an editable and movable comment on QGraphicsScene at a given scene position.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt5 import QtWidgets, QtCore, QtGui



class CommentItem(QtWidgets.QGraphicsRectItem):
    """Create an editable and movable comment for QGraphicsScene.

    Features:
        Editable field for plain text.
        Draggable item with visible datum centered at actual location.
        Multiple color schemes.

    Args:
        initial_scene_pos (QPointF): The starting position of the comment datum on the scene.
        color (str): The color scheme based on the presets of text color (white, red, blue, black, yellow, green).
        comment_text (str): Text of the comment.
        set_cursor_on_creation (bool): True to set cursor on comment text field on instantiation; False to ignore.
    """
    def __init__(self, initial_scene_pos=None, color="white", comment_text="Text", set_cursor_on_creation=False):
        super().__init__()

        self.comment_text = comment_text
        self.pos_on_scene = initial_scene_pos
        self.color = color

        pen = QtGui.QPen() 
        pen.setCosmetic(True)
        pen.setWidth(2)
        pen.setColor(QtCore.Qt.white) # setColor also works
        pen.setCapStyle(QtCore.Qt.SquareCap)
        pen.setJoinStyle(QtCore.Qt.MiterJoin)
            
        brush = QtGui.QBrush()
        brush.setColor(QtCore.Qt.white)
        brush.setStyle(QtCore.Qt.SolidPattern)

        width = 4
        height = 4

        ellipse_pos_topleft = QtCore.QPointF(-width/2, -height/2)
        ellipse_pos_bottomright = QtCore.QPointF(width/2,height/2)

        ellipse_rect = QtCore.QRectF(ellipse_pos_topleft, ellipse_pos_bottomright)
        self.ellipse_item = QtWidgets.QGraphicsEllipseItem(ellipse_rect)

        self.ellipse_item.setPos(0,0)
        
        self.ellipse_item.setBrush(brush)
        self.ellipse_item.setPen(pen)

        self.ellipse_item.setFlags(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)

        self.shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=8, color=QtGui.QColor(0, 0, 0, 255), xOffset=0, yOffset=0)

        dx = 30
        dy = -30
        point_p1 = QtCore.QPointF(0,0)
        point_p2 = QtCore.QPointF(dx,dy)
        line = QtCore.QLineF(point_p1, point_p2)
        self.line_item = QtWidgets.QGraphicsLineItem(line)
        pen = QtGui.QPen() 
        pen.setWidth(2)
        pen.setColor(QtCore.Qt.white)
        pen.setCapStyle(QtCore.Qt.SquareCap)
        pen.setJoinStyle(QtCore.Qt.MiterJoin)
        self.line_item.setPen(pen)
        self.line_item.setFlags(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)
        self.line_item.setPos(0,0)
        self.line_item.setGraphicsEffect(self.shadow)

        self.line_item_bounding_box = QtWidgets.QGraphicsLineItem(line)
        # self.line_item_bounding_box = QGraphicsLineItemWithCustomSignals(line)
        pen = QtGui.QPen() 
        pen.setWidth(20)
        pen.setColor(QtCore.Qt.transparent)
        pen.setCapStyle(QtCore.Qt.SquareCap)
        pen.setJoinStyle(QtCore.Qt.MiterJoin)
        self.line_item_bounding_box.setPen(pen)
        self.line_item_bounding_box.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable | QtWidgets.QGraphicsItem.ItemIgnoresTransformations)
        self.line_item_bounding_box.setPos(self.pos_on_scene.x(), self.pos_on_scene.y())

        self.text_item = QtWidgets.QGraphicsTextItem()
        self.text_item.setHtml("<div style='background:rgba(0, 0, 0, 31);'>" + "" + "</div>")
        self.text_item.setPlainText(self.comment_text)
        font = self.text_item.font()
        font.setPointSize(12)
        self.text_item.setFont(font)
        self.text_item.setPos(dx+1,dy-14)
        self.text_item.setDefaultTextColor(QtCore.Qt.white)
        self.text_item.setFlags(QtWidgets.QGraphicsItem.ItemIgnoresTransformations | QtWidgets.QGraphicsItem.ItemIsFocusable) # QtWidgets.QGraphicsItem.ItemIsSelectable
        self.text_item.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)

        self.text_item.setParentItem(self.line_item)
        self.ellipse_item.setParentItem(self.line_item)
        self.line_item.setParentItem(self.line_item_bounding_box)

        self.line_item_bounding_box.setParentItem(self)

        self.set_color(self.color)

        if set_cursor_on_creation:
            self.set_cursor()

    def set_cursor(self):
        """Set cursor on the comment text field."""
        self.text_item.setFocus(QtCore.Qt.MouseFocusReason)
        self.text_item.setSelected(True);
        cursor = self.text_item.textCursor()
        cursor.select(QtGui.QTextCursor.Document)
        self.text_item.setTextCursor(cursor)

    def get_scene_pos(self):
        """QPointF: Get datum position of the comment."""
        scene_pos = self.line_item_bounding_box.pos()
        return scene_pos

    def get_comment_text_qstring(self):
        """QString: Get comment text."""
        text_qstring = self.text_item.toPlainText()
        return text_qstring

    def get_comment_text_str(self):
        """str: Get comment text."""
        text_qstring = self.get_comment_text_qstring()
        text_str = str(text_qstring)
        return text_str

    def get_color(self):
        """str: Get descriptor of color."""
        color = self.color
        return color

    def set_color(self, color="white"):
        """Set color based on the presets of text color (white, red, blue, black, yellow, green).

        Applies highlight behind the text to make it more visible over images.

        Args:
            color (str): The color scheme based on the presets of text color (white, red, blue, black, yellow, green).
        """
        pen_ellipse = self.ellipse_item.pen()
        pen_line = self.line_item.pen()

        self.color = color
        needs_background = "dark"
        color_code = QtCore.Qt.white

        if color == "red":
            color_code = QtCore.Qt.red
            needs_background = "light"
        elif color == "blue":
            color_code = QtCore.Qt.blue
            needs_background = "light"
        elif color == "black":
            color_code = QtCore.Qt.black
            needs_background = "light"
            self.text_item.setHtml("<div style='background:rgba(255, 255, 255, 255);'>" + str(self.text_item.toPlainText()).replace("\n","<br>") + "</div>")
            self.shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=8, color=QtGui.QColor(255, 255, 255, 255), xOffset=0, yOffset=0)
            self.line_item.setGraphicsEffect(self.shadow)
        elif color == "yellow":
            needs_background = "dark"
            color_code = QtCore.Qt.yellow
        elif color == "green":
            needs_background = "dark"
            color_code = QtCore.Qt.green

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