#!/usr/bin/env python3

"""Drag-and-drop interface widgets and their supporting subwidgets for Butterfly Viewer.

Not intended as a script.

Interface widgets are:
    DragDropImageLabel, for users to drag and drop an image from local storage and show a preview in the drop area.
    FourDragDropImageLabel, a 2x2 panel of DragDropImageLabel designed for users to arrange images for a SplitView.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



import sys
import time

from PyQt5 import QtCore, QtGui, QtWidgets

from aux_labels import FilenameLabel



class ImageLabel(QtWidgets.QLabel):
    """Custom QLabel as a drag-and-drop zone for images.
    
    Instantiate without input.
    """

    became_occupied = QtCore.pyqtSignal(bool)

    def __init__(self, text=None, is_addable=True):
        super().__init__()

        self.IS_ADDABLE = is_addable
        self.IS_OCCUPIED = False

        # self.setMargin(4)
        self.setAlignment(QtCore.Qt.AlignCenter)

        if text:
            self.setText(text)

        self.set_stylesheet_occupied(self.IS_OCCUPIED)


    def setPixmap(self, image):
        """QPixmap: Extend setPixmap() to also set style and size, and execute supporting functions."""
        size = self.size()
        self.IS_OCCUPIED = True
        self.original_pixmap = image
        self.set_pixmap_to_label_size()
        self.set_stylesheet_occupied(self.IS_OCCUPIED)
        self.became_occupied.emit(True)
        self.setFixedSize(size)
        
    def set_pixmap_to_label_size(self):
        """Resize and set pixmap to the label's size, thus maintaining the label's size and shape."""
        w = self.width_contents()
        h = self.height_contents()
        p = self.original_pixmap
        p = p.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        super().setPixmap(p)
            
    def clear(self):
        """Extend clear() to also set style and size, reduce memory."""
        self.IS_OCCUPIED = False
        self.set_stylesheet_occupied(self.IS_OCCUPIED)

        if self.original_pixmap:
            del self.original_pixmap # Remove from memory
            
        super().clear()

        self.became_occupied.emit(False)

        self.setMinimumSize(QtCore.QSize(0,0))
        self.setMinimumSize(QtCore.QSize(QtWidgets.QWIDGETSIZE_MAX,QtWidgets.QWIDGETSIZE_MAX))
    
    
    def width_contents(self):
        """float: Width of the label's contents excluding the frame width."""
        return self.width() - 2*self.frameWidth()
    
    def height_contents(self):
        """float: Height of the label's contents excluding the frame width."""
        return self.height() - 2*self.frameWidth()

    # Styles

    def stylesheet_unoccupied_notaddable(self):
        """Set label stylesheet to unoccupied and unaddable state."""
        self.setStyleSheet("QLabel {font-size: 9pt; border: 0.13em dashed lightGray; border-radius: 0.5em; background-color: transparent;}")

    def stylesheet_unoccupied_addable(self):
        """Set label stylesheet to unoccupied and addable state."""
        self.setStyleSheet("QLabel {font-size: 9pt; border: 0.13em dashed gray; border-radius: 0.5em; background-color: transparent;}")

    def stylesheet_occupied_notaddable(self):
        """Set label stylesheet to occupied and unaddable state."""
        self.setStyleSheet("QLabel font-size: 9pt; border: 0.13em dashed gray; border-radius: 0.5em; background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6F6F6F, stop: 1 #3F3F3F);}")

    def stylesheet_occupied_addable(self):
        """Set label stylesheet to occupied and addable state."""
        self.setStyleSheet("QLabel {font-size: 9pt; border: 0.13em dashed gray; border-radius: 0.5em; background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3F3F3F, stop: 1 #0F0F0F);}")

    def stylesheet_hovered_unoccupied(self):
        """Set label stylesheet to hovered and unoccupied."""
        self.setStyleSheet("QLabel {font-size: 9pt; border: 0.13em dashed black; border-radius: 0.5em; background-color: rgba(0,0,0,63);}")

    def stylesheet_hovered_occupied(self):
        """Set label stylesheet to hovered and occupied."""
        self.setStyleSheet("QLabel {font-size: 9pt; border: 0.13em dashed black; border-radius: 0.5em; background-color: rgba(0,0,0,63);}")

    def set_stylesheet_addable(self, boolean):
        """bool: Set addable state of label stylesheet, considering current occupied state."""
        if boolean:
            if self.IS_OCCUPIED:
                self.stylesheet_occupied_addable()
            else:
                self.stylesheet_unoccupied_addable()
        else:
            if self.IS_OCCUPIED:
                self.stylesheet_occupied_notaddable()
            else:
                self.stylesheet_unoccupied_notaddable()

    def set_stylesheet_occupied(self, boolean):
        """bool: Set occupied state of label stylesheet, considering current addable state."""
        if boolean:
            if self.IS_ADDABLE:
                self.stylesheet_occupied_addable()
            else:
                self.stylesheet_occupied_notaddable()
        else:
            if self.IS_ADDABLE: 
                self.stylesheet_unoccupied_addable()
            else:
                self.stylesheet_unoccupied_notaddable()

    def set_stylesheet_hovered(self, boolean):
        """bool: Set hovered state of label stylesheet, considering current occupied and addable states."""
        if boolean:
            if self.IS_OCCUPIED:
                self.stylesheet_hovered_occupied()
            else:
                self.stylesheet_hovered_unoccupied()
        else:
            if self.IS_ADDABLE:
                if self.IS_OCCUPIED:
                    self.stylesheet_occupied_addable()
                else:
                    self.stylesheet_unoccupied_addable()
            else:
                if self.IS_OCCUPIED:
                    self.stylesheet_occupied_notaddable()
                else:
                    self.stylesheet_unoccupied_notaddable()



class ImageLabelMain(ImageLabel):
    """Extend ImageLabel as 'main' drag-and-drop zone for SplitViewCreator.
    
    Instantiate without input.
    """
    def __init__(self, text=None):
        super().__init__(text)
        


class DragDropImageLabel(QtWidgets.QWidget):
    """Drag-and-drop widget to preview an image from local storage and hold its filepath.
    
    Includes:
        Button to select an image from a dialog window. 
        Button to clear the current image.

    Args:
        show_filename (bool): True to show label with filename over image preview; False to hide.
        show_pushbuttons (bool): True to show button for selecting file from dialog and button to clear image; False to hide.
        is_main (bool): True if the label is the drag zone for the main image of SplitView; False if not.
        text_default (str): Text to show when no image preview is showing.
    """

    became_occupied = QtCore.pyqtSignal(bool)

    def __init__(self, show_filename=False, show_pushbuttons=True, is_main=False, text_default="Drag image"):
        super().__init__()
        
        self.file_path = None
        self.show_filepath_while_loading = False

        self.text_default = text_default
        
        self.MAX_DIMENSION_FOR_IMAGE_IN_LABEL = 400
        
        self.show_filename = show_filename
        self.show_pushbuttons = show_pushbuttons

        self.image_filetypes = [
            ".jpeg", ".jpg", ".jpe", ".jif", ".jfif", ".jfi", ".pjpeg", ".pjp",
            ".png",
            ".tiff", ".tif",
            ".bmp",
            ".webp",
            ".ico", ".cur"]
        
        self.setAcceptDrops(True)

        main_layout = QtWidgets.QGridLayout()

        if is_main:
            self.image_label_child = ImageLabelMain()
        else:
            self.image_label_child = ImageLabel()

        self.image_label_child.became_occupied.connect(self.became_occupied)

        self.set_text(self.text_default)

        main_layout.addWidget(self.image_label_child, 0, 0)

        self.filename_label = FilenameLabel("No filename available", remove_path=True)
        main_layout.addWidget(self.filename_label, 0, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.filename_label.setVisible(False)
        
        if self.show_pushbuttons is True:
            self.buttons_layout = QtWidgets.QGridLayout()
            self.clear_layout = QtWidgets.QGridLayout()
            
            self.open_pushbutton = QtWidgets.QToolButton()
            self.open_pushbutton.setText("Select image...")
            self.open_pushbutton.setToolTip("Select image from file and add here in sliding overlay creator...")
            self.open_pushbutton.setStyleSheet("""
                QToolButton { 
                    font-size: 9pt;
                    } 
                """)

            self.clear_pushbutton = QtWidgets.QToolButton()
            self.clear_pushbutton.setText("×")
            self.clear_pushbutton.setToolTip("Clear image")
            self.clear_pushbutton.setStyleSheet("""
                QToolButton { 
                    font-size: 9pt;
                    } 
                """)
            
            self.open_pushbutton.clicked.connect(self.was_clicked_open_pushbutton)
            self.clear_pushbutton.clicked.connect(self.was_clicked_clear_pushbutton)
            
            w = 8

            self.buttons_layout.addWidget(self.open_pushbutton, 0, 0)
            self.buttons_layout.setContentsMargins(w,w,w,w)
            self.buttons_layout.setSpacing(w)

            self.clear_layout.addWidget(self.clear_pushbutton, 0, 0)
            self.clear_layout.setContentsMargins(w,w,w,w)
            self.clear_layout.setSpacing(w)
            
            main_layout.addLayout(self.buttons_layout, 0, 0, QtCore.Qt.AlignBottom)
            main_layout.addLayout(self.clear_layout, 0, 0, QtCore.Qt.AlignTop|QtCore.Qt.AlignRight)
            
            self.clear_pushbutton.setEnabled(False)
            self.clear_pushbutton.setVisible(False)


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

        main_layout.addWidget(self.loading_grayout_label, 0, 0)
        
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        self.setLayout(main_layout)

    def set_addable(self, boolean):
        """bool: Set whether an imaged may be added (dragged and dropped) into the widget."""
        self.image_label_child.IS_ADDABLE = boolean
        self.image_label_child.setEnabled(boolean)
        self.open_pushbutton.setEnabled(boolean)
        self.setAcceptDrops(boolean)
        self.filename_label.setEnabled(boolean)
        self.image_label_child.set_stylesheet_addable(boolean)
    
    
    def dragEnterEvent(self, event):
        """event: Override dragEnterEvent() to set stylesheet as hovered and read filepath from a dragged image, but reject multiple files."""
        if len(event.mimeData().urls()) is 1 and self.grab_image_urls_from_mimedata(event.mimeData()):
            self.image_label_child.set_stylesheet_hovered(True)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """event: Override dragMoveEvent() to reject multiple files."""
        if len(event.mimeData().urls()) is 1 and self.grab_image_urls_from_mimedata(event.mimeData()):
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """event: Override dragLeaveEvent() to set stylesheet as not hovered."""
        self.image_label_child.set_stylesheet_hovered(False)

    def dropEvent(self, event):
        """event: Override dropEvent() to read filepath from a dragged image and load image preview."""
        urls = self.grab_image_urls_from_mimedata(event.mimeData())
        if len(urls) is 1 and urls:
            event.setDropAction(QtCore.Qt.CopyAction)
            file_path = urls[0].toLocalFile()
            loaded = self.load_image(file_path)
            if loaded:
                event.accept()
            else:
                event.ignore()
                self.image_label_child.set_stylesheet_hovered(False)
        else:
            event.ignore()

    def grab_image_urls_from_mimedata(self, mimedata):
        """mimeData: Get urls (filepaths) from drag event."""
        urls = list()
        for url in mimedata.urls():
            if any([filetype in url.toLocalFile().lower() for filetype in self.image_filetypes]):
                urls.append(url)
        return urls
    
    def mouseDoubleClickEvent(self, event):
        """event: Override mouseDoubleClickEvent() to trigger dialog window to open image."""
        self.open_image_via_dialog() 
    
    def was_clicked_open_pushbutton(self):
        """Trigger dialog window to open image when button to select image is clicked."""
        self.open_image_via_dialog()
    
    def was_clicked_clear_pushbutton(self):
        """Clear image preview when clear button is clicked."""
        self.clear_image()
    
    def set_image(self, pixmap):
        """QPixmap: Scale and set preview of image; set status of clear button."""
        self.image_label_child.setPixmap(pixmap.scaled(self.MAX_DIMENSION_FOR_IMAGE_IN_LABEL, self.MAX_DIMENSION_FOR_IMAGE_IN_LABEL, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self.clear_pushbutton.setEnabled(True)
        self.clear_pushbutton.setVisible(True)
    
    def load_image(self, file_path):
        """str: Load image from filepath with loading grayout; set filename text.
        
        Returns:
            loaded (bool): True if image successfully loaded; False if not."""
        loading_text = "Loading..."
        if self.show_filepath_while_loading:
            loading_text = loading_text.replace("...",  " '" + file_path.split("/")[-1] + "'...")
        self.display_loading_grayout(True, loading_text)
        pixmap = QtGui.QPixmap(file_path)
        if pixmap.depth() is 0:
            self.display_loading_grayout(False)
            return False

        self.set_image(pixmap)
        self.set_filename_label(file_path)
        self.file_path = file_path
        self.display_loading_grayout(False)
        return True
        
    def open_image_via_dialog(self):
        """Open dialog window to select and load image from file."""
        file_dialog = QtWidgets.QFileDialog(self)
        
        file_dialog.setNameFilters([
            "All supported image files (*.jpeg *.jpg  *.png *.tiff *.tif *.gif *.bmp)",
            "All files (*)",
            "JPEG image files (*.jpeg *.jpg)", 
            "PNG image files (*.png)", 
            "TIFF image files (*.tiff *.tif)", 
            "BMP (*.bmp)"])
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        
        if not file_dialog.exec_():
            return
        
        file_path = file_dialog.selectedFiles()[0]
        
        self.load_image(file_path)
    
    def clear_image(self):
        """Clear image preview and filepath; set status of clear button; set text of drag zone."""
        if self.image_label_child.pixmap():
            self.image_label_child.clear()
            
        self.set_text(self.text_default)
        self.file_path = None
        self.clear_pushbutton.setEnabled(False)
        self.clear_pushbutton.setVisible(False)
        self.filename_label.setText("No filename available")
        self.filename_label.setVisible(False)
        
    def set_text(self, text):
        """str: Set text of drag zone when there is no image preview."""
        text_margin_vertical = "\n\n\n"
        self.image_label_child.setText(text_margin_vertical+text+text_margin_vertical)
        
    def set_filename_label(self, text):
        """str: Set text of filename label on image preview."""
        self.filename_label.setText(text)
        self.filename_label.setVisible(self.show_filename)

    def display_loading_grayout(self, boolean, text="Loading...", pseudo_load_time=0.2):
        """Show/hide grayout overlay on label for loading sequences.

        Args:
            boolean (bool): True to show grayout; False to hide.
            text (str): The text to show on the grayout.
            pseudo_load_time (float): The delay (in seconds) to hide the grayout to give users a feeling of action.
        """ 
        if not boolean:
            text = "Loading..."
        self.loading_grayout_label.setText(text)
        self.loading_grayout_label.setVisible(boolean)
        if boolean:
            self.loading_grayout_label.repaint()
        if not boolean:
            time.sleep(pseudo_load_time)
        
        
        
class FourDragDropImageLabel(QtWidgets.QFrame):
    """2x2 panel of drag-and-drop zones for users to arrange images for a SplitView.

    Instantiate without input.
    
    Allows dragging multiple files (1–4) at once.
    """

    will_start_loading = QtCore.pyqtSignal(bool, str)
    has_stopped_loading = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self.image_filetypes = [
            ".jpeg", ".jpg", ".jpe", ".jif", ".jfif", ".jfi", ".pjpeg", ".pjp",
            ".png",
            ".tiff", ".tif",
            ".bmp",
            ".webp",
            ".ico", ".cur"]

        self.setAcceptDrops(True)

        main_layout = QtWidgets.QGridLayout()
        
        self.app_main_topleft   = DragDropImageLabel(show_filename=True, show_pushbuttons=True, is_main=True, text_default="Drag image(s)")
        self.app_topright       = DragDropImageLabel(show_filename=True, show_pushbuttons=True)
        self.app_bottomleft     = DragDropImageLabel(show_filename=True, show_pushbuttons=True)
        self.app_bottomright    = DragDropImageLabel(show_filename=True, show_pushbuttons=True)
        
        main_layout.addWidget(self.app_main_topleft, 0, 0)
        main_layout.addWidget(self.app_topright, 0, 1)
        main_layout.addWidget(self.app_bottomleft, 1, 0)
        main_layout.addWidget(self.app_bottomright, 1, 1)
        
        main_layout.setColumnStretch(0,1)
        main_layout.setColumnStretch(1,1)
        main_layout.setRowStretch(0,1)
        main_layout.setRowStretch(1,1)
        
        contents_margins_w = 0
        main_layout.setContentsMargins(contents_margins_w, contents_margins_w, contents_margins_w, contents_margins_w)
        main_layout.setSpacing(4)
        
        self.setLayout(main_layout)
    
    def dragEnterEvent(self, event):
        """Override dragEnterEvent() to accept multiple (1-4) image files and set stylesheet(s) as hovered."""
        urls = self.grab_image_urls_from_mimedata(event.mimeData())
        if len(event.mimeData().urls()) >= 1 and len(event.mimeData().urls()) <= 4 and self.grab_image_urls_from_mimedata(event.mimeData()):
            self.app_main_topleft.image_label_child.set_stylesheet_hovered(True)
            i = 0
            if len(urls) >= 2:
                i += 1
                self.app_topright.image_label_child.set_stylesheet_hovered(True)

                if len(urls) >= 3:
                    i += 1
                    self.app_bottomright.image_label_child.set_stylesheet_hovered(True)

                    if len(urls) >= 4:
                        i += 1
                        self.app_bottomleft.image_label_child.set_stylesheet_hovered(True)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Override dragMoveEvent() to accept multiple (1-4) image files."""
        if len(event.mimeData().urls()) >= 1 and len(event.mimeData().urls()) <= 4 and self.grab_image_urls_from_mimedata(event.mimeData()):
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Override dragLeaveEvent() to set stylesheet(s) as no longer hovered."""
        self.app_main_topleft.image_label_child.set_stylesheet_hovered(False)
        self.app_topright.image_label_child.set_stylesheet_hovered(False)
        self.app_bottomright.image_label_child.set_stylesheet_hovered(False)
        self.app_bottomleft.image_label_child.set_stylesheet_hovered(False)

    def dropEvent(self, event):
        """event: Override dropEvent() to read filepath(s) from 1-4 dragged images and load the preview(s)."""
        urls = self.grab_image_urls_from_mimedata(event.mimeData())
        n = len(urls)
        n_str = str(n)
        if n >= 1 and n <= 4 and urls:
            event.setDropAction(QtCore.Qt.CopyAction)
            i = 0
            file_path = urls[i].toLocalFile()

            self.will_start_loading.emit(True, "Loading to creator " + str(i+1) + "/" + n_str + "...")

            loaded = self.app_main_topleft.load_image(file_path)
            if not loaded:
                self.app_main_topleft.image_label_child.set_stylesheet_hovered(False)

            if n >= 2:
                i += 1
                file_path = urls[i].toLocalFile()
                self.will_start_loading.emit(True, "Loading to creator " + str(i+1) + "/" + n_str + "...")
                loaded = self.app_topright.load_image(file_path)
                if not loaded:
                    self.app_topright.image_label_child.set_stylesheet_hovered(False)

                if n >= 3:
                    i += 1
                    file_path = urls[i].toLocalFile()
                    self.will_start_loading.emit(True, "Loading to creator " + str(i+1) + "/" + n_str + "...")
                    loaded = self.app_bottomright.load_image(file_path)
                    if not loaded:
                        self.app_bottomright.image_label_child.set_stylesheet_hovered(False)

                    if n >= 4:
                        i += 1
                        file_path = urls[i].toLocalFile()
                        self.will_start_loading.emit(True, "Loading to creator " + str(i+1) + "/" + n_str + "...")
                        loaded = self.app_bottomleft.load_image(file_path)
                        if not loaded:
                            self.app_bottomleft.image_label_child.set_stylesheet_hovered(False)

            self.has_stopped_loading.emit(False)
            
            event.accept()
        else:
            event.ignore()

    def grab_image_urls_from_mimedata(self, mimedata):
        """mimeData: Get urls (filepaths) from drag event."""
        urls = list()
        for url in mimedata.urls():
            if any([filetype in url.toLocalFile().lower() for filetype in self.image_filetypes]):
                urls.append(url)
        return urls

        

def main():
    """Demo the drag-and-drop function in the 2x2 panel."""

    app = QtWidgets.QApplication(sys.argv)
    
    demo = FourDragDropImageLabel()
    demo.show()
    
    sys.exit(app.exec_())



if __name__ == '__main__':
    main()