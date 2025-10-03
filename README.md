# Normal Map Generator

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6-2796EC?style=flat&logo=qt)](https://www.qt.io/qt-for-python)
[![Issues](https://img.shields.io/github/issues/dovvnloading/normalizer)](https://github.com/dovvnloading/normalizer/issues)

A powerful and intuitive desktop application for generating high-quality normal maps from 2D images. This tool is designed for 3D artists, game developers, and CGI professionals who need a fast and flexible way to create detailed normal maps for their projects.

Built with Python and PySide6, this generator provides real-time previews and robust controls to fine-tune your results, transforming any texture or height map into a production-ready normal map.

<img width="1282" height="752" alt="Screenshot 2025-10-02 205150" src="https://github.com/user-attachments/assets/95a82efa-91e2-499a-9d8b-bd814747411c" />


## Features

-   **High-Quality Conversion:** Utilizes the Scharr operator for accurate gradient calculation and offers an optional High-Quality mode with a bilateral filter for edge-preserving smoothing.
-   **Real-Time Preview:** All adjustments are reflected instantly in the main display window.
-   **Intuitive Controls:** Uses interactive sliders for precise control over key parameters.
    -   **Intensity / Strength:** Control the perceived depth and power of the normal map.
    -   **Smoothness:** Apply a pre-blur to the source image to reduce noise and create smoother surfaces.
-   **Channel Inversion:** Independently invert the X (Red) and Y (Green) channels to ensure compatibility with different rendering engines (e.g., OpenGL vs. DirectX).
-   **Flexible Export Options:**
    -   Save normal maps in common formats like PNG, JPEG, and BMP.
    -   Export in both **8-bit** and **16-bit** color depths (16-bit for PNG only) for professional workflows.
-   **Cross-Platform:** Built with the Qt framework (PySide6), allowing it to run on Windows, macOS, and Linux.

## Technology Stack

-   **Backend:** Python 3.9+
-   **GUI:** PySide6
-   **Core Image Processing:**
    -   **NumPy:** For high-performance numerical operations.
    -   **SciPy:** For signal convolution (Scharr filter).
    -   **scikit-image:** For advanced image filtering, including the high-quality bilateral filter.
    -   **Pillow (PIL Fork):** For loading and saving a wide range of image formats.

## Installation

To run this application on your local machine, please follow these steps.

#### Prerequisites

-   [Python](https://www.python.org/downloads/) (version 3.9 or newer)
-   [Git](https://git-scm.com/downloads/)

#### Setup Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/dovvnloading/normalizer.git
    cd normalizer
    ```

2.  **Create and activate a virtual environment (Recommended):**
    -   **On Windows:**
        ```bash
        python -m venv .venv
        .\.venv\Scripts\activate
        ```
    -   **On macOS / Linux:**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Install the required dependencies:**
    ```bash
    pip install numpy scipy scikit-image PySide6 Pillow
    ```

## Usage

Once the installation is complete, you can run the application from your terminal.

1.  **Launch the application:**
    ```bash
    python normalizer.py
    ```
2.  **Load an Image:** Click the "Load Image..." button and select a source image to use as a height map.
3.  **Adjust Parameters:** Use the sliders and checkboxes to modify the smoothness, intensity, and channel inversion to achieve the desired effect.
4.  **Save the Normal Map:** Click the "Save Normal Map..." button, choose your desired bit depth, and save the file.

#### For Visual Studio Users
This repository includes a Visual Studio solution file (`.sln`). You can open the project in Visual Studio, ensure your Python environment is configured with the dependencies listed above, and run/debug the `normalizer.py` script directly from the IDE.

## Contributing

Contributions are welcome! If you have suggestions for improvements, find a bug, or want to add a new feature, please feel free to:

-   [Open an issue](https://github.com/dovvnloading/normalizer/issues) to discuss the change.
-   Fork the repository and submit a pull request.

## License

This project is licensed under the **Apache 2.0 License**. See the `LICENSE` file for more details.
