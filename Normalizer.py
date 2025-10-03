import sys
import numpy as np
from PIL import Image
from scipy.signal import convolve2d
from scipy.ndimage import gaussian_filter
from skimage.restoration import denoise_bilateral

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSlider, QCheckBox,
    QGroupBox, QFileDialog, QMessageBox
)
from PySide6.QtGui import QImage, QPixmap, QIcon

class NormalizerLogic:
    """Encapsulates the image processing logic for generating normal maps."""

    def generate_normal_map(self, image_data, params):
        if image_data is None:
            return None

        # --- 1. Convert to Grayscale Height Map ---
        img_float = image_data.astype(np.float64) / 255.0 # Work with floats in [0, 1] for filters
        height_map = (img_float[:, :, 0] * 0.2126 + 
                      img_float[:, :, 1] * 0.7152 + 
                      img_float[:, :, 2] * 0.0722)

        # --- 2. Apply Smoothing ---
        use_hq_mode = params.get('high_quality', False)
        smoothness = params.get('smoothness', 0.0)

        if use_hq_mode:
            # Only apply the filter if smoothness is non-zero to prevent division by zero errors.
            if smoothness > 0.001:
                sigma_color = smoothness / 10.0
                sigma_spatial = smoothness
                height_map = denoise_bilateral(height_map, sigma_color=sigma_color, sigma_spatial=sigma_spatial, channel_axis=None)
        else:
            if smoothness > 0:
                height_map = gaussian_filter(height_map, sigma=smoothness)

        # --- 3. Calculate Gradients using Scharr Operator (more accurate than Sobel) ---
        scharr_x = np.array([[-3, 0, 3], [-10, 0, 10], [-3, 0, 3]])
        scharr_y = np.array([[-3, -10, -3], [0, 0, 0], [3, 10, 3]])

        grad_x = convolve2d(height_map, scharr_x, mode='same', boundary='symm')
        grad_y = convolve2d(height_map, scharr_y, mode='same', boundary='symm')

        # --- 4. Calculate Normal Vectors ---
        intensity = params['intensity']
        
        nx = -grad_x * intensity
        ny = -grad_y * intensity
        
        if params['invert_x']:
            nx *= -1
        if params['invert_y']:
            ny *= -1
        
        nz = np.ones_like(nx)

        magnitude = np.sqrt(nx**2 + ny**2 + nz**2)
        magnitude[magnitude == 0] = 1

        nx_norm = nx / magnitude
        ny_norm = ny / magnitude
        nz_norm = nz / magnitude

        # --- 5. Encode Vectors into RGB Image ---
        normal_map = np.zeros_like(img_float)
        normal_map[..., 0] = (nx_norm * 0.5 + 0.5)
        normal_map[..., 1] = (ny_norm * 0.5 + 0.5)
        normal_map[..., 2] = (nz_norm * 0.5 + 0.5)

        return (normal_map * 255).astype(np.uint8)

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
                QMessageBox.critical(self, "Error", f"Failed to save image:\an{e}")

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
