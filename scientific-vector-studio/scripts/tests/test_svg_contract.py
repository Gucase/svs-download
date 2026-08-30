import unittest
import test_native_svg
from xml.etree import ElementTree as ET
from validate_master_svg import validate

SVG = test_native_svg.SVG

class SvgContractTests(unittest.TestCase):
    setUp = test_native_svg.NativeSvgTests.setUp
    run_prepare = test_native_svg.NativeSvgTests.run_prepare
    def test_content_preserved_except_ids_and_version(self):
        self.run_prepare()
        before, after = ET.fromstring(SVG), ET.parse(self.output).getroot()
        for a, b in zip(before.iter(), after.iter()):
            self.assertEqual(a.tag, b.tag)
            self.assertEqual(a.text, b.text)
            self.assertEqual({k: v for k, v in a.attrib.items() if k not in ('id', 'version')},
                             {k: v for k, v in b.attrib.items() if k not in ('id', 'version')})

    def test_validator_rejects_entities_and_css_escape(self):
        for data in [
            '<!DOCTYPE svg [<!ENTITY x "bad">]>' + SVG,
            SVG.replace('<path ', '<path style="fill: url (https://example.org/a)" '),
            SVG.replace('<path ', '<path style="fill: u\\72l(#shade)" '),
            SVG.replace('<path ', '<path style="broken declaration" '),
        ]:
            self.source.write_text(data, encoding='utf-8')
            self.assertEqual(validate(self.source, False, 'illustrator-native')['status'], 'FAIL')

    def test_no_labels_required_for_unlabelled_artwork(self):
        self.source.write_text('<svg viewBox="0 0 8 8"><circle id="a" cx="4" cy="4" r="3"/></svg>', encoding='utf-8')
        self.assertEqual(validate(self.source)['status'], 'PASS')
        self.assertEqual(validate(self.source, True)['status'], 'FAIL')

if __name__ == '__main__':
    unittest.main()
