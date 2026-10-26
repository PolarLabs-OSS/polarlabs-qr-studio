import unittest
from io import BytesIO
from pathlib import Path
from PIL import Image
import resvg_py
from qr_engine import generate, logo_image, decode_test

ROOT = Path(__file__).resolve().parent.parent
URL = "https://www.polarlabs.it/academy"

class QRStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logo = logo_image(ROOT / "assets" / "demo-logo.svg")

    def test_mosaico_fedele_png(self):
        result = generate(self.logo, URL, "Mosaico fedele", 100, False)
        self.assertEqual(result["url"], URL)
        self.assertEqual(result["mode"], "Mosaico fedele")
        self.assertTrue(all(result["tests"]))
        self.assertGreaterEqual(result["modules"], 60)
        self.assertTrue(all(decode_test(result["image"], URL)))

    def test_mosaico_fedele_svg(self):
        result = generate(self.logo, URL, "Mosaico fedele", 100, False)
        data = resvg_py.svg_to_bytes(svg_string=result["svg"], width=800, height=800)
        preview = Image.open(BytesIO(data)).convert("RGB")
        self.assertTrue(all(decode_test(preview, URL)))

    def test_mosaico_soft(self):
        result = generate(self.logo, URL, "Mosaico soft", 100, False)
        self.assertTrue(all(result["tests"]))

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            generate(self.logo, "javascript:alert(1)", "Mosaico fedele", 100, False)

if __name__ == "__main__":
    unittest.main()
