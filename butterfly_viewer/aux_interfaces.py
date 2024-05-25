#!/usr/bin/env python3

"""User interface widgets and their supporting subwidgets for Butterfly Viewer.

Not intended as a script.

Interface widgets are:
    SplitViewCreator, for users to add images in a 2x2 drag-and-drop zone from which to create a sliding overlay.
    SplitViewManager, for shortcut buttons to position and lock the position of the split in a sliding overlay.
    SlidersOpacitySplitViews, for sliders to the transparencies of a SplitView's overlayed images.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



import time

from PyQt5 import QtWidgets, QtCore, QtGui

from aux_dragdrop import FourDragDropImageLabel
from aux_buttons import ViewerButton



class FourDragDropImageLabelForSplitView(FourDragDropImageLabel):
    """Extends a 2x2 drag-and-drop zone for SplitViewCreator.
    
    Requires a base image (main; top-left) to be given before other images of SplitView may be added.

    Instantiate without input:
        self.drag_drop_area = FourDragDropImageLabelForSplitView()
    """

    main_became_occupied = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.set_addable_all_except_main(False)
        self.app_main_topleft.became_occupied.connect(self.on_main_topleft_occupied)
        self.app_main_topleft.became_occupied.connect(self.main_became_occupied)


    # Set style and function of drag-and-drop zones

    def set_addable_all_except_main(self, boolean):
        """Set all overlay images to be (or not to be) addable via drag-and-drop.

        Convenience for the SplitViewCreator.

        Args:
            boolean (bool): True to make the overlay images addable; False to make un-addable.
        """
        self.app_topright.set_addable(boolean)
        self.app_bottomright.set_addable(boolean)
        self.app_bottomleft.set_addable(boolean)

    def on_main_topleft_occupied(self, boolean):
        """Set when base image becomes occupied or unoccupied to set whether overlay images can be added.
        
        Args:
            boolean (bool): True to indicate base image is occupied (and thus overlay images may be added); 
             False to indicate main image is unoccupied (and thus overlay images may not be added)."""
        self.set_addable_all_except_main(boolean)



class SplitViewCreator(QtWidgets.QFrame):
    """Interface for users to add images from which to create a SplitView.
    
    Users can add local image files via drag-and-drop and "Select image..." dialogs.

    Instantiate without input. See Butterfly Viewer for implementation.
    """
    
    clicked_create_splitview_pushbutton = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()  
        
        main_layout = QtWidgets.QGridLayout()
        
        self.drag_drop_area = FourDragDropImageLabelForSplitView()
        self.drag_drop_area.will_start_loading.connect(self.display_loading_grayout)
        self.drag_drop_area.has_stopped_loading.connect(self.display_loading_grayout)
        
        self.buttons_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        self.create_splitview_pushbutton = QtWidgets.QPushButton("Create")
        self.create_splitview_pushbutton.setToolTip("Create a sliding overlay window with these images")
        self.create_splitview_pushbutton.setStyleSheet("QPushButton { font-size: 10pt; }")
        self.create_splitview_pushbutton.clicked.connect(self.clicked_create_splitview_pushbutton)

        self.create_splitview_pushbutton.setEnabled(False)
        self.drag_drop_area.main_became_occupied.connect(self.create_splitview_pushbutton.setEnabled)
        
        self.buttons_layout.addWidget(self.create_splitview_pushbutton)

        self.loading_grayout_label = QtWidgets.QLabel("Loading...")
        self.loading_grayout_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.loading_grayout_label.setVisible(False)
        self.loading_grayout_label.setStyleSheet("""
            QLabel { 
                color: white;
                font-size: 7.5pt;
                background-color: rgba(0,0,0,223);
                } 
            """)

        self.title_label = QtWidgets.QLabel("Sliding overlay creator")
        self.title_label.setAlignment(QtCore.Qt.AlignLeft)
        self.title_label.setStyleSheet("""
            QLabel { 
                font-size: 10pt;
                } 
            """)
        
        main_layout.addWidget(self.title_label,0,0)
        main_layout.addWidget(self.drag_drop_area, 1, 0)
        main_layout.addLayout(self.buttons_layout, 2, 0)
        main_layout.addWidget(self.loading_grayout_label, 0, 0, 3, 1)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setContentsMargins(4,4,4,4)
        
        # self.setMinimumWidth(250)
        # self.setMinimumHeight(325)
        
        self.setLayout(main_layout)
        self.setContentsMargins(2,2,2,2) # As docked on left side
        
        self.setStyleSheet("QFrame {background: palette(window); border-radius: 0.5em;}")

    def setMouseTracking(self, flag):
        """PyQt flag: Override mouse tracking to set mouse tracking for all children widgets."""
        def recursive_set(parent):
            for child in parent.findChildren(QtCore.QObject): # Needed to track the split in sliding overlays while hovering over interfaces and other widgets; prevents sudden stops and jumps of the split
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)
        QtWidgets.QWidget.setMouseTracking(self, flag)
        recursive_set(self)

    def display_loading_grayout(self, boolean, text="Loading...", pseudo_load_time=0.2): 
        """Show/hide grayout screen for loading sequences.

        Args:
            boolean (bool): True to show grayout; False to hide.
            text (str): The text to show on the grayout.
            pseudo_load_time (float): The delay (in seconds) to hide the grayout to give users a feeling of action.
        """ 
        # Needed to give feedback to user that images are loading
        if not boolean:
            text = "Loading..."
        self.loading_grayout_label.setText(text)
        self.loading_grayout_label.setVisible(boolean)
        if boolean:
            self.loading_grayout_label.repaint()
        if not boolean:
            time.sleep(pseudo_load_time)



class SliderDeluxe(QtWidgets.QWidget):
    """Custom slider for setting and indicating the transparencies of overlay images in SplitView.
    
    Used in SlidersOpacitySplitViews.
    
    Args:
        name (str): Text for slider label.
        pixmap_preview_position (str): The position of the preview icon for indicating opacity ("Full", "Top right", "Bottom right", "Bottom left").
    """   

    was_changed_slider_value = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, name="Text", pixmap_preview_position="Full"):
        super().__init__()

        self.show_pixmap_preview = True

        self.slider = QtWidgets.QSlider(
            QtCore.Qt.Horizontal,
            minimum=0,
            maximum=100,
            value=100,
            valueChanged=self.on_slider_changed,
        )

        # Updated valueChanged to actionTriggered to prevent unwanted recursive behavior.
        # When a slider is set programmatically to refresh a UI, the value changing shouldn't trigger subsequent UI effects which think "Ah, the user has changed it" when that isn't the case.
        # Example: The split is set temporarily to the window center when changing transparencies, but that split shouldn't move when refreshing the transparency sliders.
        self.slider.actionTriggered.connect(self.on_slider_trigger)

        self.slider.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.slider.setTickInterval(10)
        self.slider.setSingleStep(5)
        self.slider.setStyleSheet("""
            QSlider { 
                font-size: 10pt;
                } 
            """)

        self.spinbox = QtWidgets.QSpinBox()
        self.spinbox.setMinimum(self.slider.minimum())
        self.spinbox.setMaximum(self.slider.maximum())
        self.spinbox.setSingleStep(1)
        self.spinbox.setValue(self.slider.value())
        self.spinbox.setAlignment(QtCore.Qt.AlignRight)
        self.spinbox.setStyleSheet("""
            QSpinBox { 
                font-size: 10pt;
                } 
            """)

        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)
        self.spinbox.valueChanged.connect(self.on_spinbox_change)

        layout = QtWidgets.QHBoxLayout()

        if name is not None:
            self.label = QtWidgets.QLabel(name, alignment=QtCore.Qt.AlignCenter)
            layout.addWidget(self.label)

        layout.addWidget(self.slider)
        layout.addWidget(self.spinbox)
        layout.setContentsMargins(2,2,2,2)
        layout.setSpacing(4)

        if self.show_pixmap_preview:

            checker_length = 10

            self.pixmap_icon = QtGui.QPixmap(checker_length*2+2, checker_length*2+2)
            self.pixmap_icon.fill(QtCore.Qt.transparent)

            self.pixmap_outline = QtGui.QPixmap(self.pixmap_icon.size())
            self.pixmap_outline.fill(QtCore.Qt.transparent)

            if pixmap_preview_position == "Top left":
                x_0 = 0
                y_0 = 0
                x   = 0.5*checker_length
                y   = 0.5*checker_length

            elif pixmap_preview_position == "Top right":
                x_0 = checker_length
                y_0 = 0
                x   = 0.5*checker_length
                y   = 0.5*checker_length

            elif pixmap_preview_position == "Bottom right":
                x_0 = checker_length
                y_0 = checker_length
                x   = 0.5*checker_length
                y   = 0.5*checker_length

            elif pixmap_preview_position == "Bottom left":
                x_0 = 0
                y_0 = checker_length
                x   = 0.5*checker_length
                y   = 0.5*checker_length
                
            else:
                x_0 = 0
                y_0 = 0
                x   = checker_length
                y   = checker_length

            painter_icon = QtGui.QPainter(self.pixmap_icon)

            painter_icon.setPen(QtCore.Qt.NoPen)
            painter_icon.setBrush(QtCore.Qt.black)
            painter_icon.drawRect(x_0, y_0, 2.0*x + 1, 2.0*y + 1)

            painter_icon.setPen(QtCore.Qt.NoPen)
            painter_icon.setBrush(QtCore.Qt.white)
            painter_icon.drawRect(1 + x_0, 1 + y_0, x, y)
            painter_icon.drawRect(1 + x_0 + x, 1 + y_0 + y, x, y)

            painter_icon.end()
            

            painter_outline = QtGui.QPainter(self.pixmap_outline)

            painter_outline.setPen(QtCore.Qt.black)
            painter_outline.setBrush(QtCore.Qt.NoBrush)
            painter_outline.drawRect(x_0, y_0, 2.0*x + 1, 2.0*y + 1)
 
            painter_outline.setPen(QtCore.Qt.black)
            painter_outline.setBrush(QtCore.Qt.NoBrush)
            painter_outline.drawRect(0, 0, 2*checker_length + 1, 2*checker_length + 1)

            painter_outline.end()


            pixmap = QtGui.QPixmap(self.pixmap_icon.size())
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.drawPixmap(QtCore.QPoint(), self.pixmap_icon)
            painter.drawPixmap(QtCore.QPoint(), self.pixmap_outline)
            painter.end()


            self.label_pixmap = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
            self.label_pixmap.setPixmap(pixmap)
            layout.insertWidget(0, self.label_pixmap)

        self.setLayout(layout)

    @QtCore.pyqtSlot(int)
    def on_slider_changed(self, value):
        """Set opacity of preview icon when slider is changed.
        
        Triggered when the slider value changes.

        Args:
            value (int): Opacity, where 100 is opaque (not transparent) and 0 is transparent.
        """
        if self.show_pixmap_preview:
            new_pix = QtGui.QPixmap(self.pixmap_icon.size())
            new_pix.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(new_pix)
            painter.setOpacity(value * 0.01)
            painter.drawPixmap(QtCore.QPoint(), self.pixmap_icon)
            painter.setOpacity(1)
            painter.drawPixmap(QtCore.QPoint(), self.pixmap_outline)
            painter.end()
            self.label_pixmap.setPixmap(new_pix)

    def on_slider_trigger(self, action):
        """QAction: Signal the slider position when slider is triggered."""
        self.was_changed_slider_value.emit(self.slider.sliderPosition())

    def on_spinbox_change(self, value):
        """int: Signal the slider position when spinbox is changed."""
        self.was_changed_slider_value.emit(self.slider.sliderPosition())

    def set_value(self, value):
        """int (0-100): Set value of slider."""
        self.slider.setValue(value)



class SlidersOpacitySplitViews(QtWidgets.QFrame):
    """Interface for changing the transparency (opposite of opacity) of the overlay images of a SplitView.

    Instantiate without input. See Butterfly Viewer for implementation.
    """

    was_changed_slider_base_value = QtCore.pyqtSignal(int)
    was_changed_slider_topright_value = QtCore.pyqtSignal(int)
    was_changed_slider_bottomright_value = QtCore.pyqtSignal(int)
    was_changed_slider_bottomleft_value = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):

        super().__init__()

        self.slider_base = SliderDeluxe(name=None, pixmap_preview_position="Base")
        self.slider_base.setToolTip("Adjust transparency of base image (0% = transparent; 100% = opaque)")
        self.slider_topright = SliderDeluxe(name=None, pixmap_preview_position="Top right")
        self.slider_topright.setToolTip("Adjust transparency of top right of sliding overlay (0% = transparent; 100% = opaque)")
        self.slider_bottomright = SliderDeluxe(name=None, pixmap_preview_position="Bottom right")
        self.slider_bottomright.setToolTip("Adjust transparency of bottom right of sliding overlay (0% = transparent; 100% = opaque)")
        self.slider_bottomleft = SliderDeluxe(name=None, pixmap_preview_position="Bottom left")
        self.slider_bottomleft.setToolTip("Adjust transparency of bottom left of sliding overlay (0% = transparent; 100% = opaque)")

        self.slider_base.was_changed_slider_value.connect(self.was_changed_slider_base_value)
        self.slider_topright.was_changed_slider_value.connect(self.was_changed_slider_topright_value)
        self.slider_bottomright.was_changed_slider_value.connect(self.was_changed_slider_bottomright_value)
        self.slider_bottomleft.was_changed_slider_value.connect(self.was_changed_slider_bottomleft_value)

        layout_sliders = QtWidgets.QGridLayout()

        layout_sliders.addWidget(self.slider_base, 0, 1)
        layout_sliders.addWidget(self.slider_topright, 1, 1)
        layout_sliders.addWidget(self.slider_bottomright, 2, 1)
        layout_sliders.addWidget(self.slider_bottomleft, 3, 1)

        self.label_base = QtWidgets.QLabel("", alignment=QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.label_topright = QtWidgets.QLabel("", alignment=QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.label_bottomright = QtWidgets.QLabel("", alignment=QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.label_bottomleft = QtWidgets.QLabel("", alignment=QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

        self.title_label = QtWidgets.QLabel("Opacity of active image window")
        self.title_label.setAlignment(QtCore.Qt.AlignLeft)
        self.title_label.setStyleSheet("""
            QLabel { 
                font-size: 10pt;
                } 
            """)

        layout_sliders.addWidget(self.label_base, 0, 0)
        layout_sliders.addWidget(self.label_topright, 1, 0)
        layout_sliders.addWidget(self.label_bottomright, 2, 0)
        layout_sliders.addWidget(self.label_bottomleft, 3, 0)

        layout_sliders.setContentsMargins(0,0,0,0)
        layout_sliders.setSpacing(0)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.title_label,0,0)
        layout.addLayout(layout_sliders,1,0)
        
        contents_margins_w = 4
        layout.setContentsMargins(contents_margins_w, contents_margins_w, contents_margins_w, contents_margins_w)
        layout.setSpacing(2*contents_margins_w)

        self.setLayout(layout)
        #self.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Sunken)
        self.setStyleSheet("QFrame {background: palette(window); border-radius: 0.5em;}")
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setContentsMargins(2,2,2,2)

        self.setMinimumWidth(220)

        self.set_enabled_base(False)
        self.set_enabled_topright(False)
        self.set_enabled_bottomright(False)
        self.set_enabled_bottomleft(False)


    def update_sliders(self, opacity_base, opacity_topright, opacity_bottomright, opacity_bottomleft):
        """Update the values of the opacity sliders.
        
        Arg: 
            opacity_topright (int): Set the value of the slider for top-right of SplitView (0-100).
            opacity_bottomright (int): Set the value of the slider for bottom-right slider of SplitView (0-100).
            opacity_bottomleft (int): Set the value of the slider for bottom-left slider of SplitView (0-100).
        """
        self.slider_base.set_value(opacity_base)
        self.slider_topright.set_value(opacity_topright)
        self.slider_bottomright.set_value(opacity_bottomright)
        self.slider_bottomleft.set_value(opacity_bottomleft)

    def reset_sliders(self):
        """Reset all sliders to 100 and disable them (convenience)."""
        self.update_sliders(100, 100, 100, 100)
        self.set_enabled(False, False, False, False)

    def set_enabled(self, boolean_base, boolean_topright, boolean_bottomright, boolean_bottomleft):
        """Enable/disable opacity sliders (convenience).
        
        Arg: 
            boolean_base (bool): True is enabled; False is disabled.
            boolean_topright (bool): True is enabled; False is disabled.
            boolean_bottomright (bool): True is enabled; False is disabled.
            boolean_bottomleft (bool): True is enabled; False is disabled.
        """
        self.set_enabled_base(boolean_base)
        self.set_enabled_topright(boolean_topright)
        self.set_enabled_bottomright(boolean_bottomright)
        self.set_enabled_bottomleft(boolean_bottomleft)

    def set_enabled_base(self, boolean):
        """bool: Enable/disable opacity slider and label for base of SplitView."""
        self.slider_base.setEnabled(boolean)
        self.label_base.setEnabled(boolean)

    def set_enabled_topright(self, boolean):
        """bool: Enable/disable opacity slider and label for top-right of SplitView."""
        self.slider_topright.setEnabled(boolean)
        self.label_topright.setEnabled(boolean)

    def set_enabled_bottomright(self, boolean):
        """bool: Enable/disable opacity slider and label for bottom-right of SplitView."""
        self.slider_bottomright.setEnabled(boolean)
        self.label_bottomright.setEnabled(boolean)

    def set_enabled_bottomleft(self, boolean):
        """bool: Enable/disable opacity slider and label for bottom-left of SplitView."""
        self.slider_bottomleft.setEnabled(boolean)
        self.label_bottomleft.setEnabled(boolean)

    def setMouseTracking(self, flag):
        """PyQt flag: Override mouse tracking to set mouse tracking for all children widgets."""
        def recursive_set(parent):
            for child in parent.findChildren(QtCore.QObject):
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)
        QtWidgets.QWidget.setMouseTracking(self, flag)
        recursive_set(self)



class PushbuttonSplitViewSet(ViewerButton):
    """Custom ViewerButton for buttons in SplitViewManager to set the position of the split in a SplitView.
    
    Args:
        url (str): The SVG icon of the split shortcut.
        x (float): The position of the split (0-1) of which is to be "shortcutted" as a proportion of the base image's horizontal resolution.
        y (float): The position of the split (0-1) of which is to be "shortcutted" as a proportion of the base image's vertical resolution.
    """

    hovered_xy = QtCore.pyqtSignal(float,float)
    clicked_xy = QtCore.pyqtSignal(float,float)

    def __init__(self, parent=None, url: str=None, x=None, y=None):
        super().__init__(style="trigger-split")
        if url: self.setIcon(url)
        self.x = x
        self.y = y
        self.clicked.connect(self.on_clicked)

        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            
    def enterEvent(self, event):
        """Override enterEvent to signal the shortcutted position of the button when hovered by the mouse.
        
        Allows the user to preview the split shortcut without needing to click and lock.
        
        Args:
            event (PyQt event)
        """
        self.hovered_xy.emit(self.x, self.y)
        pass

    def leaveEvent(self, event):
        """event: Override leaveEvent to pass when mouse leaves area of the button."""
        pass

    def on_clicked(self):
        """Signal the shortcutted position of the button when clicked."""
        self.clicked_xy.emit(self.x, self.y)



class SplitViewManager(QtWidgets.QWidget):
    """Interface for shortcut buttons to position and lock the split in a sliding overlay.

    Instantiate without input. See Butterfly Viewer for implementation.
    
    Features:
        Button to lock and unlock the split of a sliding overlay. 
        Arrow buttons position the split to shortcut parts of the image (center, top-right, bottom-left, etc.).
    """

    hovered_xy = QtCore.pyqtSignal(float,float)
    clicked_xy = QtCore.pyqtSignal(float,float)
    lock_split_locked   = QtCore.pyqtSignal()
    lock_split_unlocked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()

        self.lock_split_pushbutton = QtWidgets.QToolButton()
        self.lock_split_pushbutton.setText("Lock Overlay (Shift·X)")
        self.lock_split_pushbutton.setToolTip("Lock the split position of the active sliding overlay")
        self.lock_split_pushbutton.setStyleSheet("""
            QToolButton {
                color: white;
                background-color: rgba(0, 0, 0, 91);
                border-width: 0.06em;
                border-style: solid;
                border-color: white;
                border-radius: 0.13em;
                font-size: 11pt;
            }
            QToolButton:hover {
                background-color: rgba(223, 166, 0, 223);
            }
            QToolButton:pressed {
                color: white;
                background-color: rgba(255, 181, 0, 255);
            }
            QToolButton:checked {
                color: white;
                background-color: rgba(191, 151, 0, 191);
                border-color: rgba(255, 181, 0, 255);
            }
            QToolButton:checked:hover {
                color: white;
                background-color: rgba(223, 166, 0, 223);
                border-color: rgba(255, 181, 0, 255);
            }
            QToolButton:checked:pressed {
                color: white;
                background-color: rgba(255, 181, 0, 255);
                border-color: rgba(255, 181, 0, 255);
            }
            """)
        self.lock_split_pushbutton.setCheckable(True)
        self.lock_split_pushbutton.toggled.connect(self.on_toggle_lock_split_pushbutton)
        lock_split_layout = QtWidgets.QGridLayout()
        lock_split_layout.addWidget(self.lock_split_pushbutton)
        lock_split_widget = QtWidgets.QWidget()
        lock_split_widget.setLayout(lock_split_layout)

        layout_buttons = QtWidgets.QGridLayout()
        layout_buttons.setContentsMargins(0,0,0,0)
        layout_buttons.setSpacing(0)

        layout_buttons.setRowStretch(0,1)
        layout_buttons.setColumnStretch(0,1)

        self.topleft_pushbutton = PushbuttonSplitViewSet(url=r"./icons/arrow-up-left-svgrepo-com.svg", x=0.0, y=0.0)
        self.topleft_pushbutton.setToolTip("Top left of sliding overlay (move and lock)")
        self.topleft_pushbutton.hovered_xy.connect(self.on_hovered_set_pushbutton)
        self.topleft_pushbutton.clicked_xy.connect(self.on_clicked_set_pushbutton)

        self.topcenter_pushbutton = PushbuttonSplitViewSet(url=r"./icons/arrow-up-svgrepo-com.svg", x=0.5, y=0.0)
        self.topcenter_pushbutton.setToolTip("Top center of sliding overlay (move and lock)")
        self.topcenter_pushbutton.hovered_xy.connect(self.on_hovered_set_pushbutton)
        self.topcenter_pushbutton.clicked_xy.connect(self.on_clicked_set_pushbutton)
        
        self.topright_pushbutton = PushbuttonSplitViewSet(url=r"./icons/arrow-up-right-svgrepo-com.svg", x=1.0, y=0.0)
        self.topright_pushbutton.setToolTip("Top right of sliding overlay (move and lock)")
        self.topright_pushbutton.hovered_xy.connect(self.on_hovered_set_pushbutton)
        self.topright_pushbutton.clicked_xy.connect(self.on_clicked_set_pushbutton)
        
        self.middleleft_pushbutton = PushbuttonSplitViewSet(url=r"./icons/arrow-left-svgrepo-com.svg", x=0.0, y=0.5)
        self.middleleft_pushbutton.setToolTip("Middle left of sliding overlay (move and lock)")
        self.middleleft_pushbutton.hovered_xy.connect(self.on_hovered_set_pushbutton)
        self.middleleft_pushbutton.clicked_xy.connect(self.on_clicked_set_pushbutton)
        
        self.middlecenter_pushbutton = PushbuttonSplitViewSet(url=r"./icons/plus-svgrepo-com.svg", x=0.5, y=0.5)
        self.middlecenter_pushbutton.setToolTip("Middle center of sliding overlay (move and lock)")
        self.middlecenter_pushbutton.hovered_xy.connect(self.on_hovered_set_pushbutton)
        self.middlecenter_pushbutton.clicked_xy.connect(self.on_clicked_set_pushbutton)
        
        self.middleright_pushbutton = PushbuttonSplitViewSet(url=r"./icons/arrow-right-svgrepo-com.svg", x=1.0, y=0.5)
        self.middleright_pushbutton.setToolTip("Middle right of sliding overlay (move and lock)")
        self.middleright_pushbutton.hovered_xy.connect(self.on_hovered_set_pushbutton)
        self.middleright_pushbutton.clicked_xy.connect(self.on_clicked_set_pushbutton)
        
        self.bottomleft_pushbutton = PushbuttonSplitViewSet(url=r"./icons/arrow-down-left-svgrepo-com.svg", x=0.0, y=1.0)
        self.bottomleft_pushbutton.setToolTip("Bottom left of sliding overlay (move and lock)")
        self.bottomleft_pushbutton.hovered_xy.connect(self.on_hovered_set_pushbutton)
        self.bottomleft_pushbutton.clicked_xy.connect(self.on_clicked_set_pushbutton)
        
        self.bottomcenter_pushbutton = PushbuttonSplitViewSet(url=r"./icons/arrow-down-svgrepo-com.svg", x=0.5, y=1.0)
        self.bottomcenter_pushbutton.setToolTip("Bottom center of sliding overlay (move and lock)")
        self.bottomcenter_pushbutton.hovered_xy.connect(self.on_hovered_set_pushbutton)
        self.bottomcenter_pushbutton.clicked_xy.connect(self.on_clicked_set_pushbutton)
        
        self.bottomright_pushbutton = PushbuttonSplitViewSet(url=r"./icons/arrow-down-right-svgrepo-com.svg", x=1.0, y=1.0)
        self.bottomright_pushbutton.setToolTip("Bottom right of sliding overlay (move and lock)")
        self.bottomright_pushbutton.hovered_xy.connect(self.on_hovered_set_pushbutton)
        self.bottomright_pushbutton.clicked_xy.connect(self.on_clicked_set_pushbutton)
        

        layout_buttons.addWidget(self.topleft_pushbutton,1,1)
        layout_buttons.addWidget(self.topcenter_pushbutton,1,2)
        layout_buttons.addWidget(self.topright_pushbutton,1,3)
        layout_buttons.addWidget(self.middleleft_pushbutton,2,1)
        layout_buttons.addWidget(self.middlecenter_pushbutton,2,2)
        layout_buttons.addWidget(self.middleright_pushbutton,2,3)
        layout_buttons.addWidget(self.bottomleft_pushbutton,3,1)
        layout_buttons.addWidget(self.bottomcenter_pushbutton,3,2)
        layout_buttons.addWidget(self.bottomright_pushbutton,3,3)

        layout_buttons.setRowStretch(layout_buttons.rowCount(),1)
        layout_buttons.setColumnStretch(layout_buttons.columnCount(),1)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(lock_split_widget, 0, 0)
        layout.addLayout(layout_buttons, 1, 0)

        contents_margins_w = 8
        layout.setContentsMargins(contents_margins_w, 0, contents_margins_w, 0)
        layout.setSpacing(0)
        
        self.setLayout(layout)
        self.setContentsMargins(0,0,0,0)
        
    def on_toggle_lock_split_pushbutton(self, boolean):
        """Signal the locking and unlocking of the split and set the text elements of the lock button.
        
        Triggered when the lock button is toggled on and off (locked and unlocked).
        
        Args:
            boolean (bool): True for locking split; False for unlocking split.
        """
        if boolean:
            text = "Unlock Overlay (Shift·X)"
            tooltip = "Unlock the split position of the active sliding overlay"
            self.lock_split_locked.emit()
        else:
            text = "Lock Overlay (Shift·X)"
            tooltip = "Lock the split position of the active sliding overlay"
            self.lock_split_unlocked.emit()
        self.lock_split_pushbutton.setText(text)
        self.lock_split_pushbutton.setToolTip(tooltip)

    def on_hovered_set_pushbutton(self, x_percent, y_percent): 
        """Signal the position of the split to temporarily move the split.
        
        Triggered when the shortcut arrow buttons are hovered.
        Needed to temporarily signal the moving of the split when the user hovers over a split shortcut button. 

        Args:
            x_percent (float): The position of the split as a proportion (0-1) of the base image's horizontal resolution.
            y_percent (float): The position of the split as a proportion (0-1) of the base image's vertical resolution.
        """
        self.hovered_xy.emit(x_percent, y_percent)
        
    def on_clicked_set_pushbutton(self, x_percent, y_percent):
        """Signal the clicking of the lock button with a given split position.

        Args:
            x_percent (float): The position of the split as a proportion (0-1) of the base image's horizontal resolution.
            y_percent (float): The position of the split as a proportion (0-1) of the base image's vertical resolution.
        """
        self.clicked_xy.emit(x_percent, y_percent)