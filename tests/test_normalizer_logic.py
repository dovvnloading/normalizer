import unittest

import numpy as np

from normalizer_logic import NormalizerLogic


class TestNormalizerLogic(unittest.TestCase):
    def setUp(self):
        self.logic = NormalizerLogic()

    def test_flat_image_produces_neutral_normal(self):
        image = np.full((32, 32, 3), 128, dtype=np.uint8)
        out = self.logic.generate_normal_map(image, {"intensity": 1.0})
        self.assertEqual(out.shape, image.shape)
        self.assertTrue(np.all(out[..., 0] == 128))
        self.assertTrue(np.all(out[..., 1] == 128))
        self.assertTrue(np.all(out[..., 2] == 255))

    def test_x_inversion_flips_red_channel_direction(self):
        ramp = np.tile(np.linspace(0, 255, 32, dtype=np.uint8), (32, 1))
        image = np.stack([ramp, ramp, ramp], axis=-1)

        regular = self.logic.generate_normal_map(
            image,
            {"intensity": 2.0, "invert_x": False, "invert_y": False, "smoothness": 0.0},
        )
        inverted = self.logic.generate_normal_map(
            image,
            {"intensity": 2.0, "invert_x": True, "invert_y": False, "smoothness": 0.0},
        )

        self.assertTrue(np.mean(regular[..., 0]) < 128)
        self.assertTrue(np.mean(inverted[..., 0]) > 128)


if __name__ == "__main__":
    unittest.main()
