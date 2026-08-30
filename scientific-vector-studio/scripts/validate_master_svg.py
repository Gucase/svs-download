"""SVS local SVG contract checker. Does not render, trace, or resolve resources."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET

DRAWABLE = frozenset('path rect ellipse circle line polyline polygon'.split())
STRUCTURAL = frozenset('svg defs g text tspan title desc metadata'.split())
PAINT = frozenset(('linearGradient', 'radialGradient'))
NATIVE = PAINT | {'stop', 'clipPath'}
URI = re.compile(r'''url\(\s*(?:"#([\w.-]+)"|'#([\w.-]+)'|#([\w.-]+))\s*\)''', re.I)
NUMBER = re.compile(r'[+-]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][+-]?\d+)?')

def local_name(value):
    return value.split('}')[-1]

def _dimensions(value):
    try:
        numbers = tuple(map(float, value.replace(',', ' ').split()))
        if len(numbers) == 4 and all(map(math.isfinite, numbers)) and min(numbers[2:]) > 0:
            return list(numbers)
    except (ValueError, AttributeError):
        pass
    return None

def _properties(element):
    """Inspect both presentation attributes and inline CSS declarations."""
    for key, value in element.attrib.items():
        if key == 'style':
            for declaration in value.split(';'):
                if not declaration.strip():
                    continue
                if ':' not in declaration:
                    yield 'invalid-css', declaration
                else:
                    prop, content = declaration.split(':', 1)
                    yield prop.strip(), content.strip()
        else:
            yield local_name(key), value

def validate(svg_path, require_text=False, profile='portable'):
    if profile not in ('portable', 'illustrator-native'):
        raise ValueError('Unsupported profile: %s' % profile)
    path = Path(svg_path)
    result = dict(schema_version='2.0', file=str(path.resolve()), profile=profile,
                  status='FAIL', view_box=None, geometry_count=0, live_text_count=0,
                  stable_id_count=0, errors=[], warnings=[])
    errors = result['errors']
    try:
        raw = path.read_bytes()
        # Reject entity declarations before parsing; never expand external/internal DTDs.
        if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
            raise ValueError('DTD/entity declarations are not part of authored SVG.')
        document = ET.fromstring(raw)
    except (ValueError, OSError, ET.ParseError) as error:
        errors.append(str(error))
        return result
    elements = list(document.iter())
    identifiers = Counter(item.get('id') for item in elements if item.get('id'))
    resources = {item.get('id'): local_name(item.tag) for item in elements if item.get('id')}
    result['stable_id_count'] = len(identifiers)
    result['view_box'] = _dimensions(document.get('viewBox'))
    if local_name(document.tag) != 'svg' or result['view_box'] is None:
        errors.append('Expected an SVG root with a finite viewBox and positive width/height.')
    for identifier, count in identifiers.items():
        if count != 1:
            errors.append('ID occurs more than once: %s' % identifier)
    allowed = STRUCTURAL | DRAWABLE | (NATIVE if profile == 'illustrator-native' else set())
    for item in elements:
        kind = local_name(item.tag)
        label = '%s#%s' % (kind, item.get('id', '?'))
        if kind not in allowed:
            errors.append('Unaccepted node: ' + label)
        if kind in DRAWABLE or kind == 'text':
            counter = 'live_text_count' if kind == 'text' else 'geometry_count'
            result[counter] += 1
            if not item.get('id'):
                errors.append('Missing object ID: ' + label)
        if kind == 'path' and not item.get('d', '').strip():
            errors.append('Path has no commands: ' + label)
        if kind in ('polygon', 'polyline') and len(NUMBER.findall(item.get('points', ''))) < 4:
            errors.append('Point list is incomplete: ' + label)
        for prop, content in _properties(item):
            value = content.lower()
            if prop.lower().startswith('on') or prop.lower() in ('href', 'invalid-css'):
                errors.append('Unsupported attribute: %s.%s' % (label, prop))
            if any(token in value for token in ('base64,', 'data:image', '@import', 'expression(', '\\', '/*')):
                errors.append('Payload or escaped CSS is not accepted: ' + label)
            if re.search(r'(?<![a-z])(?:nan|inf)(?![a-z])', value):
                errors.append('Non-finite value: ' + label)
            if re.search(r'url\s*\(', value):
                reference = URI.fullmatch(content.strip())
                identifier = next((g for g in reference.groups() if g), None) if reference else None
                target_type = resources.get(identifier)
                valid_target = ((prop in ('fill', 'stroke') and target_type in PAINT) or
                                (prop == 'clip-path' and target_type == 'clipPath'))
                if profile != 'illustrator-native' or not valid_target:
                    errors.append('Unresolved or disallowed resource: %s.%s' % (label, prop))
    if not result['geometry_count']:
        errors.append('Drawing contains no vector objects.')
    if require_text and not result['live_text_count']:
        errors.append('This drawing requires editable text.')
    result['status'] = 'FAIL' if errors else 'PASS'
    return result

def main():
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument('--svg', type=Path, required=True)
    command.add_argument('--profile', default='portable', choices=('portable', 'illustrator-native'))
    command.add_argument('--require-text', action='store_true')
    command.add_argument('--report', type=Path)
    settings = command.parse_args()
    outcome = validate(settings.svg, settings.require_text, settings.profile)
    serialized = json.dumps(outcome, indent=2, ensure_ascii=False)
    if settings.report:
        settings.report.parent.mkdir(parents=True, exist_ok=True)
        settings.report.write_text(serialized + '\n', encoding='utf-8')
    print(serialized)
    return int(outcome['status'] != 'PASS')

if __name__ == '__main__':
    raise SystemExit(main())
