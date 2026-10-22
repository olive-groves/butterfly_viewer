#!/usr/bin/env python3

"""Ruler items for CustomQGraphicsScene.

Not intended as a script. Used in Butterfly Viewer.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



import sys
import math
from PyQt6 import QtWidgets, QtCore, QtGui



class CustomItem(QtWidgets.QGraphicsEllipseItem):
    """Endpoint for RulerItem."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.line = None
        self.is_point = None
        self.text = None
        self.text1 = None
        self.text2 = None
        self.unit = "px"
        self.px_per_unit = 1.0
        self.relative_origin_position = "bottomleft"
        self.y_origin = -1

    def add_line(self, line, is_point):
        self.line = line
        self.is_point = is_point

    def add_text(self, text):
        self.text = text

    def add_text1(self, text):
        self.text1 = text

    def add_text2(self, text):
        self.text2 = text

    def set_px_per_unit(self, px_per_unit):
        self.px_per_unit = px_per_unit

    def set_unit(self, unit):
        self.unit = unit

    def set_relative_origin_position(self, relative_origin_position):
        self.relative_origin_position = relative_origin_position
        if self.relative_origin_position == "topleft":
            self.y_origin = +1
        elif self.relative_origin_position == "bottomleft":
            self.y_origin = -1

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value

            self.move_line_to_center(new_pos)
            self.update_text()
            self.move_text(new_pos)
            self.update_text1()
            self.move_text1(new_pos)
            self.update_text2()
            self.move_text2(new_pos)

        return super(CustomItem, self).itemChange(change, value)

    def move_line_to_center(self, new_pos):
        x_offset = self.rect().x() + self.rect().width()/2
        y_offset = self.rect().y() + self.rect().height()/2

        new_center_pos = QtCore.QPointF(new_pos.x()+x_offset, new_pos.y()+y_offset)

        p1 = new_center_pos if self.is_point else self.line.line().p1()
        p2 = self.line.line().p2() if self.is_point else new_center_pos

        self.line.setLine(QtCore.QLineF(p1, p2))

    def update_text(self):
        length_px = self.get_line_length(self.line.line())
        unit = self.unit
        px_per_unit = self.px_per_unit
        length_unit = length_px/px_per_unit
        string_length = "{:.1f}".format(length_unit) + " " + unit
        string = "<div style='background:rgba(0, 0, 0, 91);'>" + string_length + "</div>"
        self.text.setHtml(string)

    def update_text1(self):
        length_px = self.get_line_length(self.line.line())
        unit = self.unit
        px_per_unit = self.px_per_unit
        p1 = self.line.line().p1()
        p2 = self.line.line().p2()

        length_unit = length_px/px_per_unit
        dx_unit = (p1.x()-p2.x())/px_per_unit
        dy_unit = (p1.y()-p2.y())/px_per_unit
        dy_unit *= self.y_origin
        ang = math.degrees(math.atan2(dy_unit, dx_unit))

        string_abs = "|v|  " + "{:.1f}".format(length_unit) + " " + unit
        string_dx = "⬌  " + "{:.1f}".format(dx_unit) + " " + unit
        string_dy = "⬍  " + "{:.1f}".format(dy_unit) + " " + unit
        string_ang = "∠  " + "{:.1f}".format(ang) + "°"
        string = "<div style='background:rgba(0, 0, 0, 91);'>" + string_abs + "<br>" + string_dx + "<br>" + string_dy + "<br>" + string_ang + "</div>"
        self.text1.setHtml(string)

    def update_text2(self):
        length_px = self.get_line_length(self.line.line())
        unit = self.unit
        px_per_unit = self.px_per_unit
        p1 = self.line.line().p1()
        p2 = self.line.line().p2()

        length_unit = length_px/px_per_unit
        dx_unit = (p2.x()-p1.x())/px_per_unit
        dy_unit = (p2.y()-p1.y())/px_per_unit
        dy_unit *= self.y_origin
        ang = math.degrees(math.atan2(dy_unit, dx_unit))

        string_abs = "|v|  " + "{:.1f}".format(length_unit) + " " + unit
        string_dx = "⬌  " + "{:.1f}".format(dx_unit) + " " + unit
        string_dy = "⬍  " + "{:.1f}".format(dy_unit) + " " + unit
        string_ang = "∠  " + "{:.1f}".format(ang) + "°"
        string = "<div style='background:rgba(0, 0, 0, 91);'>" + string_abs + "<br>" + string_dx + "<br>" + string_dy + "<br>" + string_ang + "</div>"
        self.text2.setHtml(string)

    def move_text(self, new_pos):
        if self.text:
            center_pos = self.line.line().center()
            new_pos = QtCore.QPointF(center_pos.x(), center_pos.y())
            self.text.setPos(new_pos)

    def move_text1(self, new_pos):
        if self.text:
            pos = self.line.line().p1()
            new_pos = QtCore.QPointF(pos.x(), pos.y())
            self.text1.setPos(new_pos)

    def move_text2(self, new_pos):
        if self.text:
            pos = self.line.line().p2()
            new_pos = QtCore.QPointF(pos.x(), pos.y())
            self.text2.setPos(new_pos)

    def refresh_positions(self):
        self.move_line_to_center(self.pos())
        self.move_text(self.pos())
        self.update_text()
        self.update_text1()
        self.update_text2()

    def get_line_length(self, line):
        dx = line.x2() - line.x1()
        dy = line.y2() - line.y1()
        length = math.sqrt(dx**2 + dy**2)
        return length



class RulerItem(QtWidgets.QGraphicsRectItem):
    """Movable ruler on QGraphicsScene with a specified unit of length."""

    def __init__(self, unit="px", px_per_mm=None, initial_pos_p1=None, initial_pos_p2=None, relative_origin_position="bottomleft"):
        super().__init__()

        self.unit = unit

        mm_per_unit = 1.0
        if "cm" == unit:
            mm_per_unit = 10.0
        elif "m" == unit:
            mm_per_unit = 1000.0
        elif "in" == unit:
            mm_per_unit = 25.4
        elif "ft" == unit:
            mm_per_unit = 304.8
        elif "yd" == unit:
            mm_per_unit = 914.4
        
        if "px" == unit:
            self.px_per_unit = 1.0
        else:
            self.px_per_unit = px_per_mm * mm_per_unit

        self._mm_per_unit = mm_per_unit
        self.relative_origin_position = relative_origin_position

        if not initial_pos_p1:
            initial_pos_p1 = QtCore.QPointF(10,10)
        if not initial_pos_p2:
            initial_pos_p2 = QtCore.QPointF(100,200)

        pen = QtGui.QPen()
        pen.setWidth(2)
        pen.setCosmetic(True)
        pen.setColor(QtGui.QColor(QtCore.Qt.GlobalColor.white))
        pen.setCapStyle(QtCore.Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
            
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor(QtCore.Qt.GlobalColor.white))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)

        brush_black = QtGui.QBrush()
        brush_black.setColor(QtGui.QColor(QtCore.Qt.GlobalColor.black))
        brush_black.setStyle(QtCore.Qt.BrushStyle.SolidPattern)

        width = 8
        height = 8
        point_topleft = QtCore.QPointF(-width/2, -height/2)
        point_bottomright = QtCore.QPointF(width/2,height/2)
        ellipse_rect = QtCore.QRectF(point_topleft, point_bottomright)

        self.ellipse_item1 = CustomItem(ellipse_rect)
        self.ellipse_item1.setPos(initial_pos_p1)
        self.ellipse_item1.setBrush(brush_black)
        self.ellipse_item1.setPen(pen)

        text_item = QtWidgets.QGraphicsTextItem("text")
        text_item.setPos(0,0)
        font = text_item.font()
        font.setPointSize(11)
        text_item.setFont(font)
        text_item.setDefaultTextColor(QtGui.QColor(QtCore.Qt.GlobalColor.white))
        text_item.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)

        text_item1 = QtWidgets.QGraphicsTextItem("text")
        text_item1.setPos(initial_pos_p1)
        font = text_item1.font()
        font.setPointSize(10)
        text_item1.setFont(font)
        text_item1.setDefaultTextColor(QtGui.QColor(QtCore.Qt.GlobalColor.white))
        text_item1.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        
        text_item2 = QtWidgets.QGraphicsTextItem("text")
        text_item2.setPos(initial_pos_p2)
        font = text_item2.font()
        font.setPointSize(10)
        text_item2.setFont(font)
        text_item2.setDefaultTextColor(QtGui.QColor(QtCore.Qt.GlobalColor.white))
        text_item2.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)

        ellipse_rect = QtCore.QRectF(point_topleft, point_bottomright)

        self.ellipse_item2 = CustomItem(ellipse_rect)
        self.ellipse_item2.setPos(initial_pos_p2)
        self.ellipse_item2.setBrush(brush_black)
        self.ellipse_item2.setPen(pen)

        line_item = QtWidgets.QGraphicsLineItem(QtCore.QLineF(40, 40, 80, 80))
        pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        line_item.setPen(pen)
        self.shadow_line = QtWidgets.QGraphicsDropShadowEffect(blurRadius=4, color=QtGui.QColor(0, 0, 0, 255), xOffset=0, yOffset=0)

        self.ellipse_item1.set_relative_origin_position(self.relative_origin_position)
        self.ellipse_item2.set_relative_origin_position(self.relative_origin_position)

        self.ellipse_item1.add_line(line_item, True)
        self.ellipse_item2.add_line(line_item, False)
        self.ellipse_item1.add_text(text_item)
        self.ellipse_item2.add_text(text_item)
        self.ellipse_item1.add_text1(text_item1)
        self.ellipse_item2.add_text1(text_item1)
        self.ellipse_item1.add_text2(text_item2)
        self.ellipse_item2.add_text2(text_item2)

        self.ellipse_item1.set_px_per_unit(self.px_per_unit)
        self.ellipse_item2.set_px_per_unit(self.px_per_unit)
        self.ellipse_item1.set_unit(self.unit)
        self.ellipse_item2.set_unit(self.unit)

        line_item.setParentItem(self)
        self.ellipse_item1.setParentItem(self)
        self.ellipse_item2.setParentItem(self)
        text_item.setParentItem(self)
        text_item1.setParentItem(self)
        text_item2.setParentItem(self)

        self.ellipse_item2.refresh_positions()
        self.ellipse_item1.refresh_positions()

    def set_and_refresh_px_per_unit(self, px_per_unit):
        unit = self.unit
        if "px" != unit:
            mm_per_unit = self._mm_per_unit
            self.px_per_unit = px_per_unit * mm_per_unit
            self.ellipse_item1.set_px_per_unit(self.px_per_unit)
            self.ellipse_item2.set_px_per_unit(self.px_per_unit)
            self.ellipse_item2.refresh_positions()
            self.ellipse_item1.refresh_positions()

    def set_and_refresh_relative_origin_position(self, relative_origin_position):
        self.relative_origin_position = relative_origin_position
        self.ellipse_item1.set_relative_origin_position(self.relative_origin_position)
        self.ellipse_item2.set_relative_origin_position(self.relative_origin_position)
        self.ellipse_item2.refresh_positions()
        self.ellipse_item1.refresh_positions()



def main():
    app = QtWidgets.QApplication(sys.argv)

    scene = QtWidgets.QGraphicsScene()
    pixmap_item = QtWidgets.QGraphicsPixmapItem()

    pixmap = QtGui.QPixmap(r"C:\image.png")
    pixmap_item.setPixmap(pixmap)

    scene.addItem(pixmap_item)

    ruler = RulerItem()

    scene.addItem(ruler)

    ruler.setPos(50,100)

    view = QtWidgets.QGraphicsView(scene)
    view.show()

    sys.exit(app.exec())



if __name__ == '__main__':
    main()