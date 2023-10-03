#!/usr/bin/env python3

"""QDialog widgets for SplitView.

Not intended as a script. Used in Butterfly Viewer.

Creates a dialog window for users to calculate the pixel-unit conversion for rulers in SplitView.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt5 import QtWidgets, QtCore



class PixelUnitConversionInputDialog(QtWidgets.QDialog):
    """Create a dialog window to calculate the conversion for pixels to other units of length in SplitView.
    
    Currently only supports millimeters.
    Emits the value of the px-per-mm conversion if user clicks "Ok" on dialog.

    Args:
        parent: Do not set OR only set to None.
        unit (str): Unit of length to which to convert from pixels, abbreviated. 
            Currently only supports "mm" (millimeters).
        px_conversion (float): Quantity of pixels in a known distance.
        unit_conversion (float): Quantity of the specified unit of length in a known distance.
        px_per_unit (float): Pixel-per-unit conversion. Set to None if not previously calculated.
    """  

    def __init__(self, parent=None, unit="mm", px_conversion=1.0, unit_conversion=1.0, px_per_unit=None):
        super().__init__(parent)
        self.setWindowTitle("Set conversion factor for pixel-per-" + unit + " conversion for this image window")
        self.setWindowFlags(QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint)

        frame_rect = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame_rect.moveCenter(center_point)
        self.move(frame_rect.topLeft())

        self.unit = unit
        if unit == "mm":
            self.unit_longform = "millimeter"
            self.unit_longform_cap = "Millimeter"
        else:
            self.unit_longform = unit
            self.unit_longform_cap = self.unit_longform
        self.px_conversion = px_conversion # e.g., 100 pixels
        self.unit_conversion = unit_conversion # e.g., 50 mm
        self.px_per_unit = px_per_unit
        if self.px_per_unit is None:
            self.px_per_unit = self.px_conversion/self.unit_conversion # e.g., 100 px per 50 mm = 2 px/mm

        buttonbox = QtWidgets.QDialogButtonBox()
        buttonbox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        buttonbox.accepted.connect(self.accept) 
        buttonbox.rejected.connect(self.reject)

        dialog_string = "Enter the pixel and " + self.unit_longform + " length for a known distance in the base image of the active window."
        dialog_string = dialog_string + "\n\n" + "Tip: First use a pixel ruler to measure a known distance in the image (such as the width of a painting canvas or the length of a calibration ruler) and then enter the distance in pixels and " + self.unit_longform + "s here.\n"
        dialog_label = QtWidgets.QLabel(dialog_string)
        dialog_label.setWordWrap(True)

        values_layout = QtWidgets.QGridLayout()
        px_label = QtWidgets.QLabel("Pixels in a known distance: ")
        px_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        px_string = "{:.2f}".format(self.px_conversion)
        self.px_textedit = QtWidgets.QLineEdit(px_string)
        self.px_textedit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.px_textedit.textEdited.connect(self.on_px_textedit_edited)
        self.px_textedit.editingFinished.connect(lambda: self.px_textedit.setText("{:.2f}".format(self.px_conversion)))

        unit_label = QtWidgets.QLabel(self.unit_longform_cap + "s" + " in a known distance: ")
        unit_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        unit_string = "{:.2f}".format(self.unit_conversion) # + " " + "px"
        self.unit_textedit = QtWidgets.QLineEdit(unit_string)
        self.unit_textedit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.unit_textedit.textEdited.connect(self.on_unit_textedit_edited)
        self.unit_textedit.editingFinished.connect(lambda: self.unit_textedit.setText("{:.2f}".format(self.unit_conversion)))

        px_per_unit_label = QtWidgets.QLabel("Calculated pixels per " + self.unit_longform + " for the known distance: ")
        px_per_unit_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        px_per_unit_string = "{:.2f}".format(self.px_per_unit)
        self.px_per_unit_textedit = QtWidgets.QLineEdit(px_per_unit_string)
        self.px_per_unit_textedit.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: 0px transparent;
            }
            """)
        self.px_per_unit_textedit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.px_per_unit_textedit.setReadOnly(True)

        values_layout.addWidget(px_label, 0, 0)
        values_layout.addWidget(self.px_textedit, 0, 1)
        values_layout.addWidget(unit_label, 1, 0)
        values_layout.addWidget(self.unit_textedit, 1, 1)
        values_layout.addWidget(px_per_unit_label, 2, 0)
        values_layout.addWidget(self.px_per_unit_textedit, 2, 1)

        values_layout_widget = QtWidgets.QWidget()
        values_layout_widget.setLayout(values_layout)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(dialog_label)
        layout.addWidget(values_layout_widget)
        layout.addWidget(buttonbox)

        self.setStyleSheet("font-size: 9pt")

    def on_px_textedit_edited(self, text):
        """Filter and correct text typed into pixel field.
        
        Corrects the following:
            Decimal comma to decimal point (0,2 > 0.2).
            No leading zero to leading zero (.2 > 0.2).
            Hanging decimal to zero in tenths place (2. > 2.0).

        Filters:
            Non-numeric text.
            Non float-to-text convertible numbers.
            Zeroes (distances cannot be zero).

        Triggered by QLineEdit.textEdited.
        
        Args:
            text (str): From QLineEdit.textEdited.
        """
        if text is None:
            return
        text = text.replace(" ", "")
        if text is "":
            return
        text = text.replace(",", ".")
        text_filter = text
        text_filter = text.replace(".", "")
        if not text_filter.isnumeric():
            return
        if text.endswith("."):
            text.replace(".", ".0")
        if text.startswith("."):
            text.replace(".", "0.")
        
        try: 
            px_conversion = float(text)
        except:
            return
        
        try: #: Ensure not zero.
            1/px_conversion
        except:
            return
       
        self.px_conversion = px_conversion
        self.px_per_unit = self.px_conversion/self.unit_conversion
        self.px_per_unit_textedit.setText("{:.2f}".format(self.px_per_unit))

    def on_unit_textedit_edited(self, text):
        """Filter and correct text typed into unit of length field.
        
        Corrects the following:
            Decimal comma to decimal point (0,2 > 0.2).
            No leading zero to leading zero (.2 > 0.2).
            Hanging decimal to zero in tenths place (2. > 2.0).

        Filters:
            Non-numeric text.
            Non float-to-text convertible numbers.
            Zeroes.

        Triggered by QLineEdit.textEdited.
        
        Args:
            text (str): From QLineEdit.textEdited.
        """
        if text is None:
            return
        text = text.replace(" ", "")
        if text is "":
            return
        text = text.replace(",", ".")
        text_filter = text
        text_filter = text.replace(".", "")
        if not text_filter.isnumeric():
            return
        if text.endswith("."):
            text.replace(".", ".0")
        if text.startswith("."):
            text.replace(".", "0.")
            
        try:
            unit_conversion = float(text)
        except:
            return
        
        try: #: Ensure not dividing by zero.
            px_per_unit = self.px_conversion/unit_conversion
        except:
            return
        
        self.unit_conversion = unit_conversion
        self.px_per_unit = px_per_unit
        self.px_per_unit_textedit.setText("{:.2f}".format(self.px_per_unit))