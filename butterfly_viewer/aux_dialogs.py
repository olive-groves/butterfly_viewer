#!/usr/bin/env python3

"""QDialog widgets for SplitView.

Not intended as a script. Used in Butterfly Viewer.
"""
# SPDX-License-Identifier: GPL-3.0-or-later



from PyQt6 import QtWidgets, QtCore



class PixelUnitConversionInputDialog(QtWidgets.QDialog):
    """Dialog for pixel-per-mm conversion in SplitView."""

    def __init__(self, parent=None, unit="mm", px_conversion=1.0, unit_conversion=1.0, px_per_unit=None):
        super().__init__(parent)
        self.setWindowTitle("Set conversion factor for pixel-per-" + unit + " conversion for this image window")
        self.setWindowFlags(QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.WindowCloseButtonHint)

        frame_rect = self.frameGeometry()
        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            center_point = screen.availableGeometry().center()
            frame_rect.moveCenter(center_point)
            self.move(frame_rect.topLeft())

        self.unit = unit
        if unit == "mm":
            self.unit_longform = "millimeter"
            self.unit_longform_cap = "Millimeter"
        else:
            self.unit_longform = unit
            self.unit_longform_cap = self.unit_longform
        self.px_conversion = px_conversion
        self.unit_conversion = unit_conversion
        self.px_per_unit = px_per_unit
        if self.px_per_unit is None:
            self.px_per_unit = self.px_conversion/self.unit_conversion

        buttonbox = QtWidgets.QDialogButtonBox()
        buttonbox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok)
        buttonbox.accepted.connect(self.accept) 
        buttonbox.rejected.connect(self.reject)

        dialog_string = "Enter the pixel and " + self.unit_longform + " length for a known distance in the base image of the active window."
        dialog_string = dialog_string + "\n\n" + "Tip: First use a pixel ruler to measure a known distance in the image (such as the width of a painting canvas or the length of a calibration ruler) and then enter the distance in pixels and " + self.unit_longform + "s here.\n"
        dialog_label = QtWidgets.QLabel(dialog_string)
        dialog_label.setWordWrap(True)

        values_layout = QtWidgets.QGridLayout()
        px_label = QtWidgets.QLabel("Pixels in a known distance: ")
        px_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        px_string = "{:.2f}".format(self.px_conversion)
        self.px_textedit = QtWidgets.QLineEdit(px_string)
        self.px_textedit.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.px_textedit.textEdited.connect(self.on_px_textedit_edited)
        self.px_textedit.editingFinished.connect(lambda: self.px_textedit.setText("{:.2f}".format(self.px_conversion)))

        unit_label = QtWidgets.QLabel(self.unit_longform_cap + "s" + " in a known distance: ")
        unit_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        unit_string = "{:.2f}".format(self.unit_conversion)
        self.unit_textedit = QtWidgets.QLineEdit(unit_string)
        self.unit_textedit.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.unit_textedit.textEdited.connect(self.on_unit_textedit_edited)
        self.unit_textedit.editingFinished.connect(lambda: self.unit_textedit.setText("{:.2f}".format(self.unit_conversion)))

        px_per_unit_label = QtWidgets.QLabel("Calculated pixels per " + self.unit_longform + " for the known distance: ")
        px_per_unit_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        px_per_unit_string = "{:.2f}".format(self.px_per_unit)
        self.px_per_unit_textedit = QtWidgets.QLineEdit(px_per_unit_string)
        self.px_per_unit_textedit.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: 0px transparent;
            }
            """)
        self.px_per_unit_textedit.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
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
        if text is None:
            return
        text = text.replace(" ", "")
        if text == "":
            return
        text = text.replace(",", ".")
        text_filter = text.replace(".", "")
        if not text_filter.isnumeric():
            return
        if text.endswith("."):
            text = text + "0"
        if text.startswith("."):
            text = "0" + text
        
        try: 
            px_conversion = float(text)
        except Exception:
            return
        
        try:
            1/px_conversion
        except Exception:
            return
       
        self.px_conversion = px_conversion
        self.px_per_unit = self.px_conversion/self.unit_conversion
        self.px_per_unit_textedit.setText("{:.2f}".format(self.px_per_unit))

    def on_unit_textedit_edited(self, text):
        if text is None:
            return
        text = text.replace(" ", "")
        if text == "":
            return
        text = text.replace(",", ".")
        text_filter = text.replace(".", "")
        if not text_filter.isnumeric():
            return
        if text.endswith("."):
            text = text + "0"
        if text.startswith("."):
            text = "0" + text
            
        try:
            unit_conversion = float(text)
        except Exception:
            return
        
        try:
            px_per_unit = self.px_conversion/unit_conversion
        except Exception:
            return
        
        self.unit_conversion = unit_conversion
        self.px_per_unit = px_per_unit
        self.px_per_unit_textedit.setText("{:.2f}".format(self.px_per_unit))