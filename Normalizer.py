import sys
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSlider, QCheckBox,
    QGroupBox, QFileDialog, QMessageBox
)
from PySide6.QtGui import QImage, QPixmap, QIcon

from normalizer_logic import NormalizerLogic

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Normal Map Generator v1.3")
        pixmap = QPixmap(1, 1)
        pixmap.fill(Qt.GlobalColor.transparent)
        self.setWindowIcon(QIcon(pixmap))
        self.setGeometry(100, 100, 1280, 720)
        

        self.original_image_data = None
        self.processed_image_data = None
        self.logic = NormalizerLogic()

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        controls_panel = QWidget()
        controls_panel.setFixedWidth(300)
        controls_layout = QVBoxLayout(controls_panel)
        main_layout.addWidget(controls_panel)

        display_panel = QWidget()
        display_layout = QVBoxLayout(display_panel)
        main_layout.addWidget(display_panel, 1)

        self.load_button = QPushButton("Load Image...")
        self.load_button.clicked.connect(self._load_image)

        self.save_button = QPushButton("Save Normal Map...")
        self.save_button.clicked.connect(self._save_image)

        gen_group = self._create_generator_controls()
        export_group = self._create_export_controls()

        controls_layout.addWidget(self.load_button)
        controls_layout.addWidget(self.save_button)
        controls_layout.addWidget(gen_group)
        controls_layout.addWidget(export_group)
        controls_layout.addStretch()

        self.processed_image_label = self._create_display_label("Load an image to generate a Normal Map")
        display_layout.addWidget(self.processed_image_label)
        
        self._update_ui_state()
        


    def _create_generator_controls(self):
        group = QGroupBox("Generator Settings")
        layout = QGridLayout(group)
        layout.setColumnStretch(1, 1)

        self.hq_mode_check = QCheckBox("High-Quality Mode (Slower)")
        self.hq_mode_check.stateChanged.connect(self._process_image)

        # --- Smoothness Slider ---
        self.smoothness_slider = QSlider(Qt.Orientation.Horizontal)
        self.smoothness_slider.setRange(0, 100) # Corresponds to 0.0 - 10.0
        self.smoothness_slider.setValue(10) # Default 1.0
        self.smoothness_label = QLabel(f"{self.smoothness_slider.value() / 10.0:.1f}")
        self.smoothness_slider.valueChanged.connect(self._on_slider_change)
        
        # --- Intensity Slider ---
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(1, 500) # Corresponds to 0.1 - 50.0
        self.intensity_slider.setValue(2) # Default 0.2
        self.intensity_label = QLabel(f"{self.intensity_slider.value() / 10.0:.1f}")
        self.intensity_slider.valueChanged.connect(self._on_slider_change)
        
        self.invert_x_check = QCheckBox("Invert X (Red)")
        self.invert_x_check.stateChanged.connect(self._process_image)
        
        self.invert_y_check = QCheckBox("Invert Y (Green)")
        self.invert_y_check.stateChanged.connect(self._process_image)

        layout.addWidget(self.hq_mode_check, 0, 0, 1, 3)
        layout.addWidget(QLabel("Smoothness:"), 1, 0)
        layout.addWidget(self.smoothness_slider, 1, 1)
        layout.addWidget(self.smoothness_label, 1, 2)
        layout.addWidget(QLabel("Intensity:"), 2, 0)
        layout.addWidget(self.intensity_slider, 2, 1)
        layout.addWidget(self.intensity_label, 2, 2)
        layout.addWidget(self.invert_x_check, 3, 0, 1, 3)
        layout.addWidget(self.invert_y_check, 4, 0, 1, 3)
        return group
    
    def _on_slider_change(self):
        smoothness_val = self.smoothness_slider.value() / 10.0
        self.smoothness_label.setText(f"{smoothness_val:.1f}")

        intensity_val = self.intensity_slider.value() / 10.0
        self.intensity_label.setText(f"{intensity_val:.1f}")

        self._process_image()

    def _create_export_controls(self):
        group = QGroupBox("Export Settings")
        layout = QGridLayout(group)
        self.bit_depth_combo = QComboBox()
        self.bit_depth_combo.addItems(["8-bit", "16-bit (PNG only)"])
        layout.addWidget(QLabel("Bit Depth:"), 0, 0)
        layout.addWidget(self.bit_depth_combo, 0, 1)
        return group

    def _create_display_label(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFrameShape(QLabel.Shape.StyledPanel)
        label.setMinimumSize(300, 300)
        return label

    def _load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Image", "", "Images (*.png *.jpg *.bmp *.tif)")
        if file_path:
            try:
                with Image.open(file_path) as img:
                    img_rgb = img.convert("RGB")
                    self.original_image_data = np.array(img_rgb)
                self._on_slider_change() # Initial process
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image:\n{e}")
                self.original_image_data = None
            self._update_ui_state()

    def _save_image(self):
        if self.processed_image_data is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)")
        if file_path:
            try:
                img_to_save = self.processed_image_data
                
                if "16-bit" in self.bit_depth_combo.currentText() and file_path.lower().endswith('.png'):
                    img_to_save_16bit = (img_to_save.astype(np.uint16) * 257)
                    r = Image.fromarray(img_to_save_16bit[:,:,0], mode='I;16')
                    g = Image.fromarray(img_to_save_16bit[:,:,1], mode='I;16')
                    b = Image.fromarray(img_to_save_16bit[:,:,2], mode='I;16')
                    final_img = Image.merge("RGB", (r, g, b))
                else:
                    final_img = Image.fromarray(img_to_save)
                
                final_img.save(file_path)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image:\n{e}")

    def _process_image(self):
        if self.original_image_data is None:
            return

        params = {
            'high_quality': self.hq_mode_check.isChecked(),
            'smoothness': self.smoothness_slider.value() / 10.0,
            'intensity': self.intensity_slider.value() / 10.0,
            'invert_x': self.invert_x_check.isChecked(),
            'invert_y': self.invert_y_check.isChecked()
        }
        self.processed_image_data = self.logic.generate_normal_map(self.original_image_data, params)
        self._update_displays()

    def _update_displays(self):
        if self.processed_image_data is not None:
            self.processed_image_label.setPixmap(self._numpy_to_pixmap(self.processed_image_data))

    def _numpy_to_pixmap(self, array):
        h, w, ch = array.shape
        bytes_per_line = ch * w
        q_image = QImage(array.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        return pixmap.scaled(self.processed_image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def _update_ui_state(self):
        is_loaded = self.original_image_data is not None
        for child in self.findChildren(QWidget):
            if isinstance(child, (QComboBox, QSlider, QCheckBox, QPushButton)) and child != self.load_button:
                child.setEnabled(is_loaded)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
