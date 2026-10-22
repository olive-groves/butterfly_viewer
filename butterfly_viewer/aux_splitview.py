#!/usr/bin/env python3

"""Image viewing widget for individual images and sliding overlays with sync zoom and pan.

Not intended as a script. Used in Butterfly Viewer and Registrator.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



import gc
import os
import math
import csv
from datetime import datetime

from PyQt6 import QtCore, QtGui, QtWidgets

from aux_viewing import SynchableGraphicsView
from aux_trackers import EventTracker, EventTrackerSplitBypassDeadzone
from aux_functions import strippedName, determineSyncSenderDimension, determineSyncAdjustmentFactor, setAvailableMemory
from aux_labels import FilenameLabel
from aux_scenes import CustomQGraphicsScene
from aux_comments import CommentItem
from aux_rulers import RulerItem



class SplitView(QtWidgets.QFrame):
    """Image viewing widget for individual images and sliding overlays."""

    def __init__(self, pixmap_main_topleft=None, filename_main_topleft=None, name=None, 
            pixmap_topright=None, pixmap_bottomleft=None, pixmap_bottomright=None, transform_mode_smooth=False):
        super().__init__()

        self.currentFile = filename_main_topleft

        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)

        self.viewName = name
        self.comment_position_object = None

        pixmap_main_topleft = self.pixmap_none_ify(pixmap_main_topleft)
        pixmap_topright     = self.pixmap_none_ify(pixmap_topright)
        pixmap_bottomleft   = self.pixmap_none_ify(pixmap_bottomleft)
        pixmap_bottomright  = self.pixmap_none_ify(pixmap_bottomright)

        self.pixmap_topright_exists     = (pixmap_topright is not None)
        self.pixmap_bottomright_exists  = (pixmap_bottomright is not None)
        self.pixmap_bottomleft_exists   = (pixmap_bottomleft is not None)

        if not self.pixmap_bottomright_exists:
            pixmap_bottomright = QtGui.QPixmap()

        if not self.pixmap_topright_exists:
            pixmap_topright = QtGui.QPixmap()
            
        if not self.pixmap_bottomleft_exists:
            pixmap_bottomleft = QtGui.QPixmap()

        self._zoomFactorDelta = 1.25
        self.transform_mode_smooth = transform_mode_smooth

        self._scene_main_topleft = CustomQGraphicsScene()
        self._view_main_topleft = SynchableGraphicsView(self._scene_main_topleft)

        self._view_main_topleft.setInteractive(True)
        self._view_main_topleft.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self._view_main_topleft.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self._view_main_topleft.setRenderHints(QtGui.QPainter.RenderHint.SmoothPixmapTransform | QtGui.QPainter.RenderHint.Antialiasing)

        self._scene_main_topleft.changed.connect(self.sceneChanged)
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
        
        self._view_layoutdriving_topleft = QtWidgets.QGraphicsView()
        self._view_layoutdriving_topleft.setStyleSheet("border: 0px; border-style: solid; background-color: rgba(0,0,0,0)")
        self._view_layoutdriving_topleft.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._view_layoutdriving_topleft.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_layoutdriving_topleft.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_layoutdriving_topleft.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self._pixmapItem_topright = QtWidgets.QGraphicsPixmapItem()
        self.pixmap_topright = pixmap_topright
        
        self._scene_topright = QtWidgets.QGraphicsScene()
        self._scene_topright.addItem(self._pixmapItem_topright)
        
        self._view_topright = QtWidgets.QGraphicsView(self._scene_topright)
        self._view_topright.setStyleSheet("border: 0px; border-style: solid; border-color: rgba(0,0,0,0); background-color: rgba(0,0,0,0);")
        self._view_topright.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._view_topright.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_topright.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_topright.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
        self._pixmapItem_bottomleft = QtWidgets.QGraphicsPixmapItem()
        self.pixmap_bottomleft = pixmap_bottomleft
        
        self._scene_bottomleft = QtWidgets.QGraphicsScene()
        self._scene_bottomleft.addItem(self._pixmapItem_bottomleft)
        
        self._view_bottomleft = QtWidgets.QGraphicsView(self._scene_bottomleft)
        self._view_bottomleft.setStyleSheet("border: 0px; border-style: solid; border-color: rgba(0,0,0,0); background-color: rgba(0,0,0,0);")
        self._view_bottomleft.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._view_bottomleft.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_bottomleft.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_bottomleft.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
        self._pixmapItem_bottomright = QtWidgets.QGraphicsPixmapItem()
        self.pixmap_bottomright = pixmap_bottomright
        
        self._scene_bottomright = QtWidgets.QGraphicsScene()
        self._scene_bottomright.addItem(self._pixmapItem_bottomright)
        
        self._view_bottomright = QtWidgets.QGraphicsView(self._scene_bottomright)
        self._view_bottomright.setStyleSheet("border: 0px; border-style: solid; border-color: rgba(0,0,0,0); background-color: rgba(0,0,0,0);")
        self._view_bottomright.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._view_bottomright.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_bottomright.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_bottomright.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Ignored)
        self._view_main_topleft.setSizePolicy(size_policy)
        self._view_topright.setSizePolicy(size_policy)
        self._view_bottomright.setSizePolicy(size_policy)
        self._view_bottomleft.setSizePolicy(size_policy)

        # By default the split is set to half the widget's size so all pixmap views are equally sized at the start
        self._view_layoutdriving_topleft.setMaximumWidth(self.width() // 2)
        self._view_layoutdriving_topleft.setMaximumHeight(self.height() // 2)
        
        if pixmap_main_topleft:
            self.pixmap_main_topleft = pixmap_main_topleft
        
        self._layout = QtWidgets.QGridLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        self.setContentsMargins(0, 0, 0, 0)

        self.label_main_topleft = FilenameLabel(visibility_based_on_text=True, belongs_to_split=True, remove_path=False)
        self.label_topright     = FilenameLabel(visibility_based_on_text=True, belongs_to_split=True, remove_path=False)
        self.label_bottomright  = FilenameLabel(visibility_based_on_text=True, belongs_to_split=True, remove_path=False)
        self.label_bottomleft   = FilenameLabel(visibility_based_on_text=True, belongs_to_split=True, remove_path=False)

        self.label_main_topleft.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label_topright.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label_bottomright.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label_bottomleft.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.close_pushbutton = QtWidgets.QPushButton("×")
        self.close_pushbutton.setToolTip("Close image window")
        self.close_pushbutton.clicked.connect(self.was_clicked_close_pushbutton)
        self.close_pushbutton_always_visible = True

        px_deadzone = 8

        self.resize_deadzone_top = QtWidgets.QPushButton("")
        self.resize_deadzone_top.setFixedHeight(px_deadzone)
        self.resize_deadzone_top.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
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
        self.resize_deadzone_bottom.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
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
        self.resize_deadzone_left.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
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
        self.resize_deadzone_right.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
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

        self.frame_hud = QtWidgets.QFrame()
        self.frame_hud.setStyleSheet("border: 0px solid transparent")
        self.frame_hud.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._layout.addWidget(self._view_main_topleft, 0, 0, 2, 2)
        self._layout.addWidget(self._view_layoutdriving_topleft, 0, 0)
        self._layout.addWidget(self._view_topright, 0, 1)
        self._layout.addWidget(self._view_bottomleft, 1, 0)
        self._layout.addWidget(self._view_bottomright, 1, 1)

        self._layout.addWidget(self.resize_deadzone_top, 0, 0, 2, 2, QtCore.Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self.resize_deadzone_bottom, 0, 0, 2, 2, QtCore.Qt.AlignmentFlag.AlignBottom)
        self._layout.addWidget(self.resize_deadzone_left, 0, 0, 2, 2, QtCore.Qt.AlignmentFlag.AlignLeft)
        self._layout.addWidget(self.resize_deadzone_right, 0, 0, 2, 2, QtCore.Qt.AlignmentFlag.AlignRight)

        self._layout.addWidget(self.frame_hud, 0, 0, 2, 2)

        self._layout.addWidget(self.label_main_topleft, 0, 0, 2, 2, QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        self._layout.addWidget(self.label_topright, 0, 0, 2, 2, QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignRight)
        self._layout.addWidget(self.label_bottomright, 0, 0, 2, 2, QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignRight)
        self._layout.addWidget(self.label_bottomleft, 0, 0, 2, 2, QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignLeft)

        self._layout.addWidget(self.close_pushbutton, 0, 0, 2, 2, QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignRight)

        self.setLayout(self._layout)

        self.set_scene_background_color(self._scene_main_topleft.background_color)
        self._view_main_topleft.setStyleSheet("border: 0px; border-style: solid; border-color: red; background-color: rgba(0,0,0,0)")

        self.tracker = EventTracker(self)
        self.tracker.mouse_position_changed.connect(self.positionChanged)
        self.tracker.mouse_position_changed.connect(self.on_positionChanged)
        
        self.mouse_rect_scene_main_topleft = None
        self.create_mouse_rect()

        # Allow users to lock the split and remember where the split was last set
        self.split_locked = False
        self.last_updated_point_of_split_on_scene_main = QtCore.QPointF()

        self.enableScrollBars(False)

        sync_by = "box"
        sender_width = self._pixmapItem_main_topleft.pixmap().width()
        sender_height = self._pixmapItem_main_topleft.pixmap().height()
        sender_dimension = determineSyncSenderDimension(sender_width, sender_height, sync_by)

        topright_width = self._pixmapItem_topright.pixmap().width()
        topright_height = self._pixmapItem_topright.pixmap().height()
        self._topright_zoom_adjust = determineSyncAdjustmentFactor(sync_by, sender_dimension,
                                                                  topright_width, topright_height)
        
        bottomright_width = self._pixmapItem_bottomright.pixmap().width()
        bottomright_height = self._pixmapItem_bottomright.pixmap().height()
        self._bottomright_zoom_adjust = determineSyncAdjustmentFactor(sync_by, sender_dimension,
                                                                      bottomright_width, bottomright_height)
        
        bottomleft_width = self._pixmapItem_bottomleft.pixmap().width()
        bottomleft_height = self._pixmapItem_bottomleft.pixmap().height()
        self._bottomleft_zoom_adjust = determineSyncAdjustmentFactor(sync_by, sender_dimension,
                                                                     bottomleft_width, bottomleft_height)

    @property
    def currentFile(self):
        return self._currentFile

    @currentFile.setter
    def currentFile(self, filename_main_topleft):
        self._currentFile = QtCore.QFileInfo(filename_main_topleft).canonicalFilePath()
        self._isUntitled = False
        self.setWindowTitle(self.userFriendlyCurrentFile)

    @property
    def userFriendlyCurrentFile(self):
        if self.currentFile:
            return strippedName(self.currentFile)
        else:
            return ""
    
    def set_close_pushbutton_always_visible(self, boolean):
        self.close_pushbutton_always_visible = boolean
        self.refresh_close_pushbutton_stylesheet()
            
    def refresh_close_pushbutton_stylesheet(self):
        if not self.close_pushbutton:
            return
        always_visible = self.close_pushbutton_always_visible
        background_rgb = self._scene_main_topleft.background_rgb
        avg_background_rgb = sum(background_rgb)/len(background_rgb)
        if not always_visible:
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
        else:
            if avg_background_rgb >= 223:
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
            else:
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
        if not self._scene_main_topleft:
            return
        self._scene_main_topleft.setBackgroundBrush(brush)

    def set_scene_background_color(self, color: list):
        if not self._scene_main_topleft:
            return
        rgb = color[1:4]
        rgb_clamp = [max(min(channel, 255), 0) for channel in rgb]
        brush = QtGui.QColor(rgb_clamp[0], rgb_clamp[1], rgb_clamp[2])
        self.set_scene_background(brush)
        self._scene_main_topleft.background_color = color
        self.refresh_close_pushbutton_stylesheet()

    def update_sync_zoom_by(self, by: str):
        self._scene_main_topleft.sync_zoom_by = by
    
    def pixmap_none_ify(self, pixmap):
        if pixmap:
            if pixmap.width()==0 or pixmap.height()==0:
                return None
            else:
                return pixmap
        else:
            return None
    
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_positionChanged(self, pos):
        point_of_mouse_on_widget = pos
        self.update_split(point_of_mouse_on_widget)
        self.update_mouse_rect(point_of_mouse_on_widget)

    def set_split(self, x_percent=0.5, y_percent=0.5, ignore_lock=False, percent_of_visible=False):
        if percent_of_visible:
            x = x_percent*self.width()
            y = y_percent*self.height()
            point_of_split_on_widget = QtCore.QPoint(int(x), int(y))
        else:
            width_pixmap_main_topleft = self.imageWidth
            height_pixmap_main_topleft = self.imageHeight

            x = x_percent*width_pixmap_main_topleft
            y = y_percent*height_pixmap_main_topleft

            point_of_split_on_scene = QtCore.QPointF(x,y)
            point_of_split_on_widget = self._view_main_topleft.mapFromScene(point_of_split_on_scene)

        self.update_split(point_of_split_on_widget, ignore_lock=ignore_lock)
        
    def update_split(self, pos = None, pos_is_global=False, ignore_lock=False): 
        if pos is None:
            point_of_cursor_global = QtGui.QCursor.pos()
            point_of_mouse_on_widget = self._view_main_topleft.mapFromGlobal(point_of_cursor_global)
        else:
            if pos_is_global:
                point_of_mouse_on_widget = self._view_main_topleft.mapFromGlobal(pos)
            else:
                point_of_mouse_on_widget = pos

        point_of_mouse_on_widget.setX(point_of_mouse_on_widget.x()+1)
        point_of_mouse_on_widget.setY(point_of_mouse_on_widget.y()+1)

        scene_point = self._view_main_topleft.mapToScene(point_of_mouse_on_widget)
        self.last_updated_point_of_split_on_scene_main = QtCore.QPointF(scene_point)
        
        point_of_bottom_right_on_widget = QtCore.QPointF(self.width(), self.height())
        point_of_widget_origin_on_scene_main = self._view_main_topleft.mapToScene(0,0)

        point_of_split_on_scene_main = self._view_main_topleft.mapToScene(max(point_of_mouse_on_widget.x(),0), max(point_of_mouse_on_widget.y(),0))
        point_of_bottom_right_on_scene_main = self._view_main_topleft.mapToScene(int(point_of_bottom_right_on_widget.x()), int(point_of_bottom_right_on_widget.y()))
        
        self._view_layoutdriving_topleft.setMaximumWidth(max(point_of_mouse_on_widget.x(),0))
        self._view_layoutdriving_topleft.setMaximumHeight(max(point_of_mouse_on_widget.y(),0))
        
        render_buffer = 100

        scale_topright = 1/self._topright_zoom_adjust
        scale_bottomright = 1/self._bottomright_zoom_adjust
        scale_bottomleft = 1/self._bottomleft_zoom_adjust
    
        top_left_of_scene_topright = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_topright, point_of_widget_origin_on_scene_main.y()*scale_topright)
        bottom_right_of_scene_topright = QtCore.QPointF(point_of_bottom_right_on_scene_main.x()*scale_topright + render_buffer, point_of_split_on_scene_main.y()*scale_topright + render_buffer)
        
        top_left_of_scene_bottomright = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_bottomright, point_of_split_on_scene_main.y()*scale_bottomright)
        bottom_right_of_scene_bottomright = QtCore.QPointF(point_of_bottom_right_on_scene_main.x()*scale_bottomright + render_buffer, point_of_bottom_right_on_scene_main.y()*scale_bottomright + render_buffer)
        
        top_left_of_scene_bottomleft = QtCore.QPointF(point_of_widget_origin_on_scene_main.x()*scale_bottomleft, point_of_split_on_scene_main.y()*scale_bottomleft)
        bottom_right_of_scene_bottomleft = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_bottomleft + render_buffer, point_of_bottom_right_on_scene_main.y()*scale_bottomleft + render_buffer)
        
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
        scene_point = self.last_updated_point_of_split_on_scene_main
        # Compatibility: mapToScene(QPoint) → QPoint; mapFromScene() wants QPointF
        if not isinstance(scene_point, QtCore.QPointF):
            scene_point = QtCore.QPointF(scene_point)
        point_of_mouse_on_widget = self._view_main_topleft.mapFromScene(scene_point)
        
        point_of_bottom_right_on_widget = QtCore.QPointF(self.width(), self.height())
        point_of_widget_origin_on_scene_main = self._view_main_topleft.mapToScene(0,0)
        point_of_split_on_scene_main = self._view_main_topleft.mapToScene(max(point_of_mouse_on_widget.x(),0), max(point_of_mouse_on_widget.y(),0))
        point_of_bottom_right_on_scene_main = self._view_main_topleft.mapToScene(int(point_of_bottom_right_on_widget.x()), int(point_of_bottom_right_on_widget.y()))

        self._view_layoutdriving_topleft.setMaximumWidth(max(point_of_mouse_on_widget.x(),0))
        self._view_layoutdriving_topleft.setMaximumHeight(max(point_of_mouse_on_widget.y(),0))
        
        render_buffer = 100

        scale_topright = 1/self._topright_zoom_adjust
        scale_bottomright = 1/self._bottomright_zoom_adjust
        scale_bottomleft = 1/self._bottomleft_zoom_adjust
    
        top_left_of_scene_topright = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_topright, point_of_widget_origin_on_scene_main.y()*scale_topright)
        bottom_right_of_scene_topright = QtCore.QPointF(point_of_bottom_right_on_scene_main.x()*scale_topright + render_buffer, point_of_split_on_scene_main.y()*scale_topright + render_buffer)
        
        top_left_of_scene_bottomright = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_bottomright, point_of_split_on_scene_main.y()*scale_bottomright)
        bottom_right_of_scene_bottomright = QtCore.QPointF(point_of_bottom_right_on_scene_main.x()*scale_bottomright + render_buffer, point_of_bottom_right_on_scene_main.y()*scale_bottomright + render_buffer)
        
        top_left_of_scene_bottomleft = QtCore.QPointF(point_of_widget_origin_on_scene_main.x()*scale_bottomleft, point_of_split_on_scene_main.y()*scale_bottomleft)
        bottom_right_of_scene_bottomleft = QtCore.QPointF(point_of_split_on_scene_main.x()*scale_bottomleft + render_buffer, point_of_bottom_right_on_scene_main.y()*scale_bottomleft + render_buffer)
        
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
        self.update_split(pos=pos_global, pos_is_global=True)

    def on_right_click_comment(self, scene_pos):
        self._scene_main_topleft.addItem(CommentItem(initial_scene_pos=scene_pos, set_cursor_on_creation=True))

    def on_right_click_ruler(self, scene_pos, relative_origin_position, unit="px", px_per_unit=1.0, update_px_per_unit_on_existing=False):
        placement_factor = 1/3

        widget_width = self.width()
        widget_height = self.height()

        pos_p1 = self._view_main_topleft.mapToScene(int(widget_width*placement_factor), int(widget_height*placement_factor))
        pos_p2 = self._view_main_topleft.mapToScene(int(widget_width*(1-placement_factor)), int(widget_height*(1-placement_factor)))
        self._scene_main_topleft.addItem(RulerItem(unit=unit, px_per_mm=px_per_unit, initial_pos_p1=pos_p1, initial_pos_p2=pos_p2, relative_origin_position=relative_origin_position))

    def on_changed_px_per_unit(self, unit, px_per_unit):
        for item in self._scene_main_topleft.items():
            if isinstance(item, RulerItem):
                item.set_and_refresh_px_per_unit(px_per_unit)

    def on_right_click_save_all_comments(self):
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

        date_and_time = datetime.now().strftime('%Y-%m-%d %H%M%S')
        filename = "Untitled comments" + " - " + os.path.basename(filepath_mainview).split('.')[0] + " - " + date_and_time + ".csv"
        name_filters = "CSV (*.csv)"
        
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
        self.display_loading_grayout(True, "Selecting comment file (.csv) to load into current view...", pseudo_load_time=0)

        folderpath = None
        filepath_mainview = self.currentFile

        if filepath_mainview:
            folderpath = filepath_mainview
            folderpath = os.path.dirname(folderpath)
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
                    box_type = QtWidgets.QMessageBox.Icon.Warning
                    title = "Invalid .csv comment file"
                    text = "The selected .csv comment file does not have a format accepted by this app."
                    box_buttons = QtWidgets.QMessageBox.StandardButton.Close
                    box = QtWidgets.QMessageBox(box_type, title, text, box_buttons)
                    box.exec()
                else:
                    i += 1
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
                        box_type = QtWidgets.QMessageBox.Icon.Warning
                        title = "No comments in .csv"
                        text = "No comments found in the selected .csv comment file."
                        box_buttons = QtWidgets.QMessageBox.StandardButton.Close
                        box = QtWidgets.QMessageBox(box_type, title, text, box_buttons)
                        box.exec()
                    
        self.display_loading_grayout(False)

    def on_right_click_set_relative_origin_position(self, string):
        for item in self._scene_main_topleft.items():
            if isinstance(item, RulerItem):
                item.set_and_refresh_relative_origin_position(string)

    def display_loading_grayout(self, boolean, text="Loading...", pseudo_load_time=0.2):
        self.signal_display_loading_grayout.emit(boolean, text, pseudo_load_time)
        
    def update_mouse_rect(self, pos=None):
        if not self.mouse_rect_scene_main_topleft:
            return
    
        if pos is None:
            point_of_mouse_on_widget = self._view_main_topleft.mapFromGlobal(QtGui.QCursor.pos())
        else:
            point_of_mouse_on_widget = pos
    
        mouse_rect_pos_origin = self._view_main_topleft.mapToScene(int(point_of_mouse_on_widget.x()), int(point_of_mouse_on_widget.y()))
        mouse_rect_pos_origin.setX(math.floor(mouse_rect_pos_origin.x() - self.mouse_rect_width + 1))
        mouse_rect_pos_origin.setY(math.floor(mouse_rect_pos_origin.y() - self.mouse_rect_height + 1))
        
        self.mouse_rect_scene_main_topleft.setPos(mouse_rect_pos_origin.x(), mouse_rect_pos_origin.y())
    
    signal_display_loading_grayout = QtCore.pyqtSignal(bool, str, float)
    became_closed = QtCore.pyqtSignal()
    was_clicked_close_pushbutton = QtCore.pyqtSignal()
    was_set_global_transform_mode = QtCore.pyqtSignal(bool)
    was_set_scene_background_color = QtCore.pyqtSignal(list)
    was_set_sync_zoom_by = QtCore.pyqtSignal(str)
    positionChanged = QtCore.pyqtSignal(QtCore.QPoint)
    sceneChanged = QtCore.pyqtSignal('QList<QRectF>')
    transformChanged = QtCore.pyqtSignal()
    scrollChanged = QtCore.pyqtSignal()

    def connectSbarSignals(self, slot):
        self._view_main_topleft.connectSbarSignals(slot)

    def disconnectSbarSignals(self):
        self._view_main_topleft.disconnectSbarSignals()

    @property
    def pixmap_main_topleft(self):
        return self._pixmapItem_main_topleft.pixmap()

    @pixmap_main_topleft.setter
    def pixmap_main_topleft(self, pixmap_main_topleft):
        if pixmap_main_topleft is not None:
            self._pixmapItem_main_topleft.setPixmap(pixmap_main_topleft)
            self._pixmapItem_main_topleft.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
            self._pixmap_base_original = pixmap_main_topleft
            self.set_opacity_base(100)

    @QtCore.pyqtSlot(int)
    def set_opacity_base(self, percent):
        self._opacity_base = percent

        pixmap_to_be_transparent = QtGui.QPixmap(self._pixmap_base_original.size())
        pixmap_to_be_transparent.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap_to_be_transparent)
        painter.setOpacity(percent/100)
        painter.drawPixmap(QtCore.QPoint(0, 0), self._pixmap_base_original)
        painter.end()

        self._pixmapItem_main_topleft.setPixmap(pixmap_to_be_transparent)
    
    @property
    def pixmap_topright(self):
        return self._pixmapItem_topright.pixmap()
    
    @pixmap_topright.setter
    def pixmap_topright(self, pixmap):
        self._pixmap_topright_original = pixmap
        self.set_opacity_topright(100)
    
    @QtCore.pyqtSlot(int)
    def set_opacity_topright(self, percent):
        if not self.pixmap_topright_exists:
            self._opacity_topright = 100
            return
        
        self._opacity_topright = percent

        pixmap_to_be_transparent = QtGui.QPixmap(self._pixmap_topright_original.size())
        pixmap_to_be_transparent.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap_to_be_transparent)
        painter.setOpacity(percent/100)
        painter.drawPixmap(QtCore.QPoint(0, 0), self._pixmap_topright_original)
        painter.end()

        self._pixmapItem_topright.setPixmap(pixmap_to_be_transparent)
    

    @property
    def pixmap_bottomright(self):
        return self._pixmapItem_bottomright.pixmap()
    
    @pixmap_bottomright.setter
    def pixmap_bottomright(self, pixmap):
        self._pixmap_bottomright_original = pixmap
        self.set_opacity_bottomright(100)
    
    @QtCore.pyqtSlot(int)
    def set_opacity_bottomright(self, percent):
        if not self.pixmap_bottomright_exists:
            self._opacity_bottomright = 100
            return

        self._opacity_bottomright = percent

        pixmap_to_be_transparent = QtGui.QPixmap(self._pixmap_bottomright_original.size())
        pixmap_to_be_transparent.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap_to_be_transparent)
        painter.setOpacity(percent/100)
        painter.drawPixmap(QtCore.QPoint(0, 0), self._pixmap_bottomright_original)
        painter.end()

        self._pixmapItem_bottomright.setPixmap(pixmap_to_be_transparent)
    

    @property
    def pixmap_bottomleft(self):
        return self._pixmapItem_bottomleft.pixmap()
    
    @pixmap_bottomleft.setter
    def pixmap_bottomleft(self, pixmap):
        self._pixmap_bottomleft_original = pixmap
        self.set_opacity_bottomleft(100)
    
    @QtCore.pyqtSlot(int)
    def set_opacity_bottomleft(self, percent):
        if not self.pixmap_bottomleft_exists:
            self._opacity_bottomleft = 100
            return

        self._opacity_bottomleft = percent

        pixmap_to_be_transparent = QtGui.QPixmap(self._pixmap_bottomleft_original.size())
        pixmap_to_be_transparent.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap_to_be_transparent)
        painter.setOpacity(percent/100)
        painter.drawPixmap(QtCore.QPoint(0, 0), self._pixmap_bottomleft_original)
        painter.end()

        self._pixmapItem_bottomleft.setPixmap(pixmap_to_be_transparent)
    
    def moveEvent(self, event):
        super().moveEvent(event)

    def resizeEvent(self, event):
        self.resize_scene()
        super().resizeEvent(event)
        
    def resize_scene(self):
        scene_to_viewport_factor = self._view_main_topleft.zoomFactor
        
        width_viewport_window = self.width()
        height_viewport_window = self.height()

        peek_precent = 0.1
        peek_margin_x = width_viewport_window*peek_precent
        peek_margin_y = height_viewport_window*peek_precent
        
        width_viewport = (width_viewport_window - peek_margin_x)/scene_to_viewport_factor
        height_viewport = (height_viewport_window - peek_margin_y)/scene_to_viewport_factor
        
        width_pixmap = self.imageWidth
        height_pixmap = self.imageHeight
        
        width_scene = 2.0*(width_viewport + width_pixmap/2.0)
        height_scene = 2.0*(height_viewport + height_pixmap/2.0)
        
        scene_rect = QtCore.QRectF(-width_scene/2.0 + width_pixmap/2.0, -height_scene/2.0 + height_pixmap/2.0, width_scene, height_scene)
        self._scene_main_topleft.setSceneRect(scene_rect)
    
    def set_transform_mode_smooth_on(self):
        self.transform_mode_smooth = True
        self._scene_main_topleft.set_single_transform_mode_smooth(True)
        self.refresh_transform_mode()
            
    def set_transform_mode_smooth_off(self):
        self.transform_mode_smooth = False
        self._scene_main_topleft.set_single_transform_mode_smooth(False)
        self.refresh_transform_mode()

    def set_transform_mode_smooth(self, boolean):
        if boolean:
            self.set_transform_mode_smooth_on()
        elif not boolean:
            self.set_transform_mode_smooth_off()
            
    @QtCore.pyqtSlot()
    def on_transformChanged(self):
        self.resize_scene()
        self.update_split()

    @property
    def viewName(self):
        return self._name
    
    @viewName.setter
    def viewName(self, name):
        self._name = name

    @property
    def handDragging(self):
        return self._view_main_topleft.handDragging

    @property
    def scrollState(self):
        return self._view_main_topleft.scrollState

    @scrollState.setter
    def scrollState(self, state):
        self._view_main_topleft.scrollState = state

    @property
    def zoomFactor(self):
        return self._view_main_topleft.zoomFactor

    @zoomFactor.setter
    def zoomFactor(self, newZoomFactor):
        self._view_main_topleft.zoomFactor = newZoomFactor

        scale_topright = newZoomFactor * self._topright_zoom_adjust / self._view_topright.transform().m11()
        scale_bottomright = newZoomFactor * self._bottomright_zoom_adjust / self._view_bottomright.transform().m11()
        scale_bottomleft = newZoomFactor * self._bottomleft_zoom_adjust / self._view_bottomleft.transform().m11()

        self._view_topright.scale(scale_topright, scale_topright)
        self._view_bottomright.scale(scale_bottomright, scale_bottomright)
        self._view_bottomleft.scale(scale_bottomleft, scale_bottomleft)

        self.refresh_transform_mode()

    def refresh_transform_mode(self):
        zoomFactor = self.zoomFactor
        self.set_pixmap_transform_from_scale(self._pixmapItem_main_topleft, zoomFactor)
        
        scale_topright = self._view_topright.transform().m11()
        scale_bottomright = self._view_bottomright.transform().m11()
        scale_bottomleft = self._view_bottomleft.transform().m11()

        self.set_pixmap_transform_from_scale(self._pixmapItem_topright, scale_topright)
        self.set_pixmap_transform_from_scale(self._pixmapItem_bottomright, scale_bottomright)
        self.set_pixmap_transform_from_scale(self._pixmapItem_bottomleft, scale_bottomleft)

    def set_pixmap_transform_from_scale(self, pixmap_item, scale, limit: float = 1.0):
        if (scale < limit) or (self.transform_mode_smooth):
            pixmap_item.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
        else:
            pixmap_item.setTransformationMode(QtCore.Qt.TransformationMode.FastTransformation)

    @property
    def _horizontalScrollBar(self):
        return self._view_main_topleft.horizontalScrollBar()

    @property
    def _verticalScrollBar(self):
        return self._view_main_topleft.verticalScrollBar()

    @property
    def _sceneRect(self):
        return self._view_main_topleft.sceneRect()

    @QtCore.pyqtSlot()
    def scrollToTop(self):
        self._view_main_topleft.scrollToTop()

    @QtCore.pyqtSlot()
    def scrollToBottom(self):
        self._view_main_topleft.scrollToBottom()

    @QtCore.pyqtSlot()
    def scrollToBegin(self):
        self._view_main_topleft.scrollToBegin()

    @QtCore.pyqtSlot()
    def scrollToEnd(self):
        self._view_main_topleft.scrollToEnd()

    @QtCore.pyqtSlot()
    def centerView(self):
        self._view_main_topleft.centerView()

    @QtCore.pyqtSlot(bool)
    def enableScrollBars(self, enable):
        self._view_main_topleft.enableScrollBars(enable)

    @QtCore.pyqtSlot(bool)
    def enableHandDrag(self, enable):
        self._view_main_topleft.enableHandDrag(enable)

    @QtCore.pyqtSlot()
    def zoomIn(self):
        self.scaleImage(self._zoomFactorDelta)

    @QtCore.pyqtSlot()
    def zoomOut(self):
        self.scaleImage(1 / self._zoomFactorDelta)

    @QtCore.pyqtSlot()
    def actualSize(self):
        self.scaleImage(1.0, combine=False)

    @QtCore.pyqtSlot()
    def fitToWindow(self):
        if not self._pixmapItem_main_topleft.pixmap():
            return

        padding_margin = 2
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
        return self._pixmapItem_main_topleft.pixmap().width()
    
    @property
    def imageHeight(self):
        return self._pixmapItem_main_topleft.pixmap().height()

    def handleWheelNotches(self, notches):
        self.scaleImage(self._zoomFactorDelta ** notches)

    def closeEvent(self, event):
        self.disconnectSbarSignals()
        
        self._scene_main_topleft.deleteLater()
        self._view_main_topleft.deleteLater()
        if hasattr(self, '_pixmap_base_original'):
            del self._pixmap_base_original
        
        self._scene_topright.deleteLater()
        self._view_topright.deleteLater()
        if hasattr(self, '_pixmap_topright_original'):
            del self._pixmap_topright_original
        
        self._scene_bottomright.deleteLater()
        self._view_bottomright.deleteLater()
        if hasattr(self, '_pixmap_bottomright_original'):
            del self._pixmap_bottomright_original
        
        self._scene_bottomleft.deleteLater()
        self._view_bottomleft.deleteLater()
        if hasattr(self, '_pixmap_bottomleft_original'):
            del self._pixmap_bottomleft_original
        
        super().closeEvent(event)
        gc.collect()
        self.became_closed.emit()
        setAvailableMemory()
        
    def scaleImage(self, factor, combine=True):
        if not self._pixmapItem_main_topleft.pixmap():
            return

        if combine:
            self.zoomFactor = self.zoomFactor * factor
        else:
            self.zoomFactor = factor
            
        self._view_main_topleft.checkTransformChanged()

    def dumpTransform(self):
        self._view_main_topleft.dumpTransform(self._view_main_topleft.transform(), " "*4)
    
    
    def create_mouse_rect(self):
        pen = QtGui.QPen() 
        pen.setWidth(1)
        pen.setColor(QtGui.QColor(QtCore.Qt.GlobalColor.red))
        pen.setCapStyle(QtCore.Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
            
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor(QtCore.Qt.GlobalColor.transparent))
        
        self.mouse_rect_width = 1
        self.mouse_rect_height = 1
        
        self.mouse_rect_topleft = QtCore.QPointF(0,0)
        self.mouse_rect_bottomright = QtCore.QPointF(self.mouse_rect_width-0.01, self.mouse_rect_height-0.01)
        self.mouse_rect = QtCore.QRectF(self.mouse_rect_topleft, self.mouse_rect_bottomright)
        
        self.mouse_rect_scene_main_topleft = QtWidgets.QGraphicsRectItem(self.mouse_rect)
        self.mouse_rect_scene_main_topleft.setPos(0,0)
        self.mouse_rect_scene_main_topleft.setBrush(brush)
        self.mouse_rect_scene_main_topleft.setPen(pen)
        
        self._scene_main_topleft.addItem(self.mouse_rect_scene_main_topleft)

    def set_mouse_rect_visible(self, boolean):
        self.mouse_rect_scene_main_topleft.setVisible(boolean)