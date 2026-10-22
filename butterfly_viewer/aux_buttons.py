#!/usr/bin/env python3

"""Button widgets whose icons can be "truly" set to SVG image files.

Not intended as a script. Used in Butterfly Viewer.

Credits:
    SvgButton, SvgToolButton, SvgAbstractButton: Copyright (c) 2022 Jung Gyu Yoon (https://github.com/yjg30737)
        with changes and additions to SvgAbstractButton.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QColor, QPalette, qGray
from PyQt6.QtWidgets import QAbstractButton, QGraphicsColorizeEffect, QWidget, QPushButton, QToolButton



class SvgAbstractButton(QAbstractButton):
    """QAbstractButton whose icon can be truly set to an SVG image file."""

    def __init__(self, base_widget: QWidget = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__baseWidget = base_widget
        self.__initVal()
        self.__styleInit()

    def __initVal(self):
        sc = QtWidgets.QApplication.instance().screens()[0]
        sc.logicalDotsPerInchChanged.connect(self.__scaleChanged)
        self.__size = sc.logicalDotsPerInch() // 4
        self.__padding = self.__border_radius = self.__size // 10
        self.__initBackgroundDefault()
        self.__background_color = self.__background_color_default
        self.__icon = ''
        self.__checked_icon = ''
        self.__checked_icon_css = ''
        self.__animation = ''
        self.installEventFilter(self)
        if self.__baseWidget:
            self.__baseWidget.installEventFilter(self)
            self.__initColorByBaseWidget()
        else:
            self.__initColorDefault()
            self.__hover_color = self.__hover_color_default
            self.__pressed_color = self.__pressed_color_default
            self.__checked_color = self.__checked_color_default
            self.__text_color = self.__text_color_default

    def __initBackgroundDefault(self):
        self.__background_color_default = 'transparent'

    def __initColorDefault(self):
        self.__checked_color_default = '#CCCCCC'
        self.__hover_color_default = self.__getHoverColor(QColor(self.__checked_color_default))
        self.__pressed_color_default = self.__getPressedColor(QColor(self.__checked_color_default))
        self.__text_color_default = '#AAAAAA'
        self.__checked_border_factor = 220

    def __initColorByBaseWidget(self):
        self.__base_color = self.__baseWidget.palette().color(QPalette.ColorRole.Base)
        self.__hover_color = self.__getHoverColor(self.__base_color)
        self.__pressed_color = self.__getPressedColor(self.__base_color)
        self.__checked_color = self.__getPressedColor(self.__base_color)
        self.__text_color = self.__getButtonTextColor(self.__base_color)
        self.__checked_border_factor = 100

    def __getColorByFactor(self, base_color, factor):
        r, g, b = base_color.red(), base_color.green(), base_color.blue()
        gray = qGray(r, g, b)
        if gray > 255 // 2:
            color = base_color.darker(factor)
        else:
            color = base_color.lighter(factor)
        return color

    def __getHoverColor(self, base_color):
        hover_factor = 130
        hover_color = self.__getColorByFactor(base_color, hover_factor)
        return hover_color.name()

    def __getPressedColor(self, base_color):
        pressed_factor = 150
        pressed_color = self.__getColorByFactor(base_color, pressed_factor)
        return pressed_color.name()

    def __getCheckedColor(self, base_color):
        return self.__getPressedColor(base_color)

    def __getButtonTextColor(self, base_color):
        r, g, b = base_color.red() ^ 255, base_color.green() ^ 255, base_color.blue() ^ 255
        if r == g == b:
            text_color = QColor(r, g, b)
        else:
            if qGray(r, g, b) > 255 // 2:
                text_color = QColor(255, 255, 255)
            else:
                text_color = QColor(0, 0, 0)
        return text_color.name()

    def __styleInit(self):
        self.__btn_style = f'''
        QAbstractButton
        {{
        border-width: 2px;
        border-style: solid;
        border-color: transparent;
        width: {self.__size};
        height: {self.__size};
        image: url({self.__icon});
        background-color: {self.__background_color};
        border-radius: {self.__border_radius};
        padding: {self.__padding};
        color: {self.__text_color};
        }}
        QAbstractButton:hover
        {{
        background-color: {self.__hover_color};
        }}
        QAbstractButton:pressed
        {{
        background-color: {self.__pressed_color};
        }}
        QAbstractButton:checked
        {{
        background-color: {self.__checked_color};
        {self.__checked_icon_css}
        border-color: {QColor(self.__checked_color).lighter(self.__checked_border_factor).name()}
        }}
        QAbstractButton:checked:hover
        {{
        background-color: {self.__getHoverColor(QColor(self.__checked_color))};
        }}
        QAbstractButton:checked:pressed
        {{
        background-color: {self.__getPressedColor(QColor(self.__checked_color))};
        }}
        '''

        self.setStyleSheet(self.__btn_style)

    def setIcon(self, icon: str):
        self.__icon = icon
        self.__styleInit()

    def setCheckedIcon(self, icon: str=None):
        self.__checked_icon = icon
        if self.__checked_icon:
            self.__checked_icon_css = f'image: url({self.__checked_icon});'
        else:
            self.__checked_icon_css = ''
        self.__styleInit()

    def eventFilter(self, obj, e):
        if obj == self:
            if e.type() == QtCore.QEvent.Type.EnabledChange:
                effect = QGraphicsColorizeEffect()
                effect.setColor(QColor(255, 255, 255))
                if self.isEnabled():
                    effect.setStrength(0)
                else:
                    effect.setStrength(1)
                    effect.setColor(QColor(150, 150, 150))
                self.setGraphicsEffect(effect)
        if obj == self.__baseWidget:
            if e.type() == QtCore.QEvent.Type.StyleChange:
                if self.__baseWidget.palette().color(QPalette.ColorRole.Base).name() == '#ffffff':
                    if self.__baseWidget.parent():
                        if self.__baseWidget.parent().palette().color(QPalette.ColorRole.Base).name() == '#ffffff':
                            pass
                        else:
                            self.__baseWidget = self.__baseWidget.parent()
                self.__initColorByBaseWidget()
                self.__styleInit()
        return super().eventFilter(obj, e)

    def setPadding(self, padding: int):
        self.__padding = padding
        self.__styleInit()

    def setBorderRadius(self, border_radius: int):
        self.__border_radius = border_radius
        self.__styleInit()

    def setBackground(self, background=None):
        if background:
            self.__background_color = background
        elif self.__baseWidget:
            self.__background_color = self.__base_color.name()
        else:
            self.__background_color = self.__background_color_default
        self.__styleInit()

    def setAsCircle(self):
        self.setBorderRadius(self.height() // 2)
        self.__styleInit()

    def __scaleChanged(self, dpi):
        self.__size = dpi // 4
        self.__styleInit()

    def setHoverColor(self, color=None, auto=False):
        if auto:
            self.__hover_color = self.__getHoverColor(QColor(self.__checked_color))
        elif color:
            self.__hover_color = color
        elif self.__baseWidget:
            self.__hover_color = self.__getHoverColor(self.__base_color)
        else:
            self.__hover_color = self.__hover_color_default
        self.__styleInit()

    def setPressedColor(self, color=None, auto=False):
        if auto:
            self.__pressed_color = self.__getPressedColor(QColor(self.__checked_color))
        elif color:
            self.__pressed_color = color
        elif self.__baseWidget:
            self.__pressed_color = self.__getPressedColor(self.__base_color)
        else:
            self.__pressed_color = self.__pressed_color_default
        self.__styleInit()

    def setCheckedColor(self, color=None):
        if color:
            self.__checked_color = color
        elif self.__baseWidget:
            self.__checked_color = self.__getPressedColor(self.__base_color)
        else:
            self.__checked_color = self.__checked_color_default
        self.__styleInit()

    def setTextColor(self, color=None):
        if color:
            self.__text_color = color
        elif self.__baseWidget:
            self.__text_color = self.__getButtonTextColor(self.__base_color)
        else:
            self.__text_color = self.__text_color_default
        self.__styleInit()

    def setCheckedBorderFactor(self, factor: int=220):
        self.__checked_border_factor = factor
        self.__styleInit()


class SvgButton(QPushButton, SvgAbstractButton):
    def __init__(self, base_widget: QWidget = None, *args, **kwargs):
        super().__init__(base_widget, *args, **kwargs)


class SvgToolButton(QToolButton, SvgAbstractButton):
    def __init__(self, base_widget: QWidget = None, *args, **kwargs):
        super().__init__(base_widget, *args, **kwargs)


class ViewerButton(SvgButton):
    """SvgButton with styles for Butterfly Viewer main interface."""
    def __init__(self, base_widget: QWidget = None, style: str="default", *args, **kwargs):
        super().__init__(base_widget, *args, **kwargs)
        self.setStyle(style)

    def setStyle(self, style: str="default"):
        if "trigger" in style:
            if "severe" in style:
                self.setCheckedColor("#CC0000")
                self.setBackground("rgba(0, 0, 0, 63)")
            elif "split" in style:
                self.setCheckedColor("#eaae01")
                self.setBackground("rgba(0, 0, 0, 63)")
            elif "transparent" in style:
                self.setCheckedColor("#BBBBBB")
                self.setBackground("transparent")
            else:
                self.setCheckedColor("#BBBBBB")
                self.setBackground("rgba(0, 0, 0, 63)")
        elif "invisible" in style:
            self.setCheckedColor("transparent")
            self.setBackground("transparent")
        else:
            if "green-yellow" in style:
                self.setCheckedColor("#FFA500")
                self.setCheckedBorderFactor(170)
                self.setBackground("#008000")
            else:
                self.setCheckedColor("#313191")
                self.setBackground("rgba(0, 0, 0, 63)")

        self.setHoverColor(auto=True)
        self.setPressedColor(auto=True)