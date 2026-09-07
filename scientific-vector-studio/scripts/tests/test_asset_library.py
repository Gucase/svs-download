import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
LIBRARY = ROOT / "assets" / "scientific-library"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("validate_master_svg", SCRIPTS / "validate_master_svg.py")


class AssetLibraryTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((LIBRARY / "manifest.json").read_text(encoding="utf-8"))

    def test_library_contains_sixty_unique_assets(self):
        assets = self.manifest["assets"]
        self.assertEqual(60, self.manifest["asset_count"])
        self.assertEqual(60, len(assets))
        self.assertEqual(60, len({item["id"] for item in assets}))
        counts = {category: sum(item["category"] == category for item in assets)
                  for category in ("arrows", "labware", "instruments", "biology", "medical")}
        self.assertEqual({"arrows": 6, "labware": 20, "instruments": 15,
                          "biology": 11, "medical": 8}, counts)

    def test_every_asset_is_portable_vector_geometry(self):
        for item in self.manifest["assets"]:
            with self.subTest(asset=item["id"]):
                report = validator.validate(LIBRARY / item["file"], profile="portable")
                self.assertEqual("PASS", report["status"], report["errors"])
                self.assertGreater(report["geometry_count"], 0)

    def test_review_claims_are_truthful_before_app_review(self):
        for item in self.manifest["assets"]:
            self.assertEqual("candidate", item["review_status"])
            self.assertFalse(item["illustrator_verified"])
            self.assertFalse(item["powerpoint_verified"])

    def test_semantic_parts_exist(self):
        from xml.etree import ElementTree as ET
        for item in self.manifest["assets"]:
            root = ET.fromstring((LIBRARY / item["file"]).read_bytes())
            ids = {node.get("id") for node in root.iter() if node.get("id")}
            self.assertTrue(set(item["editable_parts"]).issubset(ids), item["id"])


if __name__ == "__main__":
    unittest.main()
