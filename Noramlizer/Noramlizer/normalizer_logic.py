from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.ndimage import convolve, gaussian_filter
from skimage.restoration import denoise_bilateral


@dataclass(frozen=True)
class NormalMapParams:
    high_quality: bool = False
    smoothness: float = 0.0
    intensity: float = 1.0
    invert_x: bool = False
    invert_y: bool = False
    linearize_srgb: bool = True


class NormalizerLogic:
    """Image-processing pipeline for generating tangent-space normal maps."""

    _SCHARR_X = np.array([[-3.0, 0.0, 3.0], [-10.0, 0.0, 10.0], [-3.0, 0.0, 3.0]], dtype=np.float32) / 32.0
    _SCHARR_Y = np.array([[-3.0, -10.0, -3.0], [0.0, 0.0, 0.0], [3.0, 10.0, 3.0]], dtype=np.float32) / 32.0

    def generate_normal_map(self, image_data: np.ndarray, params: dict | NormalMapParams) -> Optional[np.ndarray]:
        if image_data is None:
            return None

        config = params if isinstance(params, NormalMapParams) else NormalMapParams(**params)

        height_map = self._to_height_map(image_data, linearize=config.linearize_srgb)
        height_map = self._apply_smoothing(height_map, config)

        grad_x = convolve(height_map, self._SCHARR_X, mode="reflect")
        grad_y = convolve(height_map, self._SCHARR_Y, mode="reflect")

        return self._encode_normal_map(grad_x, grad_y, config.intensity, config.invert_x, config.invert_y)

    @staticmethod
    def _to_height_map(image_data: np.ndarray, linearize: bool) -> np.ndarray:
        img_float = image_data.astype(np.float32) / 255.0

        if linearize:
            srgb_threshold = 0.04045
            img_linear = np.where(
                img_float <= srgb_threshold,
                img_float / 12.92,
                ((img_float + 0.055) / 1.055) ** 2.4,
            )
        else:
            img_linear = img_float

        # Rec. 709 luminance.
        return (
            img_linear[:, :, 0] * 0.2126
            + img_linear[:, :, 1] * 0.7152
            + img_linear[:, :, 2] * 0.0722
        )

    @staticmethod
    def _apply_smoothing(height_map: np.ndarray, params: NormalMapParams) -> np.ndarray:
        if params.smoothness <= 0.0:
            return height_map

        if params.high_quality:
            sigma_color = max(1e-4, params.smoothness / 10.0)
            sigma_spatial = max(1e-4, params.smoothness)
            return denoise_bilateral(
                height_map,
                sigma_color=sigma_color,
                sigma_spatial=sigma_spatial,
                channel_axis=None,
            )

        return gaussian_filter(height_map, sigma=params.smoothness)

    @staticmethod
    def _encode_normal_map(
        grad_x: np.ndarray,
        grad_y: np.ndarray,
        intensity: float,
        invert_x: bool,
        invert_y: bool,
    ) -> np.ndarray:
        nx = -grad_x * intensity
        ny = -grad_y * intensity

        if invert_x:
            nx = -nx
        if invert_y:
            ny = -ny

        nz = np.ones_like(nx, dtype=np.float32)

        magnitude = np.sqrt(nx * nx + ny * ny + nz * nz, dtype=np.float32)
        magnitude = np.maximum(magnitude, 1e-8)

        nx_norm = nx / magnitude
        ny_norm = ny / magnitude
        nz_norm = nz / magnitude

        normal_map = np.stack((nx_norm, ny_norm, nz_norm), axis=-1)
        normal_map = np.clip(normal_map * 0.5 + 0.5, 0.0, 1.0)
        return np.rint(normal_map * 255.0).astype(np.uint8)
