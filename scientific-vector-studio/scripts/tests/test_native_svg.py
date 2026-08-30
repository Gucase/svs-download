import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_native_svg import prepare
from validate_master_svg import validate


SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<defs><linearGradient id="shade"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#b66"/></linearGradient>
<clipPath id="clip"><circle cx="50" cy="50" r="45"/></clipPath></defs>
<path d="M0 0H100V100H0Z" fill="url(#shade)" clip-path="url(#clip)"/>
<text x="10" y="50">EGCG</text></svg>'''


class NativeSvgTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source.svg"
        self.output = Path(self.temp.name) / "native.svg"

    def run_prepare(self, data=SVG):
        self.source.write_text(data, encoding="utf-8")
        return prepare(self.source, self.output, True)

    def test_native_resources_live_text_and_source_preservation(self):
        report = self.run_prepare()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["live_text_count"], 1)
        self.assertEqual(self.source.read_text(encoding="utf-8"), SVG)
        self.assertEqual(ET.parse(self.output).getroot().get("version"), "1.1")
        self.assertFalse(self.output.read_bytes().startswith(b'<?xml'))
        self.assertEqual(validate(self.output, True)["status"], "FAIL")

    def test_no_overwrite_and_repeatable_ids(self):
        self.run_prepare()
        content = self.output.read_bytes()
        with self.assertRaises(ValueError):
            prepare(self.source, self.output)
        second = self.output.with_name("second.svg")
        prepare(self.output, second, True)
        self.assertEqual(content, second.read_bytes())
        with self.assertRaises(ValueError):
            prepare(self.source, self.source)

    def test_reject_unsafe_or_broken_content(self):
        variants = [
            SVG.replace("url(#shade)", "url(https://example.com/a.svg)"),
            SVG.replace("url(#shade)", "url(#missing)"),
            SVG.replace("url(#shade)", "url(#clip)"),
            SVG.replace("<path ", '<path id="shade" '),
            SVG.replace("<path ", '<path onclick="bad()" '),
            SVG.replace("</svg>", '<image href="data:image/png;base64,AAAA"/></svg>'),
            SVG.replace("</svg>", '<script>alert(1)</script></svg>'),
        ]
        for data in variants:
            with self.subTest(data=data):
                report = self.run_prepare(data)
                self.assertEqual(report["status"], "FAIL")
                self.assertFalse(self.output.exists())

    def test_flat_profile_backwards_compatible(self):
        self.source.write_text('<svg viewBox="0 0 10 10"><path id="p" d="M0 0L5 5"/><text id="t">A</text></svg>', encoding="utf-8")
        self.assertEqual(validate(self.source, True)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
