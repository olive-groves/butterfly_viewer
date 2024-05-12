#!/usr/bin/env python3

"""Image viewing widget for individual images and sliding overlays with sync zoom and pan.

Not intended as a script. Used in Butterfly Viewer and Registrator.

Credits:
    PyQt MDI Image Viewer by tpgit (http://tpgit.github.io/MDIImageViewer/) for sync pan and zoom.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



import sip
import gc
import os
import math
import csv
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets

from aux_viewing import SynchableGraphicsView
from aux_trackers import EventTracker, EventTrackerSplitBypassDeadzone
from aux_functions import strippedName, determineSyncSenderDimension, determineSyncAdjustmentFactor
from aux_labels import FilenameLabel
from aux_scenes import CustomQGraphicsScene
from aux_comments import CommentItem
from aux_rulers import RulerItem



sip.setapi('QDate', 2)
sip.setapi('QTime', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QUrl', 2)
sip.setapi('QTextStream', 2)
sip.setapi('QVariant', 2)
sip.setapi('QString', 2)

    

class SplitView(QtWidgets.QFrame):
    """Image viewing widget for individual images and sliding overlays.

    Creates an interface with a base image as a main image located at the top left  
    and optionally 3 other images (top-left, bottom-left, bottom-right) as a sliding overlay.
    Supports zoom and pan.
    Enables synchronized zoom and pan via signals.
    Input images for a given sliding overlay must have identical resolutions to 
    function properly.
    
    Args:
        pixmap (QPixmap): The main image to be viewed; the basis of the sliding overlay (main; topleft)
        filename_main_topleft (str): The image filepath of the main image.
        name (str): The name of the viewing widget.
        pixmap_topright (QPixmap): The top-right image of the sliding overlay (set None to exclude).
        pixmap_bottomleft (QPixmap): The bottom-left image of the sliding overlay (set None to exclude).
        pixmap_bottomright (QPixmap): The bottom-right image of the sliding overlay (set None to exclude).
    """

    def __init__(self, pixmap_main_topleft=None, filename_main_topleft=None, name=None, 
            pixmap_topright=None, pixmap_bottomleft=None, pixmap_bottomright=None, transform_mode_smooth=False):
        super().__init__()

        self.currentFile = filename_main_topleft

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint) # Clean appearance
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)

        self.viewName = name
        self.comment_position_object = None

        pixmap_main_topleft = self.pixmap_none_ify(pixmap_main_topleft) # Return None if given QPixmap has zero width/height or is not a QPixmap
        pixmap_topright     = self.pixmap_none_ify(pixmap_topright)
        pixmap_bottomleft   = self.pixmap_none_ify(pixmap_bottomleft)
        pixmap_bottomright  = self.pixmap_none_ify(pixmap_bottomright)

        self.pixmap_topright_exists     = (pixmap_topright is not None) # Boolean for existence of pixmap is easier to check
        self.pixmap_bottomright_exists  = (pixmap_bottomright is not None)
        self.pixmap_bottomleft_exists   = (pixmap_bottomleft is not None)

        # Pixmaps which do no exist should be transparent, so they are made into an empty pixmap
        if not self.pixmap_bottomright_exists:
            pixmap_bottomright = QtGui.QPixmap()

        if not self.pixmap_topright_exists:
            pixmap_topright = QtGui.QPixmap()
            
        if not self.pixmap_bottomleft_exists:
            pixmap_bottomleft = QtGui.QPixmap()

        self._zoomFactorDelta = 1.25 # How much zoom for each zoom call

        self.transform_mode_smooth = transform_mode_smooth

        # Sliding overlay is based on the main pixmap view of the top-left pixmap
        # self._scene_main_topleft = QtWidgets.QGraphicsScene()
        self._scene_main_topleft = CustomQGraphicsScene()
        self._view_main_topleft = SynchableGraphicsView(self._scene_main_topleft)

        self._view_main_topleft.setInteractive(True) # Functional settings
        self._view_main_topleft.setViewportUpdateMode(QtWidgets.QGraphicsView.MinimalViewportUpdate)
        self._view_main_topleft.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self._view_main_topleft.setRenderHints(QtGui.QPainter.SmoothPixmapTransform | QtGui.QPainter.Antialiasing)

        self._scene_main_topleft.changed.connect(self.sceneChanged) # Pass along underlying signals
        self._view_main_topleft.transformChanged.connect(self.transformChanged)
        self._view_main_topleft.transformChanged.connect(self.on_transformChanged)
        self._view_main_topleft.scrollChanged.connect(self.scrollChanged)
        self._view_main_topleft.wheelNotches.connect(self.handleWheelNotches)
        self._scene_main_topleft.right_click_comment.connect(self.on_right_click_comment)
        self._scene_main_topleft.right_click_ruler.connect(self.on_right_click_ruler)
        self._scene_main_topleft.right_click_save_all_comments.connect(self.on_right_click_save_all_comments)
        self._scene_main_topleft.right_click_load_comments.connect(self.on_right_click_load_comments)
        self._scene_main_topleft.right_click_relative_origin_position.connect(self.on_right_click_set_relative_origin_position)
        self._scene_main_topleft.changed_px_per_unit.connect(self.on_changed_px_per_unit)
        self._scene_main_topleft.right_click_single_transform_mode_smooth.connect(self.set_transform_mode_smooth)
        self._scene_main_topleft.right_click_all_transform_mode_smooth.connect(self.was_set_global_transform_mode)
        self._scene_main_topleft.right_click_background_color.connect(self.set_scene_background_color)
        self._scene_main_topleft.right_click_background_color.connect(self.was_set_scene_background_color)
        self._scene_main_topleft.right_click_sync_zoom_by.connect(self.was_set_sync_zoom_by)

        self._pixmapItem_main_topleft = QtWidgets.QGraphicsPixmapItem()
        self._scene_main_topleft.addItem(self._pixmapItem_main_topleft)
        
        # A pseudo view directly atop the main view is needed to drive the position of the split and layout of the four pixmaps 
        self._view_layoutdriving_topleft = QtWidgets.QGraphicsView()
        self._view_layoutdriving_topleft.setStyleSheet("border: 0px; border-style: solid; background-color: rgba(0,0,0,0)")
        self._view_layoutdriving_topleft.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._view_layoutdriving_topleft.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view_layoutdriving_topleft.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view_layoutdriving_topleft.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        
        # Add top right pixmap view
        self._pixmapItem_topright = QtWidgets.QGraphicsPixmapItem()
        self.pixmap_topright = pixmap_topright
        
        self._scene_topright = QtWidgets.QGraphicsScene()
        self._scene_topright.addItem(self._pixmapItem_topright)
        
        self._view_topright = QtWidgets.QGraphicsView(self._scene_topright)
        self._view_topright.setStyleSheet("border: 0px; border-style: solid; border-color: rgba(0,0,0,0); background-color: rgba(0,0,0,0);")
        self._view_topright.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._view_topright.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view_topright.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view_topright.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        
        # Add bottom left pixmap view
        self._pixmapItem_bottomleft = QtWidgets.QGraphicsPixmapItem()
        self.pixmap_bottomleft = pixmap_bottomleft
        
        self._scene_bottomleft = QtWidgets.QGraphicsScene()
        self._scene_bottomleft.addItem(self._pixmapItem_bottomleft)
        
        self._view_bottomleft = QtWidgets.QGraphicsView(self._scene_bottomleft)
        self._view_bottomleft.setStyleSheet("border: 0px; border-style: solid; border-color: rgba(0,0,0,0); background-color: rgba(0,0,0,0);")
        self._view_bottomleft.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._view_bottomleft.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view_bottomleft.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view_bottomleft.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        
        # Add bottom right pixmap view
        self._pixmapItem_bottomright = QtWidgets.QGraphicsPixmapItem()
        self.pixmap_bottomright = pixmap_bottomright
        
        self._scene_bottomright = QtWidgets.QGraphicsScene()
        self._scene_bottomright.addItem(self._pixmapItem_bottomright)
        
        self._view_bottomright = QtWidgets.QGraphicsView(self._scene_bottomright)
        self._view_bottomright.setStyleSheet("border: 0px; border-style: solid; border-color: rgba(0,0,0,0); background-color: rgba(0,0,0,0);")
        self._view_bottomright.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._view_bottomright.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view_bottomright.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view_bottomright.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)

         # Make the sizes of the four views entirely dictated by the "layout driving" view
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self._view_main_topleft.setSizePolicy(size_policy)
        self._view_topright.setSizePolicy(size_policy)
        self._view_bottomright.setSizePolicy(size_policy)
        self._view_bottomleft.setSizePolicy(size_policy)

        # By default the split is set to half the widget's size so all pixmap views are equally sized at the start
        self._view_layoutdriving_topleft.setMaximumWidth(self.width()/2.0)
        self._view_layoutdriving_topleft.setMaximumHeight(self.height()/2.0)
        
        if pixmap_main_topleft: # Instantiate transform and resizing
            self.pixmap_main_topleft = pixmap_main_topleft
        
        # SplitView layout
        self._layout = QtWidgets.QGridLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        self.setContentsMargins(0, 0, 0, 0)

        # Labels for the four pixmap views
        self.label_main_topleft = FilenameLabel(visibility_based_on_text=True, belongs_to_split=True)
        self.label_topright     = FilenameLabel(visibility_based_on_text=True, belongs_to_split=True)
        self.label_bottomright  = FilenameLabel(visibility_based_on_text=True, belongs_to_split=True)
        self.label_bottomleft   = FilenameLabel(visibility_based_on_text=True, belongs_to_split=True)

        self.label_main_topleft.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.label_topright.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.label_bottomright.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.label_bottomleft.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        # Pushbutton to close the image window
        self.close_pushbutton = QtWidgets.QPushButton("×")
        self.close_pushbutton.setToolTip("Close image window")
        self.close_pushbutton.clicked.connect(self.was_clicked_close_pushbutton)
        self.close_pushbutton_always_visible = True

        # Create deadzones along the bounds of SplitView to fix the issue of resize handles showing in QMdiArea despite windowless setting.
        # An event tracker "bypass" is needed for each deadzone because they hide the mouse from the sliding overlay, so the mouse must be separately tracked to ensure the split is updated.
        px_deadzone = 8

        self.resize_deadzone_top = QtWidgets.QPushButton("")
        self.resize_deadzone_top.setFixedHeight(px_deadzone)
        self.resize_deadzone_top.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.resize_deadzone_top.setEnabled(False)
        self.resize_deadzone_top.setStyleSheet("""
            QPushButton {
                color: transparent;
                background-color: transparent; 
                border: 0px black;
            }
            """)
        tracker_deadzone_top = EventTrackerSplitBypassDeadzone(self.resize_deadzone_top)
        tracker_deadzone_top.mouse_position_changed_global.connect(self.update_split_given_global)

        self.resize_deadzone_bottom = QtWidgets.QPushButton("")
        self.resize_deadzone_bottom.setFixedHeight(px_deadzone)
        self.resize_deadzone_bottom.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.resize_deadzone_bottom.setEnabled(False)
        self.resize_deadzone_bottom.setStyleSheet("""
            QPushButton {
                color: transparent;
                background-color: transparent; 
                border: 0px black;
            }
            """)
        tracker_deadzone_bottom = EventTrackerSplitBypassDeadzone(self.resize_deadzone_bottom)
        tracker_deadzone_bottom.mouse_position_changed_global.connect(self.update_split_given_global)

        self.resize_deadzone_left = QtWidgets.QPushButton("")
        self.resize_deadzone_left.setFixedWidth(px_deadzone)
        self.resize_deadzone_left.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.resize_deadzone_left.setEnabled(False)
        self.resize_deadzone_left.setStyleSheet("""
            QPushButton {
                color: transparent;
                background-color: transparent; 
                border: 0px black;
            }
            """)
        tracker_deadzone_left = EventTrackerSplitBypassDeadzone(self.resize_deadzone_left)
        tracker_deadzone_left.mouse_position_changed_global.connect(self.update_split_given_global)

        self.resize_deadzone_right = QtWidgets.QPushButton("")
        self.resize_deadzone_right.setFixedWidth(px_deadzone)
        self.resize_deadzone_right.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.resize_deadzone_right.setEnabled(False)
        self.resize_deadzone_right.setStyleSheet("""
            QPushButton {
                color: transparent;
                background-color: transparent; 
                border: 0px black;
            }
            """)
        tracker_deadzone_right = EventTrackerSplitBypassDeadzone(self.resize_deadzone_right)
        tracker_deadzone_right.mouse_position_changed_global.connect(self.update_split_given_global)

        # A frame is placed over the border of the widget to highlight it as the active subwindow in Butterfly Viewer.
        self.frame_hud = QtWidgets.QFrame()
        self.frame_hud.setStyleSheet("border: 0px solid transparent")
        self.frame_hud.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        # Set layout
        self._layout.addWidget(self._view_main_topleft, 0, 0, 2, 2)
        self._layout.addWidget(self._view_layoutdriving_topleft, 0, 0)
        self._layout.addWidget(self._view_topright, 0, 1)
        self._layout.addWidget(self._view_bottomleft, 1, 0)
        self._layout.addWidget(self._view_bottomright, 1, 1)

        self._layout.addWidget(self.resize_deadzone_top, 0, 0, 2, 2, QtCore.Qt.AlignTop)
        self._layout.addWidget(self.resize_deadzone_bottom, 0, 0, 2, 2, QtCore.Qt.AlignBottom)
        self._layout.addWidget(self.resize_deadzone_left, 0, 0, 2, 2, QtCore.Qt.AlignLeft)
        self._layout.addWidget(self.resize_deadzone_right, 0, 0, 2, 2, QtCore.Qt.AlignRight)

        self._layout.addWidget(self.frame_hud, 0, 0, 2, 2)

        self._layout.addWidget(self.label_main_topleft, 0, 0, 2, 2, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self._layout.addWidget(self.label_topright, 0, 0, 2, 2, QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)
        self._layout.addWidget(self.label_bottomright, 0, 0, 2, 2, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        self._layout.addWidget(self.label_bottomleft, 0, 0, 2, 2, QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft)

        self._layout.addWidget(self.close_pushbutton, 0, 0, 2, 2, QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)

        self.setLayout(self._layout)

        self.set_scene_background_color(self._scene_main_topleft.background_color)
        self._view_main_topleft.setStyleSheet("border: 0px; border-style: solid; border-color: red; background-color: rgba(0,0,0,0)")

        # Track the mouse position to know where to set the split
        self.tracker = EventTracker(self)
        self.tracker.mouse_position_changed.connect(self.positionChanged)
        self.tracker.mouse_position_changed.connect(self.on_positionChanged)
        
        # Create a rectangular box the size of one pixel in the main scene to show the user the size and position of the pixel over which their mouse is hovering 
        self.mouse_rect_scene_main_topleft = None
        self.create_mouse_rect()

        # Allow users to lock the split and remember where the split was last set
        self.split_locked = False
        self.last_updated_point_of_split_on_scene_main = QtCore.QPoint()

        self.enableScrollBars(False) # Clean look with no scrollbars

        # Determine zoom adjustment to scale the non-main images now instead
        # on zoom call because the sender and receivers are always the same.
        # TODO: If the photostream feature (next/prev) is to be created, these 
        # adjustment values will need to be recalculated on each new image.
        sync_by = "box"
        sender_width = self._pixmapItem_main_topleft.pixmap().width()
        sender_height = self._pixmapItem_main_topleft.pixmap().height()
        sender_dimension = determineSyncSenderDimension(sender_width,
                                                        sender_height,
                                                        sync_by)

        topright_width = self._pixmapItem_topright.pixmap().width()
        topright_height = self._pixmapItem_topright.pixmap().height()
        self._topright_zoom_adjust = determineSyncAdjustmentFactor(sync_by, sender_dimension,
                                                                  topright_width,
                                                                  topright_height)
        
        bottomright_width = self._pixmapItem_bottomright.pixmap().width()
        bottomright_height = self._pixmapItem_bottomright.pixmap().height()
        self._bottomright_zoom_adjust = determineSyncAdjustmentFactor(sync_by, sender_dimension,
                                                                      bottomright_width,
                                                                      bottomright_height)
        
        bottomleft_width = self._pixmapItem_bottomleft.pixmap().width()
        bottomleft_height = self._pixmapItem_bottomleft.pixmap().height()
        self._bottomleft_zoom_adjust = determineSyncAdjustmentFactor(sync_by, sender_dimension,
                                                                     bottomleft_width,
                                                                     bottomleft_height)

    @property
    def currentFile(self):
        """str: Filepath of base image (filename_main_topleft)."""
        return self._currentFile

    @currentFile.setter
    def currentFile(self, filename_main_topleft):
        self._currentFile = QtCore.QFileInfo(filename_main_topleft).canonicalFilePath()
        self._isUntitled = False
        self.setWindowTitle(self.userFriendlyCurrentFile)

    @property
    def userFriendlyCurrentFile(self):
        """str: Filename of base image."""
        if self.currentFile:
            return strippedName(self.currentFile)
        else:
            return ""
    
    def set_close_pushbutton_always_visible(self, boolean):
        """Enable/disable the always-on visiblilty of the close X of the view.
        
        Arg:
            boolean (bool): True to show the close X always; False to hide unless mouse hovers over.
        """
        self.close_pushbutton_always_visible = boolean
        self.refresh_close_pushbutton_stylesheet()
            
    def refresh_close_pushbutton_stylesheet(self):
        """Refresh stylesheet of close pushbutton based on background color and visibility."""
        if not self.close_pushbutton:
            return
        always_visible = self.close_pushbutton_always_visible
        background_rgb =  self._scene_main_topleft.background_rgb
        avg_background_rgb = sum(background_rgb)/len(background_rgb)
        if not always_visible: # Hide unless hovered
            self.close_pushbutton.setStyleSheet("""
                QPushButton {
                    width: 1.8em;
                    height: 1.8em;
                    color: transparent;
                    background-color: rgba(223, 0, 0, 0); 
                    font-weight: bold;
                    border-width: 0px;
                    border-style: solid;
                    border-color: transparent;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    color: white;
                    background-color: rgba(223, 0, 0, 223);
                }
                QPushButton:pressed {
                    color: white;
                    background-color: rgba(255, 0, 0, 255);
                }
                """)
        else: # Always visible
            if avg_background_rgb >= 223: # Unhovered is black X on light background
                self.close_pushbutton.setStyleSheet("""
                    QPushButton {
                        width: 1.8em;
                        height: 1.8em;
                        color: black;
                        background-color: rgba(223, 0, 0, 0); 
                        font-weight: bold;
                        border-width: 0px;
                        border-style: solid;
                        border-color: transparent;
                        font-size: 10pt;
                    }
                    QPushButton:hover {
                        color: white;
                        background-color: rgba(223, 0, 0, 223);
                    }
                    QPushButton:pressed {
                        color: white;
                        background-color: rgba(255, 0, 0, 255);
                    }
                    """)
            else: # Unhovered is white X on dark background
                self.close_pushbutton.setStyleSheet("""
                    QPushButton {
                        width: 1.8em;
                        height: 1.8em;
                        color: white;
                        background-color: rgba(223, 0, 0, 0); 
                        font-weight: bold;
                        border-width: 0px;
                        border-style: solid;
                        border-color: transparent;
                        font-size: 10pt;
                    }
                    QPushButton:hover {
                        color: white;
                        background-color: rgba(223, 0, 0, 223);
                    }
                    QPushButton:pressed {
                        color: white;
                        background-color: rgba(255, 0, 0, 255);
                    }
                    """)
            
        
    def set_scene_background(self, brush):
        """Set scene background color with QBrush.
        
        Args:
            brush (QBrush)
        """
        if not self._scene_main_topleft:
            return
        self._scene_main_topleft.setBackgroundBrush(brush)

    def set_scene_background_color(self, color: list):
        """Set scene background color with color list.

        The init for CustomQGraphicsScene contains the ground truth for selectable background colors.
        
        Args:
            color (list): Descriptor string and RGB int values. Example: ["White", 255, 255, 255].
        """
        if not self._scene_main_topleft:
            return
        rgb = color[1:4]
        rgb_clamp = [max(min(channel, 255), 0) for channel in rgb]
        brush = QtGui.QColor(rgb_clamp[0], rgb_clamp[1], rgb_clamp[2])
        self.set_scene_background(brush)
        self._scene_main_topleft.background_color = color
        self.refresh_close_pushbutton_stylesheet()

    def update_sync_zoom_by(self, by: str):
        """[str] Update right-click menu of sync zoom by."""
        self._scene_main_topleft.sync_zoom_by = by
    
    def pixmap_none_ify(self, pixmap):
        """Return None if pixmap has no pixels.
        
        Args:
            pixmap (QPixmap)

        Returns:
            None if pixmap has no pixels; same pixmap if it has pixels
        """
        if pixmap:
            if pixmap.width()==0 or pixmap.height==0:
                return None
            else:
                return pixmap
        else:
            return None
    
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_positionChanged(self, pos):
        """Update the position of the split and the 1x1 pixel rectangle.

        Triggered when mouse is moved.
        
        Args:
            pos (QPoint): The position of the mouse relative to widget.
        """
        point_of_mouse_on_widget = pos
        
        self.update_split(point_of_mouse_on_widget)
        self.update_mouse_rect(point_of_mouse_on_widget)

    def set_split(self, x_percent=0.5, y_percent=0.5, ignore_lock=False, percent_of_visible=False):
        """Set the position of the split with x and y as proportion of base image's resolution.

        Sets split position using a proportion of x and y (by default of entire main pixmap; can be set to proportion of visible pixmap).
        Top left is x=0, y=0; bottom right is x=1, y=1.
        This is needed to position the split without mouse movement from user (for example, to preview the effect of the transparency sliders in Butterfly Viewer)
        
        Args:
            x_percent (float): The position of the split as a proportion (0-1) of the base image's horizontal resolution.
            y_percent (float): The position of the split as a proportion (0-1) of the base image's vertical resolution.
            ignore_lock (bool): True to ignore the lock status of the split; False to adhere.
            percent_of_visible (bool): True to set split as proportion of visible area; False as proportion of the full image resolution.
        """
        if percent_of_visible:
            x = x_percent*self.width()
            y = y_percent*self.height()
            point_of_split_on_widget = QtCore.QPoint(x, y)
        else:
            width_pixmap_main_topleft = self.imageWidth
            height_pixmap_main_topleft = self.imageHeight

            x = x_percent*width_pixmap_main_topleft
            y = y_percent*height_pixmap_main_topleft

            point_of_split_on_scene = QtCore.QPointF(x,y)

            point_of_split_on_widget = self._view_main_topleft.mapFromScene(point_of_split_on_scene)

        self.update_split(point_of_split_on_widget, ignore_lock=ignore_lock)
        
    def update_split(self, pos = None, pos_is_global=False, ignore_lock=False): 
        """Update the position of the split with mouse position.
        
        Args:
            pos (QPoint): Position of the mouse.
            pos_is_global (bool): True if given mouse position is relative to MdiChild; False if global position.
            ignore_lock (bool): True to ignore (bypass) the status of the split lock.
        """
        if pos is None: # Get position of the split from the mouse's global coordinates (can be slow!)
            point_of_cursor_global      = QtGui.QCursor.pos()
            point_of_mouse_on_widget    = self._view_main_topleft.mapFromGlobal(point_of_cursor_global)
        else:
            if pos_is_global:
                point_of_mouse_on_widget = self._view_main_topleft.mapFromGlobal(pos)
            else:
                point_of_mouse_on_widget = pos

        point_of_mouse_on_widget.setX(point_of_mouse_on_widget.x()+1) # Offset +1 needed to have mouse cursor be hovering over the main scene (e.g., to allow manipulation of graphics item)
        point_of_mouse_on_widget.setY(point_of_mouse_on_widget.y()+1)

        self.last_updated_point_of_split_on_scene_main = self._view_main_topleft.mapToScene(point_of_mouse_on_widget.x(), point_of_mouse_on_widget.y())
        
        point_of_bottom_right_on_widget = QtCore.QPointF(self.width(), self.height())
        
        point_of_widget_origin_on_scene_main = self._view_main_topleft.mapToScene(0,0)

        point_of_split_on_scene_main = self._view_main_topleft.mapToScene(max(point_of_mouse_on_widget.x(),0),max(point_of_mouse_on_widget.y(),0))
        point_of_bottom_right_on_scene_main = self._view_main_topleft.mapToScene(point_of_bottom_right_on_widget.x(), point_of_bottom_right_on_widget.y())
        
        self._view_layoutdriving_topleft.setMaximumWidth(max(point_of_mouse_on_widget.x(),0))
        self._view_layoutdriving_topleft.setMaximumHeight(max(point_of_mouse_on_widget.y(),0))
        
        render_buffer = 100 # Needed to prevent slight pixel offset of the sliding overlays when zoomed-out below ~0.5x

        scale_topright = 1/self._topright_zoom_adjust  # Needed to scale images to the same relative size as the main image
        scale_bottomright = 1/self._bottomright_zoom_adjust
        scale_bottomleft = 1/self._bottomleft_zoom_adjust
    
        top_left_of_scene_topright          = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_topright, point_of_widget_origin_on_scene_main.y()*scale_topright)
        bottom_right_of_scene_topright      = QtCore.QPointF(point_of_bottom_right_on_scene_main.x()*scale_topright + render_buffer, point_of_split_on_scene_main.y()*scale_topright + render_buffer)
        
        top_left_of_scene_bottomright       = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_bottomright, point_of_split_on_scene_main.y()*scale_bottomright)
        bottom_right_of_scene_bottomright   = QtCore.QPointF(point_of_bottom_right_on_scene_main.x()*scale_bottomright + render_buffer, point_of_bottom_right_on_scene_main.y()*scale_bottomright + render_buffer)
        
        top_left_of_scene_bottomleft        = QtCore.QPointF(point_of_widget_origin_on_scene_main.x()*scale_bottomleft, point_of_split_on_scene_main.y()*scale_bottomleft)
        bottom_right_of_scene_bottomleft    = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_bottomleft + render_buffer, point_of_bottom_right_on_scene_main.y()*scale_bottomleft + render_buffer)
        
        rect_of_scene_topright = QtCore.QRectF(top_left_of_scene_topright, bottom_right_of_scene_topright)
        rect_of_scene_bottomright = QtCore.QRectF(top_left_of_scene_bottomright, bottom_right_of_scene_bottomright)
        rect_of_scene_bottomleft = QtCore.QRectF(top_left_of_scene_bottomleft, bottom_right_of_scene_bottomleft)
        
        self._view_topright.setSceneRect(rect_of_scene_topright)
        self._view_bottomright.setSceneRect(rect_of_scene_bottomright)
        self._view_bottomleft.setSceneRect(rect_of_scene_bottomleft)
        
        self._view_topright.centerOn(top_left_of_scene_topright)
        self._view_bottomright.centerOn(top_left_of_scene_bottomright)
        self._view_bottomleft.centerOn(top_left_of_scene_bottomleft)

    def refresh_split_based_on_last_updated_point_of_split_on_scene_main(self): 
        """Refresh the position of the split using the previously recorded split location.
        
        This is needed to maintain the position of the split during synchronized zooming and panning.
        """ 
        point_of_mouse_on_widget = self._view_main_topleft.mapFromScene(self.last_updated_point_of_split_on_scene_main)
        
        point_of_bottom_right_on_widget = QtCore.QPointF(self.width(), self.height())
        
        point_of_widget_origin_on_scene_main = self._view_main_topleft.mapToScene(0,0)
        point_of_split_on_scene_main = self._view_main_topleft.mapToScene(max(point_of_mouse_on_widget.x(),0),max(point_of_mouse_on_widget.y(),0))
        point_of_bottom_right_on_scene_main = self._view_main_topleft.mapToScene(point_of_bottom_right_on_widget.x(), point_of_bottom_right_on_widget.y())

        self._view_layoutdriving_topleft.setMaximumWidth(max(point_of_mouse_on_widget.x(),0))
        self._view_layoutdriving_topleft.setMaximumHeight(max(point_of_mouse_on_widget.y(),0))
        
        render_buffer = 100 # Needed to prevent slight pixel offset of the sliding overlays when zoomed-out below ~0.5x

        scale_topright = 1/self._topright_zoom_adjust  # Needed to scale images to the same relative size as the main image
        scale_bottomright = 1/self._bottomright_zoom_adjust
        scale_bottomleft = 1/self._bottomleft_zoom_adjust
    
        top_left_of_scene_topright          = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_topright, point_of_widget_origin_on_scene_main.y()*scale_topright)
        bottom_right_of_scene_topright      = QtCore.QPointF(point_of_bottom_right_on_scene_main.x()*scale_topright + render_buffer, point_of_split_on_scene_main.y()*scale_topright + render_buffer)
        
        top_left_of_scene_bottomright       = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_bottomright, point_of_split_on_scene_main.y()*scale_bottomright)
        bottom_right_of_scene_bottomright   = QtCore.QPointF(point_of_bottom_right_on_scene_main.x()*scale_bottomright + render_buffer, point_of_bottom_right_on_scene_main.y()*scale_bottomright + render_buffer)
        
        top_left_of_scene_bottomleft        = QtCore.QPointF(point_of_widget_origin_on_scene_main.x()*scale_bottomleft, point_of_split_on_scene_main.y()*scale_bottomleft)
        bottom_right_of_scene_bottomleft    = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_bottomleft + render_buffer, point_of_bottom_right_on_scene_main.y()*scale_bottomleft + render_buffer)
        
        rect_of_scene_topright = QtCore.QRectF(top_left_of_scene_topright, bottom_right_of_scene_topright)
        rect_of_scene_bottomright = QtCore.QRectF(top_left_of_scene_bottomright, bottom_right_of_scene_bottomright)
        rect_of_scene_bottomleft = QtCore.QRectF(top_left_of_scene_bottomleft, bottom_right_of_scene_bottomleft)
        
        self._view_topright.setSceneRect(rect_of_scene_topright)
        self._view_bottomright.setSceneRect(rect_of_scene_bottomright)
        self._view_bottomleft.setSceneRect(rect_of_scene_bottomleft)
        
        self._view_topright.centerOn(top_left_of_scene_topright)
        self._view_bottomright.centerOn(top_left_of_scene_bottomright)
        self._view_bottomleft.centerOn(top_left_of_scene_bottomleft)
    
    def update_split_given_global(self, pos_global):
        """Update the position of the split based on given global mouse position.

        Convenience function.

        Args:
            pos_global (QPoint): The position of the mouse in global coordinates.
        """
        self.update_split(pos = pos_global, pos_is_global=True)


    def on_right_click_comment(self, scene_pos):
        """Create an editable and movable comment on the scene of the main view at the given scene position.

        Args:
            pos (QPointF): position of the comment datum on the scene.
        """
        pos_on_scene = scene_pos
        self._scene_main_topleft.addItem(CommentItem(initial_scene_pos=pos_on_scene, set_cursor_on_creation=True))

    def on_right_click_ruler(self, scene_pos, relative_origin_position, unit="px", px_per_unit=1.0, update_px_per_unit_on_existing=False):
        """Create a movable ruler on the scene of the main view at the given scene position.

        Args:
            scene_pos (QPointF): The position of the ruler center on the scene.
            relative_origin_position (str): The position of the origin for coordinate system ("topleft" or "bottomleft").
            unit (str): The text for labeling units of ruler values.
            px_per_unit (float): The conversion for pixels to units. For example, 10 means 10 pixels-per-unit, meaning the ruler value will show 1 when measuring 10 pixels.
            update_px_per_unit_on_existing (bool): False always. (Legacy from past versions; future work should remove.
        """
        placement_factor = 1/3
        px_per_unit = px_per_unit
        relative_origin_position = relative_origin_position

        widget_width = self.width()
        widget_height = self.height()

        pos_p1 = self._view_main_topleft.mapToScene(widget_width*placement_factor, widget_height*placement_factor)
        pos_p2 = self._view_main_topleft.mapToScene(widget_width*(1-placement_factor), widget_height*(1-placement_factor))
        self._scene_main_topleft.addItem(RulerItem(unit=unit, px_per_unit=px_per_unit, initial_pos_p1=pos_p1, initial_pos_p2=pos_p2, relative_origin_position=relative_origin_position))

    def on_changed_px_per_unit(self, unit, px_per_unit):
        """Update the units and pixel-per-unit conversions of all rulers in main scene.

        Args:
            unit (str): The text for labeling units of ruler values.
            px_per_unit (float): The conversion for pixels to units. For example, 10 means 10 pixels-per-unit, meaning the ruler value will show 1 when measuring 10 pixels.
        """
        for item in self._scene_main_topleft.items():
            if isinstance(item, RulerItem):
                if item.unit == unit:
                    item.set_and_refresh_px_per_unit(px_per_unit)

    def on_right_click_save_all_comments(self):
        """Open a dialog window for user to save all existing comments on the main scene to .csv.
        
        Triggered from right-click menu on view.
        """
        self.display_loading_grayout(True, "Selecting folder and name for saving all comments in current view...", pseudo_load_time=0)

        style = []
        x = []
        y = []
        color = []
        string = []
        i = -1
        for item in self._scene_main_topleft.items():
            
            if isinstance(item, CommentItem):
                i += 1
                
                comment_pos = item.get_scene_pos()
                comment_color = item.get_color()
                comment_string = item.get_comment_text_str()

                style.append("plain text")
                x.append(comment_pos.x())
                y.append(comment_pos.y())
                color.append(comment_color)
                string.append(comment_string)


        folderpath = None
        filepath_mainview = self.currentFile

        if filepath_mainview:
            folderpath = filepath_mainview
            folderpath = os.path.dirname(folderpath)
            folderpath = folderpath + "\\"
        else:
            self.display_loading_grayout(False, pseudo_load_time=0)
            return
        
        header = [["Butterfly Viewer"],
                  ["1.0"],
                  ["comments"],
                  ["no details"],
                  ["origin"],
                  [os.path.basename(filepath_mainview)],
                  ["Style", "Image x", "Image y", "Appearance", "String"]]

        date_and_time = datetime.now().strftime('%Y-%m-%d %H%M%S') # Sets the default filename with date and time 
        filename = "Untitled comments" + " - " + os.path.basename(filepath_mainview).split('.')[0] + " - " + date_and_time + ".csv"
        name_filters = "CSV (*.csv)" # Allows users to select filetype of screenshot
        
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save all comments of current view to .csv", folderpath+filename, name_filters)

        if filepath:
            self.display_loading_grayout(True, "Saving all comments of current view to .csv...")

            with open(filepath, "w", newline='') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter="|")
                for row in header:
                    csv_writer.writerow(row)
                for row in zip(style, x, y, color, string):
                    csv_writer.writerow(row)

        self.display_loading_grayout(False)


    def on_right_click_load_comments(self):
        """Open a dialog window for user to load comments to the main scene via .csv as saved previously.
        
        Triggered from right-click menu on view.
        """
        self.display_loading_grayout(True, "Selecting comment file (.csv) to load into current view...", pseudo_load_time=0)

        folderpath = None
        filepath_mainview = self.currentFile

        if filepath_mainview:
            folderpath = filepath_mainview
            folderpath = os.path.dirname(folderpath)
            # folderpath = folderpath + "\\"
        else:
            self.display_loading_grayout(False, pseudo_load_time=0)
            return

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select comment file (.csv) to load into current view", folderpath, "Comma-Separated Value File (*.csv)")

        if filename:
            self.display_loading_grayout(True, "Loading comments from selected .csv into current view...")

            with open(filename, "r", newline='') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter="|")
                csv_list = list(csv_reader)

                i = None

                try:
                    i = csv_list.index(["Style", "Image x", "Image y", "Appearance", "String"])
                except ValueError:
                    box_type = QtWidgets.QMessageBox.Warning
                    title = "Invalid .csv comment file"
                    text = "The selected .csv comment file does not have a format accepted by this app."
                    box_buttons = QtWidgets.QMessageBox.Close
                    box = QtWidgets.QMessageBox(box_type, title, text, box_buttons)
                    box.exec_()
                else:
                    i += 1 # Move to first comment item
                    no_comments = True
                    for row in csv_list[i:]:
                        if row[0] == "plain text":
                            no_comments = False
                            comment_x = float(row[1])
                            comment_y = float(row[2])
                            comment_color = row[3]
                            comment_string = row[4]
                            comment_pos = QtCore.QPointF(comment_x, comment_y)
                            self._scene_main_topleft.addItem(CommentItem(initial_scene_pos=comment_pos, color=comment_color, comment_text=comment_string, set_cursor_on_creation=False))
                    if no_comments:
                        box_type = QtWidgets.QMessageBox.Warning
                        title = "No comments in .csv"
                        text = "No comments found in the selected .csv comment file."
                        box_buttons = QtWidgets.QMessageBox.Close
                        box = QtWidgets.QMessageBox(box_type, title, text, box_buttons)
                        box.exec_()
                    
        self.display_loading_grayout(False)

    def on_right_click_set_relative_origin_position(self, string):
        """Set orientation of the coordinate system for rulers by positioning the relative origin.

        Allows users to switch the coordinate orientation:
            "bottomleft" for Cartesian-style (positive X right, positive Y up)
            topleft" for image-style (positive X right, positive Y down)

        Args:
            relative_origin_position (str): The position of the origin for coordinate system ("topleft" or "bottomleft").
        """
        for item in self._scene_main_topleft.items():
            if isinstance(item, RulerItem):
                item.set_and_refresh_relative_origin_position(string)

    def display_loading_grayout(self, boolean, text="Loading...", pseudo_load_time=0.2):
        """Emit signal for showing/hiding a grayout screen to indicate loading sequences.

        Args:
            boolean (bool): True to show grayout; False to hide.
            text (str): The text to show on the grayout.
            pseudo_load_time (float): The delay (in seconds) to hide the grayout to give user feeling of action.
        """ 
        self.signal_display_loading_grayout.emit(boolean, text, pseudo_load_time)
        
    def update_mouse_rect(self, pos = None):
        """Update the position of red 1x1 outline at the pointer in the main scene.

        Args:
            pos (QPoint): The position of the mouse on the widget. Set to None to make the function determine the position using the mouse global coordinates.
        """
        if not self.mouse_rect_scene_main_topleft:
            return
    
        if pos is None: # Get position of split on main scene by directly pulling mouse global coordinates
            point_of_cursor_global      = QtGui.QCursor.pos()
            point_of_mouse_on_widget    = self._view_main_topleft.mapFromGlobal(QtGui.QCursor.pos())
        else:
            point_of_mouse_on_widget = pos
    
        mouse_rect_pos_origin = self._view_main_topleft.mapToScene(point_of_mouse_on_widget.x(),point_of_mouse_on_widget.y())
        mouse_rect_pos_origin.setX(math.floor(mouse_rect_pos_origin.x() - self.mouse_rect_width + 1))
        mouse_rect_pos_origin.setY(math.floor(mouse_rect_pos_origin.y() - self.mouse_rect_height + 1))
        
        self.mouse_rect_scene_main_topleft.setPos(mouse_rect_pos_origin.x(), mouse_rect_pos_origin.y())
    
    # Signals
    signal_display_loading_grayout = QtCore.pyqtSignal(bool, str, float)
    """Emitted when comments are being saved or loaded."""

    became_closed = QtCore.pyqtSignal()
    """Emitted when SplitView is closed."""

    was_clicked_close_pushbutton = QtCore.pyqtSignal()
    """Emitted when close pushbutton is clicked (pressed+released)."""

    was_set_global_transform_mode = QtCore.pyqtSignal(bool)
    """Emitted when transform mode is set for all views in right-click menu (passes it along)."""

    was_set_scene_background_color = QtCore.pyqtSignal(list)
    """Emitted when background color is set in right-click menu (passes it along)."""

    was_set_sync_zoom_by = QtCore.pyqtSignal(str)
    """Emitted when sync zoom option is set in right-click menu (passes it along)."""

    positionChanged = QtCore.pyqtSignal(QtCore.QPoint)
    """Emitted when mouse changes position."""

    sceneChanged = QtCore.pyqtSignal('QList<QRectF>')
    """Scene Changed **Signal**.

    Emitted whenever the |QGraphicsScene| content changes."""
    
    transformChanged = QtCore.pyqtSignal()
    """Transformed Changed **Signal**.

    Emitted whenever the |QGraphicsView| Transform matrix has been changed."""

    scrollChanged = QtCore.pyqtSignal()
    """Scroll Changed **Signal**.

    Emitted whenever the scrollbar position or range has changed."""

    def connectSbarSignals(self, slot):
        """Connect to scrollbar changed signals.

        :param slot: slot to connect scrollbar signals to."""
        self._view_main_topleft.connectSbarSignals(slot)

    def disconnectSbarSignals(self):
        self._view_main_topleft.disconnectSbarSignals()

    @property
    def pixmap_main_topleft(self):
        """The currently viewed |QPixmap| (*QPixmap*)."""
        return self._pixmapItem_main_topleft.pixmap()

    @pixmap_main_topleft.setter
    def pixmap_main_topleft(self, pixmap_main_topleft):
        if pixmap_main_topleft is not None:
            self._pixmapItem_main_topleft.setPixmap(pixmap_main_topleft)
            self._pixmapItem_main_topleft.setTransformationMode(QtCore.Qt.SmoothTransformation)
            self._pixmap_base_original = pixmap_main_topleft
            self.set_opacity_base(100)

    @QtCore.pyqtSlot()
    def set_opacity_base(self, percent):
        """Set transparency of base image.
        
        Args:
            percent (float,int): The transparency as percent opacity, where 100 is opaque (not transparent) and 0 is transparent (0-100).
        """
        
        self._opacity_base = percent

        pixmap_to_be_transparent = QtGui.QPixmap(self._pixmap_base_original.size())
        pixmap_to_be_transparent.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap_to_be_transparent)
        painter.setOpacity(percent/100)
        painter.drawPixmap(QtCore.QPoint(), self._pixmap_base_original)
        painter.end()

        self._pixmapItem_main_topleft.setPixmap(pixmap_to_be_transparent)
    
    @property
    def pixmap_topright(self):
        """The currently viewed QPixmap of the top-right of the split."""
        return self._pixmapItem_topright.pixmap()
    
    @pixmap_topright.setter
    def pixmap_topright(self, pixmap):
        self._pixmap_topright_original = pixmap
        self.set_opacity_topright(100)
    
    @QtCore.pyqtSlot()
    def set_opacity_topright(self, percent):
        """Set transparency of top-right of sliding overlay.
        
        Allows users to see base image underneath.
        Provide enhanced integration and comparison of images (for example, blending raking light with color).

        Args:
            percent (float,int): The transparency as percent opacity, where 100 is opaque (not transparent) and 0 is transparent (0-100).
        """
        if not self.pixmap_topright_exists:
            self._opacity_topright = 100
            return
        
        self._opacity_topright = percent

        pixmap_to_be_transparent = QtGui.QPixmap(self._pixmap_topright_original.size())
        pixmap_to_be_transparent.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap_to_be_transparent)
        painter.setOpacity(percent/100)
        painter.drawPixmap(QtCore.QPoint(), self._pixmap_topright_original)
        painter.end()

        self._pixmapItem_topright.setPixmap(pixmap_to_be_transparent)
    

    @property
    def pixmap_bottomright(self):
        """The currently viewed QPixmap of the bottom-right of the split."""
        return self._pixmapItem_bottomright.pixmap()
    
    @pixmap_bottomright.setter
    def pixmap_bottomright(self, pixmap):
        self._pixmap_bottomright_original = pixmap
        self.set_opacity_bottomright(100)
    
    @QtCore.pyqtSlot()
    def set_opacity_bottomright(self, percent):
        """Set transparency of bottom-right of sliding overlay.

        Args:
            percent (float,int): The transparency as percent opacity, where 100 is opaque (not transparent) and 0 is transparent (0-100).
        """
        if not self.pixmap_bottomright_exists:
            self._opacity_bottomright = 100
            return

        self._opacity_bottomright = percent

        pixmap_to_be_transparent = QtGui.QPixmap(self._pixmap_bottomright_original.size())
        pixmap_to_be_transparent.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap_to_be_transparent)
        painter.setOpacity(percent/100)
        painter.drawPixmap(QtCore.QPoint(), self._pixmap_bottomright_original)
        painter.end()

        self._pixmapItem_bottomright.setPixmap(pixmap_to_be_transparent)
    

    @property
    def pixmap_bottomleft(self):
        """The currently viewed QPixmap of the bottom-left of the split."""
        return self._pixmapItem_bottomleft.pixmap()
    
    @pixmap_bottomleft.setter
    def pixmap_bottomleft(self, pixmap):
        self._pixmap_bottomleft_original = pixmap
        self.set_opacity_bottomleft(100)
    
    @QtCore.pyqtSlot()
    def set_opacity_bottomleft(self, percent):
        """Set transparency of bottom-left of sliding overlay.

        Args:
            percent (float,int): The transparency as percent opacity, where 100 is opaque (not transparent) and 0 is transparent (0-100).
        """
        if not self.pixmap_bottomleft_exists:
            self._opacity_bottomleft = 100
            return

        self._opacity_bottomleft = percent

        pixmap_to_be_transparent = QtGui.QPixmap(self._pixmap_bottomleft_original.size())
        pixmap_to_be_transparent.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap_to_be_transparent)
        painter.setOpacity(percent/100)
        painter.drawPixmap(QtCore.QPoint(), self._pixmap_bottomleft_original)
        painter.end()

        self._pixmapItem_bottomleft.setPixmap(pixmap_to_be_transparent)
    
    def moveEvent(self, event):
        """Override move event of frame."""
        super().moveEvent(event)

    def resizeEvent(self, event):
        """Override resize event of frame to ensure scene is also resized."""
        self.resize_scene()
        super().resizeEvent(event) # Equivalent to QtWidgets.QFrame.resizeEvent(self, event)     
        
    def resize_scene(self):
        """Resize the scene to allow image to be panned just before the main pixmap leaves the viewport.

        This is needed to expand the scene so that users can pan the pixmap such that its edges are at the center of the view.
        This changes the default behavior, which limits the scene to the bounds of the pixmap, thereby blocking users 
        from panning outside the bounds of the pixmap, which can feel abrupt and restrictive.
        This takes care of preventing users from panning too far away from the pixmap. 
        """
        scene_to_viewport_factor = self._view_main_topleft.zoomFactor
        
        width_viewport_window = self.width()
        height_viewport_window = self.height()

        peek_precent = 0.1 # Percent of pixmap to be left "peeking" at bounds of pan
        peek_margin_x = width_viewport_window*peek_precent # [px]
        peek_margin_y = height_viewport_window*peek_precent
        
        width_viewport = (width_viewport_window - peek_margin_x)/scene_to_viewport_factor # This is the size of the viewport on the screen
        height_viewport = (height_viewport_window - peek_margin_y)/scene_to_viewport_factor
        
        width_pixmap = self.imageWidth
        height_pixmap = self.imageHeight
        
        width_scene = 2.0*(width_viewport + width_pixmap/2.0) # The scene spans twice the viewport plus the pixmap
        height_scene = 2.0*(height_viewport + height_pixmap/2.0)
        
        scene_rect = QtCore.QRectF(-width_scene/2.0 + width_pixmap/2.0,-height_scene/2.0 + height_pixmap/2.0,width_scene,height_scene)
        self._scene_main_topleft.setSceneRect(scene_rect)
    
    def set_transform_mode_smooth_on(self):
        """Set transform mode to smooth (interpolate) when zoomfactor is >= 1.0."""
        self.transform_mode_smooth = True
        self._scene_main_topleft.set_single_transform_mode_smooth(True)
        self.refresh_transform_mode()
            
    def set_transform_mode_smooth_off(self):
        """Set transform mode to non-smooth (non-interpolated) when zoomfactor is >= 1.0."""
        self.transform_mode_smooth = False
        self._scene_main_topleft.set_single_transform_mode_smooth(False)
        self.refresh_transform_mode()

    def set_transform_mode_smooth(self, boolean):
        """Set transform mode when zoomfactor is >= 1.0.

        Convenience function.
        
        Args:
            boolean (bool): True to smooth (interpolate); False to fast (not interpolate).
        """
        if boolean:
            self.set_transform_mode_smooth_on()
        elif not boolean:
            self.set_transform_mode_smooth_off()
            
    @QtCore.pyqtSlot()
    def on_transformChanged(self):
        """Resize scene if image transform is changed (for example, when zoomed)."""
        self.resize_scene()
        self.update_split()

    @property
    def viewName(self):
        """str: The name of the SplitView."""
        return self._name
    
    @viewName.setter
    def viewName(self, name):
        self._name = name

    @property
    def handDragging(self):
        """bool: The hand dragging state."""
        return self._view_main_topleft.handDragging

    @property
    def scrollState(self):
        """tuple: The percentage of scene extents
        *(sceneWidthPercent, sceneHeightPercent)*"""
        return self._view_main_topleft.scrollState

    @scrollState.setter
    def scrollState(self, state):
        self._view_main_topleft.scrollState = state

    @property
    def zoomFactor(self):
        """float: The zoom scale factor."""
        return self._view_main_topleft.zoomFactor

    @zoomFactor.setter
    def zoomFactor(self, newZoomFactor):
        """Apply zoom to all views, taking into account the transform mode.
        
        Args:
            newZoomFactor (float)
        """
        self._view_main_topleft.zoomFactor = newZoomFactor

        scale_topright = newZoomFactor * self._topright_zoom_adjust / self._view_topright.transform().m11()
        scale_bottomright = newZoomFactor * self._bottomright_zoom_adjust / self._view_bottomright.transform().m11()
        scale_bottomleft = newZoomFactor * self._bottomleft_zoom_adjust / self._view_bottomleft.transform().m11()

        self._view_topright.scale(scale_topright, scale_topright)
        self._view_bottomright.scale(scale_bottomright, scale_bottomright)
        self._view_bottomleft.scale(scale_bottomleft, scale_bottomleft)

        self.refresh_transform_mode()

    def refresh_transform_mode(self):
        """Refresh zoom of all views, taking into account the transform mode."""
        zoomFactor = self.zoomFactor
        self.set_pixmap_transform_from_scale(self._pixmapItem_main_topleft,
                                            zoomFactor)
        
        scale_topright = self._view_topright.transform().m11()
        scale_bottomright = self._view_bottomright.transform().m11()
        scale_bottomleft = self._view_bottomleft.transform().m11()

        self.set_pixmap_transform_from_scale(self._pixmapItem_topright,
                                            scale_topright)
        self.set_pixmap_transform_from_scale(self._pixmapItem_bottomright,
                                            scale_bottomright)
        self.set_pixmap_transform_from_scale(self._pixmapItem_bottomleft,
                                            scale_bottomleft)

    def set_pixmap_transform_from_scale(self, pixmap_item, scale, limit: float = 1.0):
        """Set a given pixmap transform based on scale (zoom)."""

        if (scale < limit) or (self.transform_mode_smooth):
            pixmap_item.setTransformationMode(QtCore.Qt.SmoothTransformation)
        else:
            pixmap_item.setTransformationMode(QtCore.Qt.FastTransformation)

    @property
    def _horizontalScrollBar(self):
        """Get the SplitView horizontal scrollbar widget (*QScrollBar*).

        (Only used for debugging purposes)"""
        return self._view_main_topleft.horizontalScrollBar()

    @property
    def _verticalScrollBar(self):
        """Get the SplitView vertical scrollbar widget (*QScrollBar*).

        (Only used for debugging purposes)"""
        return self._view_main_topleft.verticalScrollBar()

    @property
    def _sceneRect(self):
        """Get the SplitView sceneRect (*QRectF*).

        (Only used for debugging purposes)"""
        return self._view_main_topleft.sceneRect()

    @QtCore.pyqtSlot()
    def scrollToTop(self):
        """Scroll to top of image."""
        self._view_main_topleft.scrollToTop()

    @QtCore.pyqtSlot()
    def scrollToBottom(self):
        """Scroll to bottom of image."""
        self._view_main_topleft.scrollToBottom()

    @QtCore.pyqtSlot()
    def scrollToBegin(self):
        """Scroll to left side of image."""
        self._view_main_topleft.scrollToBegin()

    @QtCore.pyqtSlot()
    def scrollToEnd(self):
        """Scroll to right side of image."""
        self._view_main_topleft.scrollToEnd()

    @QtCore.pyqtSlot()
    def centerView(self):
        """Center image in view."""
        self._view_main_topleft.centerView()

    @QtCore.pyqtSlot(bool)
    def enableScrollBars(self, enable):
        """Set visiblility of the view's scrollbars.

        :param bool enable: True to enable the scrollbars """
        self._view_main_topleft.enableScrollBars(enable)

    @QtCore.pyqtSlot(bool)
    def enableHandDrag(self, enable):
        """Set whether dragging the view with the hand cursor is allowed.

        :param bool enable: True to enable hand dragging """
        self._view_main_topleft.enableHandDrag(enable)

    @QtCore.pyqtSlot()
    def zoomIn(self):
        """Zoom in on image."""
        self.scaleImage(self._zoomFactorDelta)

    @QtCore.pyqtSlot()
    def zoomOut(self):
        """Zoom out on image."""
        self.scaleImage(1 / self._zoomFactorDelta)

    @QtCore.pyqtSlot()
    def actualSize(self):
        """Change zoom to show image at actual size.

        (image pixel is equal to screen pixel)"""
        self.scaleImage(1.0, combine=False)

    @QtCore.pyqtSlot()
    def fitToWindow(self):
        """Fit image within view.
            
        If the viewport is wider than the main pixmap, then fit the pixmap to height; if the viewport is narrower, then fit the pixmap to width
        """
        if not self._pixmapItem_main_topleft.pixmap():
            return

        padding_margin = 2 # Leaves visual gap between pixmap and border of viewport
        viewport_rect = self._view_main_topleft.viewport().rect().adjusted(padding_margin, padding_margin,
                                                         -padding_margin, -padding_margin)
        aspect_ratio_viewport = viewport_rect.width()/viewport_rect.height()
        aspect_ratio_pixmap   = self.imageWidth/self.imageHeight
        if aspect_ratio_viewport > aspect_ratio_pixmap:
            self.fitHeight()
        else:
            self.fitWidth()

        self.transformChanged.emit()
    
    @QtCore.pyqtSlot()
    def fitWidth(self):
        """Fit image width to view width."""
        if not self._pixmapItem_main_topleft.pixmap():
            return
        padding_margin = 2
        viewRect = self._view_main_topleft.viewport().rect().adjusted(padding_margin, padding_margin,
                                                         -padding_margin, -padding_margin)
        factor = viewRect.width() / self.imageWidth
        self.scaleImage(factor, combine=False)
        self._view_main_topleft.centerView()
    
    @QtCore.pyqtSlot()
    def fitHeight(self):
        """Fit image height to view height."""
        if not self._pixmapItem_main_topleft.pixmap():
            return
        padding_margin = 2
        viewRect = self._view_main_topleft.viewport().rect().adjusted(padding_margin, padding_margin,
                                                         -padding_margin, -padding_margin)
        factor = viewRect.height() / self.imageHeight
        self.scaleImage(factor, combine=False)
        self._view_main_topleft.centerView()

    @property
    def imageWidth(self):
        """int: Width of base (main) image pixmap."""
        return self._pixmapItem_main_topleft.pixmap().width()
    
    @property
    def imageHeight(self):
        """int: Height of base (main) image pixmap."""
        return self._pixmapItem_main_topleft.pixmap().height()

    def handleWheelNotches(self, notches):
        """Handle wheel notch event from underlying |QGraphicsView|.

        :param float notches: Mouse wheel notches"""
        self.scaleImage(self._zoomFactorDelta ** notches)

    def closeEvent(self, event):
        """Overriden in order to disconnect scrollbar signals before
        closing.

        :param QEvent event: instance of a |QEvent|
        
        If this isn't done Python crashes!"""
        #self.scrollChanged.disconnect() #doesn't prevent crash
        self.disconnectSbarSignals()
        
        self._scene_main_topleft.deleteLater()
        self._view_main_topleft.deleteLater()
        del self._pixmap_base_original
        
        self._scene_topright.deleteLater()
        self._view_topright.deleteLater()
        del self._pixmap_topright_original
        
        self._scene_bottomright.deleteLater()
        self._view_bottomright.deleteLater()
        del self._pixmap_bottomright_original
        
        self._scene_bottomleft.deleteLater()
        self._view_bottomleft.deleteLater()
        del self._pixmap_bottomleft_original
        
        super().closeEvent(event)
        gc.collect()
        self.became_closed.emit()
        
    def scaleImage(self, factor, combine=True):
        """Scale image by factor.

        :param float factor: either new :attr:`zoomFactor` or amount to scale
                             current :attr:`zoomFactor`

        :param bool combine: if ``True`` scales the current
                             :attr:`zoomFactor` by factor.  Otherwise
                             just sets :attr:`zoomFactor` to factor"""
        if not self._pixmapItem_main_topleft.pixmap():
            return

        if combine:
            self.zoomFactor = self.zoomFactor * factor
        else:
            self.zoomFactor = factor
            
        self._view_main_topleft.checkTransformChanged()

    def dumpTransform(self):
        """Dump view transform to stdout."""
        self._view_main_topleft.dumpTransform(self._view_main_topleft.transform(), " "*4)
    
    
    def create_mouse_rect(self):
        """Create a red 1x1 outline at the pointer in the main scene.
        
        Indicates to the user the size and position of the pixel over which the mouse is hovering.
        Helps to understand the position of individual pixels and their scale at the current zoom.
        """
    
        pen = QtGui.QPen() 
        pen.setWidth(0.1)
        pen.setColor(QtCore.Qt.red)
        pen.setCapStyle(QtCore.Qt.SquareCap)
        pen.setJoinStyle(QtCore.Qt.MiterJoin)
            
        brush = QtGui.QBrush()
        brush.setColor(QtCore.Qt.transparent)
        
        self.mouse_rect_width = 1
        self.mouse_rect_height = 1
        
        self.mouse_rect_topleft = QtCore.QPointF(0,0)
        self.mouse_rect_bottomright = QtCore.QPointF(self.mouse_rect_width-0.01, self.mouse_rect_height-0.01)
        self.mouse_rect = QtCore.QRectF(self.mouse_rect_topleft, self.mouse_rect_bottomright)
        
        self.mouse_rect_scene_main_topleft = QtWidgets.QGraphicsRectItem(self.mouse_rect) # To add the same item in two scenes, you need to create two unique items
        
        self.mouse_rect_scene_main_topleft.setPos(0,0)
        
        self.mouse_rect_scene_main_topleft.setBrush(brush)
        self.mouse_rect_scene_main_topleft.setPen(pen)
        
        self._scene_main_topleft.addItem(self.mouse_rect_scene_main_topleft)

    def set_mouse_rect_visible(self, boolean):
        """Set the visibilty of the red 1x1 outline at the pointer in the main scene.
        
        Args:
            boolean (bool): True to show 1x1 outline; False to hide.
        """
        self.mouse_rect_scene_main_topleft.setVisible(boolean)