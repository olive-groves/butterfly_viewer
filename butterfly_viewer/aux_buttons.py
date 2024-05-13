from PyQt5.QtGui import QColor, QPalette, qGray
from PyQt5.QtWidgets import QAbstractButton, QGraphicsColorizeEffect, QWidget, qApp, QPushButton, QToolButton

import os
import inspect
import posixpath



def getabsres(res: str):
    """
    
    Copyright (c) 2022 Jung Gyu Yoon

    From https://github.com/yjg30737/absresgetter/"""
    stack_lst = inspect.stack()
    res_frame_idx = 0
    for i in range(len(stack_lst)):
        context = stack_lst[i].code_context[0]
        if context.find(res) == -1:
            pass
        else:
            res_frame_idx = i
    caller_path = os.path.dirname(stack_lst[res_frame_idx].filename)
    return os.path.join(caller_path, res).replace(os.path.sep, posixpath.sep)


class SvgAbstractButton(QAbstractButton):
    """Modified SvgAbstractButton with color defaults and setters.
    
    Original SvgAbstractButton: Copyright (c) 2022 Jung Gyu Yoon
    From https://github.com/yjg30737/pyqt-svg-abstractbutton"""
    def __init__(self, base_widget: QWidget = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__baseWidget = base_widget
        self.__initVal()
        self.__styleInit()

    def __initVal(self):
        # to set size accordance with scale
        sc = qApp.screens()[0]
        sc.logicalDotsPerInchChanged.connect(self.__scaleChanged)
        self.__size = sc.logicalDotsPerInch() // 4
        self.__padding = self.__border_radius = self.__size // 10
        self.__initBackgroundDefault()
        self.__background_color = self.__background_color_default
        self.__icon = ''
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
        self.__hover_color_default = '#DDDDDD'
        self.__pressed_color_default = '#FFFFFF'
        self.__checked_color_default = '#CCCCCC'
        self.__text_color_default = '#AAAAAA'

    def __initColorByBaseWidget(self):
        self.__base_color = self.__baseWidget.palette().color(QPalette.Base)
        self.__hover_color = self.__getHoverColor(self.__base_color)
        self.__pressed_color = self.__getPressedColor(self.__base_color)
        self.__checked_color = self.__getPressedColor(self.__base_color)
        self.__text_color = self.__getButtonTextColor(self.__base_color)

    def __getColorByFactor(self, base_color, factor):
        r, g, b = base_color.red(), base_color.green(), base_color.blue()
        gray = qGray(r, g, b)
        if gray > 255 // 2:
            color = base_color.darker(factor)
        else:
            color = base_color.lighter(factor)
        return color

    def __getHoverColor(self, base_color):
        hover_factor = 120
        hover_color = self.__getColorByFactor(base_color, hover_factor)
        return hover_color.name()

    def __getPressedColor(self, base_color):
        pressed_factor = 130
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
        border: 0;
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
        }}
        QAbstractButton:checked:hover
        {{
        background-color: {QColor(self.__checked_color).lighter(130).name()};
        }}
        QAbstractButton:checked:pressed
        {{
        background-color: {QColor(self.__checked_color).lighter(150).name()};
        }}
        '''

        self.setStyleSheet(self.__btn_style)

    def setIcon(self, icon: str):
        self.__icon = getabsres(icon)
        self.__styleInit()

    def eventFilter(self, obj, e):
        if obj == self:
            # to change grayscale when button gets disabled
            # if button get enabled/disabled EnableChange will emit
            # so catch the EnabledChange
            if e.type() == 98:
                # change to enabled state
                effect = QGraphicsColorizeEffect()
                effect.setColor(QColor(255, 255, 255))
                if self.isEnabled():
                    effect.setStrength(0)
                else:
                    effect.setStrength(1)
                    effect.setColor(QColor(150, 150, 150))
                self.setGraphicsEffect(effect)
        if obj == self.__baseWidget:
            # catch the StyleChange event of base widget
            if e.type() == 100:
                # if base widget's background is transparent (#ffffff)
                if self.__baseWidget.palette().color(QPalette.Base).name() == '#ffffff':
                    # then check the parent widget's background
                    if self.__baseWidget.parent():
                        if self.__baseWidget.parent().palette().color(QPalette.Base).name() == '#ffffff':
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

    # to set size accordance with scale
    def __scaleChanged(self, dpi):
        self.__size = dpi // 4
        self.__styleInit()

    def setHoverColor(self, color=None):
        """Set color when hovered ('#XXXXXX', '#XXX', '<color>', 'transparent', None)
        """
        if color:
            self.__hover_color = color
        elif self.__baseWidget:
            self.__hover_color = self.__getHoverColor(self.__base_color)
        else:
            self.__hover_color = self.__hover_color_default
        self.__styleInit()

    def setPressedColor(self, color=None):
        """Set color when pressed ('#XXXXXX', '#XXX', '<color>', 'transparent', None)
        """
        if color:
            self.__pressed_color = color
        elif self.__baseWidget:
            self.__pressed_color = self.__getPressedColor(self.__base_color)
        else:
            self.__pressed_color = self.__pressed_color_default
        self.__styleInit()

    def setCheckedColor(self, color=None):
        """Set color when checked ('#XXXXXX', '#XXX', '<color>', 'transparent', None)
        """
        if color:
            self.__checked_color = color
        elif self.__baseWidget:
            self.__checked_color = self.__getPressedColor(self.__base_color)
        else:
            self.__checked_color = self.__checked_color_default
        self.__styleInit()

    def setTextColor(self, color=None):
        """Set text color ('#XXXXXX', '#XXX', '<color>', 'transparent', None)
        """
        if color:
            self.__text_color = color
        elif self.__baseWidget:
            self.__text_color = self.__getButtonTextColor(self.__base_color)
        else:
            self.__text_color = self.__text_color_default
        self.__styleInit()


class SvgButton(QPushButton, SvgAbstractButton):
    """
    
    Copyright (c) 2022 Jung Gyu Yoon

    From https://github.com/yjg30737/pyqt-svg-button/"""
    def __init__(self, base_widget: QWidget = None, *args, **kwargs):
        super().__init__(base_widget, *args, **kwargs)


class SvgToolButton(QToolButton, SvgAbstractButton):
    """
    
    Copyright (c) 2022 Jung Gyu Yoon

    From https://github.com/yjg30737/pyqt-svg-toolbutton/blob/main/pyqt_svg_toolbutton/svgToolButton.py"""
    def __init__(self, base_widget: QWidget = None, *args, **kwargs):
        super().__init__(base_widget, *args, **kwargs)


class ViewerButton(QPushButton, SvgAbstractButton):
    """Extend SvgButton with setters for hover, pressed, and checked."""
    def __init__(self, base_widget: QWidget = None, *args, **kwargs):
        super().__init__(base_widget, *args, **kwargs)  
        self.setHoverColor("#BBBBBB")
        self.setPressedColor("#DDDDDD")
        self.setCheckedColor("#ff00ff")


class ToggleViewerButton(ViewerButton):
    """Toggle-style ViewerButton.
    
    Styled for buttons which toggle states."""
    def __init__(self, base_widget: QWidget = None, *args, **kwargs):
        super().__init__(base_widget, *args, **kwargs)
        # Set toggled icon, color, and override toggle event to switch icon?


class TriggerViewerButton(ViewerButton):
    """Trigger-style ViewerButton.
    
    Styled for buttons which trigger events."""
    def __init__(self, base_widget: QWidget = None, *args, **kwargs):
        super().__init__(base_widget, *args, **kwargs)

    # Method to set as a "This is a pretty severe trigger" aka "No take-backs trigger", like closing all windows