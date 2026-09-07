#!/usr/bin/env python3
"""Deterministically build the independently authored SVS phase-one asset library."""
import json
from pathlib import Path

from asset_definitions import extended_assets

ROOT = Path(__file__).resolve().parents[1] / "assets" / "scientific-library"


def svg(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 240 180">'
            '<title>Scientific Vector Studio editable asset</title>' + body + '</svg>\n')


def entry(asset_id, zh, en, aliases, category, parts, anchors, parameters=None, views=None):
    return {
        "id": asset_id, "name_zh": zh, "name_en": en, "aliases": aliases,
        "category": category, "file": f"{category}/{asset_id}.svg",
        "views": views or ["front"], "editable_parts": parts,
        "parameters": parameters or ["fill_colors", "stroke_color", "uniform_scale", "rotation"],
        "connection_anchors": anchors, "illustrator_verified": False,
        "powerpoint_verified": False, "review_status": "candidate"
    }


ASSETS = [
    (entry("arrow-straight", "直箭头", "Straight arrow", ["arrow", "connector", "直线箭头"], "arrows",
           ["arrow-straight-shaft", "arrow-straight-head"], {"start": [25, 90], "end": [218, 90]}),
     svg('<line id="arrow-straight-shaft" x1="25" y1="90" x2="188" y2="90" fill="none" stroke="#176B78" stroke-width="7" stroke-linecap="round"/>'
         '<polygon id="arrow-straight-head" points="184,69 218,90 184,111" fill="#176B78"/>')),
    (entry("arrow-curved", "曲线箭头", "Curved arrow", ["curved arrow", "弧形箭头", "curve connector"], "arrows",
           ["arrow-curved-shaft", "arrow-curved-head"], {"start": [28, 136], "end": [216, 62]}),
     svg('<path id="arrow-curved-shaft" d="M28 136 C62 40 150 28 193 59" fill="none" stroke="#1683A5" stroke-width="7" stroke-linecap="round"/>'
         '<polygon id="arrow-curved-head" points="187,40 216,62 181,71" fill="#1683A5"/>')),
    (entry("arrow-bidirectional", "双向箭头", "Bidirectional arrow", ["double arrow", "reversible", "双箭头"], "arrows",
           ["arrow-bidirectional-shaft", "arrow-bidirectional-left", "arrow-bidirectional-right"], {"left": [18, 90], "right": [222, 90]}),
     svg('<line id="arrow-bidirectional-shaft" x1="48" y1="90" x2="192" y2="90" fill="none" stroke="#376C78" stroke-width="7" stroke-linecap="round"/>'
         '<polygon id="arrow-bidirectional-left" points="52,67 18,90 52,113" fill="#376C78"/>'
         '<polygon id="arrow-bidirectional-right" points="188,67 222,90 188,113" fill="#376C78"/>')),
    (entry("connector-inhibition", "抑制线", "Inhibition connector", ["inhibition", "T bar", "抑制箭头"], "arrows",
           ["connector-inhibition-shaft", "connector-inhibition-bar"], {"start": [24, 90], "end": [207, 90]}),
     svg('<line id="connector-inhibition-shaft" x1="25" y1="90" x2="205" y2="90" fill="none" stroke="#B54A55" stroke-width="7" stroke-linecap="round"/>'
         '<line id="connector-inhibition-bar" x1="207" y1="61" x2="207" y2="119" fill="none" stroke="#B54A55" stroke-width="9" stroke-linecap="round"/>')),
    (entry("arrow-dashed", "虚线箭头", "Dashed arrow", ["dashed connector", "虚线", "dotted arrow"], "arrows",
           ["arrow-dashed-shaft", "arrow-dashed-head"], {"start": [25, 90], "end": [218, 90]}),
     svg('<line id="arrow-dashed-shaft" x1="25" y1="90" x2="187" y2="90" fill="none" stroke="#65747A" stroke-width="7" stroke-linecap="round" stroke-dasharray="15 13"/>'
         '<polygon id="arrow-dashed-head" points="183,69 218,90 183,111" fill="#65747A"/>')),
    (entry("arrow-cyclic", "循环箭头", "Cyclic arrow", ["cycle", "loop arrow", "回环箭头"], "arrows",
           ["arrow-cyclic-shaft", "arrow-cyclic-head"], {"start": [71, 139], "end": [204, 68]}),
     svg('<path id="arrow-cyclic-shaft" d="M71 139 A70 70 0 1 1 191 76" fill="none" stroke="#3A8F71" stroke-width="7" stroke-linecap="round"/>'
         '<polygon id="arrow-cyclic-head" points="172,71 204,68 192,99" fill="#3A8F71"/>')),
    (entry("beaker", "烧杯", "Beaker", ["beaker", "玻璃烧杯", "实验烧杯"], "labware",
           ["beaker-glass", "beaker-rim", "beaker-liquid", "beaker-graduations"], {"top": [120, 30], "bottom": [120, 162], "left": [69, 96], "right": [176, 96]},
           ["glass_color", "liquid_color", "liquid_opacity", "uniform_scale"]),
     svg('<path id="beaker-glass" d="M69 34 L78 152 Q79 161 89 162 H157 Q166 161 168 152 L176 35" fill="#DDF3F8" fill-opacity="0.48" stroke="#4E91A5" stroke-width="3" stroke-linejoin="round"/>'
         '<path id="beaker-liquid" d="M75 101 Q121 92 172 101 L168 152 Q167 158 157 159 H89 Q82 158 81 151 Z" fill="#42B9DB" fill-opacity="0.72" stroke="#2A9DBF" stroke-width="2"/>'
         '<path id="beaker-rim" d="M65 35 Q109 28 157 32 Q169 35 184 26 Q180 41 162 44 H84 Q72 44 65 35 Z" fill="#F7FCFD" stroke="#4E91A5" stroke-width="3" stroke-linejoin="round"/>'
         '<path id="beaker-highlight" d="M89 50 L94 90" fill="none" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round" opacity="0.72"/>'
         '<path id="beaker-graduations" d="M142 65 H165 M149 83 H165 M142 101 H165 M149 120 H165 M142 139 H165" fill="none" stroke="#407E91" stroke-width="2" opacity="0.75"/>')),
    (entry("erlenmeyer-flask", "锥形瓶", "Erlenmeyer flask", ["conical flask", "三角瓶", "Erlenmeyer"], "labware",
           ["flask-body", "flask-neck", "flask-liquid", "flask-rim"], {"top": [120, 20], "bottom": [120, 160], "left": [45, 130], "right": [195, 130]},
           ["glass_color", "liquid_color", "liquid_opacity", "uniform_scale"]),
     svg('<path id="flask-body" d="M95 25 L92 82 L45 144 Q40 153 51 157 Q120 167 189 157 Q201 153 194 143 L148 82 L145 25 Z" fill="#E2F4F7" fill-opacity="0.5" stroke="#4E91A5" stroke-width="3" stroke-linejoin="round"/>'
         '<path id="flask-neck" d="M95 25 L92 82 M145 25 L148 82" fill="none" stroke="#4E91A5" stroke-width="3"/>'
         '<path id="flask-liquid" d="M66 123 Q118 111 175 123 L193 146 Q198 153 187 156 Q120 164 53 156 Q43 153 48 146 Z" fill="#65C6A8" fill-opacity="0.8" stroke="#3AA184" stroke-width="2"/>'
         '<ellipse id="flask-rim" cx="120" cy="25" rx="28" ry="7" fill="#F8FDFD" stroke="#4E91A5" stroke-width="3"/>'
         '<path id="flask-highlight" d="M70 132 Q83 100 103 79" fill="none" stroke="#FFFFFF" stroke-width="7" stroke-linecap="round" opacity="0.7"/>')),
    (entry("test-tube", "试管", "Test tube", ["test tube", "试管", "culture tube"], "labware",
           ["test-tube-body", "test-tube-liquid", "test-tube-rim"], {"top": [120, 20], "bottom": [120, 164], "left": [87, 90], "right": [153, 90]},
           ["glass_color", "liquid_color", "liquid_opacity", "uniform_scale"]),
     svg('<path id="test-tube-body" d="M88 27 H152 V128 A32 32 0 0 1 88 128 Z" fill="#E5F5F8" fill-opacity="0.5" stroke="#4E91A5" stroke-width="3"/>'
         '<path id="test-tube-liquid" d="M92 91 Q120 84 148 91 V128 A28 28 0 0 1 92 128 Z" fill="#D77CB0" fill-opacity="0.78" stroke="#BC5D96" stroke-width="2"/>'
         '<ellipse id="test-tube-rim" cx="120" cy="27" rx="36" ry="9" fill="#F9FDFD" stroke="#4E91A5" stroke-width="3"/>'
         '<path id="test-tube-highlight" d="M101 45 V78" fill="none" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round" opacity="0.75"/>')),
    (entry("conical-tube", "锥形离心管", "Conical centrifuge tube", ["Falcon tube", "centrifuge tube", "离心管"], "labware",
           ["conical-cap", "conical-body", "conical-liquid", "conical-graduations"], {"top": [120, 16], "bottom": [120, 166], "left": [78, 82], "right": [162, 82]},
           ["cap_color", "glass_color", "liquid_color", "uniform_scale"]),
     svg('<path id="conical-body" d="M82 45 H158 L153 124 L127 162 Q120 170 113 162 L87 124 Z" fill="#E5F4F7" fill-opacity="0.55" stroke="#4E91A5" stroke-width="3" stroke-linejoin="round"/>'
         '<path id="conical-liquid" d="M89 91 Q120 84 155 91 L152 123 L127 159 Q120 166 114 159 L89 123 Z" fill="#F0B65A" fill-opacity="0.78" stroke="#D79A3B" stroke-width="2"/>'
         '<rect id="conical-cap" x="76" y="17" width="88" height="31" rx="6" fill="#4B9DB2" stroke="#34798B" stroke-width="3"/>'
         '<path id="conical-cap-ribs" d="M87 20 V45 M99 20 V45 M111 20 V45 M123 20 V45 M135 20 V45 M147 20 V45 M159 23 V42" fill="none" stroke="#A9D9E4" stroke-width="2"/>'
         '<path id="conical-graduations" d="M127 62 H151 M135 76 H151 M127 91 H151 M135 106 H152 M127 121 H152" fill="none" stroke="#477F8B" stroke-width="2" opacity="0.75"/>')),
    (entry("petri-dish", "培养皿", "Petri dish", ["Petri", "culture dish", "平皿"], "labware",
           ["petri-lid", "petri-base", "petri-agar", "petri-colonies"], {"top": [120, 48], "bottom": [120, 132], "left": [36, 92], "right": [204, 92]},
           ["glass_color", "agar_color", "colony_color", "uniform_scale"]),
     svg('<path id="petri-base" d="M39 85 V118 Q42 139 120 145 Q198 139 201 118 V85" fill="#DDF2F5" fill-opacity="0.58" stroke="#528FA0" stroke-width="3"/>'
         '<ellipse id="petri-agar" cx="120" cy="105" rx="76" ry="30" fill="#F1C97D" fill-opacity="0.72" stroke="#D0A34B" stroke-width="2"/>'
         '<ellipse id="petri-lid" cx="120" cy="72" rx="86" ry="34" fill="#EAF8FA" fill-opacity="0.45" stroke="#528FA0" stroke-width="3"/>'
         '<path id="petri-lid-side" d="M34 72 V89 Q38 112 120 118 Q202 112 206 89 V72" fill="none" stroke="#528FA0" stroke-width="3" opacity="0.72"/>'
         '<g id="petri-colonies"><circle id="petri-colony-1" cx="87" cy="98" r="8" fill="#D87583"/><circle id="petri-colony-2" cx="128" cy="111" r="6" fill="#D87583"/><circle id="petri-colony-3" cx="157" cy="94" r="10" fill="#D87583"/><circle id="petri-colony-4" cx="111" cy="87" r="5" fill="#D87583"/></g>')),
    (entry("micropipette", "移液器", "Micropipette", ["pipette", "移液枪", "single channel pipette"], "labware",
           ["pipette-plunger", "pipette-body", "pipette-display", "pipette-shaft", "pipette-tip"], {"top": [120, 7], "bottom": [120, 174], "grip": [120, 65]},
           ["body_color", "accent_color", "tip_color", "uniform_scale", "rotation"], ["front"]),
     svg('<rect id="pipette-plunger" x="94" y="7" width="52" height="14" rx="7" fill="#2E5260" stroke="#1D3A45" stroke-width="3"/>'
         '<rect id="pipette-plunger-stem" x="111" y="19" width="18" height="18" rx="5" fill="#7897A1" stroke="#355762" stroke-width="3"/>'
         '<path id="pipette-body" d="M91 35 Q91 27 101 27 H139 Q149 27 149 35 V78 Q149 89 137 99 L131 106 H109 L103 99 Q91 89 91 78 Z" fill="#EEF4F5" stroke="#355762" stroke-width="3" stroke-linejoin="round"/>'
         '<path id="pipette-grip" d="M92 43 H148 V68 Q120 78 92 68 Z" fill="#48AFC2" stroke="#2E8698" stroke-width="2"/>'
         '<rect id="pipette-display" x="106" y="48" width="28" height="16" rx="3" fill="#233E47" stroke="#152C33" stroke-width="2"/>'
         '<rect id="pipette-ejector" x="149" y="45" width="15" height="23" rx="6" fill="#F0B759" stroke="#9B7130" stroke-width="3"/>'
         '<rect id="pipette-collar" x="103" y="101" width="34" height="16" rx="6" fill="#5A7882" stroke="#355762" stroke-width="3"/>'
         '<path id="pipette-shaft" d="M110 116 H130 L127 150 H113 Z" fill="#B9CDD2" stroke="#526E77" stroke-width="3"/>'
         '<path id="pipette-tip" d="M114 149 H126 L122 174 H118 Z" fill="#E4F7FA" stroke="#5B9AAA" stroke-width="2"/>'
         '<path id="pipette-highlight" d="M101 34 V72" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" opacity="0.7"/>')),
    (entry("compound-microscope", "复式显微镜", "Compound microscope", ["microscope", "显微镜", "light microscope"], "instruments",
           ["microscope-base", "microscope-arm", "microscope-stage", "microscope-eyepiece", "microscope-objectives", "microscope-focus"], {"top": [84, 16], "bottom": [120, 164], "sample": [113, 106]},
           ["body_color", "accent_color", "uniform_scale"], ["side"]),
     svg('<path id="microscope-base" d="M42 145 Q44 132 61 129 H150 Q174 134 193 151 L181 164 H55 Q42 162 42 145 Z" fill="#DCE9EC" stroke="#34545F" stroke-width="3"/>'
         '<path id="microscope-arm" d="M145 48 Q187 65 187 103 Q187 133 158 149 L138 128 Q159 116 159 96 Q159 74 132 67 Z" fill="#72B0BD" stroke="#34545F" stroke-width="3" stroke-linejoin="round"/>'
         '<path id="microscope-eyepiece" d="M54 25 L91 15 L100 31 L64 43 Z" fill="#294A55" stroke="#1C3540" stroke-width="3"/>'
         '<path id="microscope-eyepiece-tube" d="M69 37 L94 29 L105 43 L82 51 Z" fill="#9DBBC2" stroke="#34545F" stroke-width="3"/>'
         '<path id="microscope-head" d="M78 39 L126 47 L135 67 L116 81 L76 58 Z" fill="#EDF3F4" stroke="#34545F" stroke-width="3"/>'
         '<ellipse id="microscope-nosepiece" cx="117" cy="80" rx="28" ry="10" fill="#385963" stroke="#213D46" stroke-width="3"/>'
         '<g id="microscope-objectives"><path id="microscope-objective-1" d="M94 83 L105 86 L99 108 L87 104 Z" fill="#D8E4E7" stroke="#34545F" stroke-width="2"/><path id="microscope-objective-2" d="M113 88 H126 L125 112 H112 Z" fill="#D8E4E7" stroke="#34545F" stroke-width="2"/><path id="microscope-objective-3" d="M133 85 L144 81 L152 103 L140 108 Z" fill="#D8E4E7" stroke="#34545F" stroke-width="2"/></g>'
         '<path id="microscope-stage" d="M66 108 H157 L166 119 H62 Z" fill="#38535D" stroke="#213C45" stroke-width="3" stroke-linejoin="round"/>'
         '<line id="microscope-stage-clip" x1="94" y1="104" x2="135" y2="104" stroke="#E8C35F" stroke-width="4" stroke-linecap="round"/>'
         '<g id="microscope-focus"><circle id="microscope-focus-large" cx="164" cy="76" r="15" fill="#4B93A2" stroke="#34545F" stroke-width="3"/><circle id="microscope-focus-small" cx="164" cy="76" r="7" fill="#C7E2E7" stroke="#34545F" stroke-width="2"/></g>'
         '<path id="microscope-condenser" d="M100 120 H136 L130 135 H106 Z" fill="#9CBAC1" stroke="#496A74" stroke-width="2"/>'
         '<ellipse id="microscope-light" cx="118" cy="145" rx="20" ry="8" fill="#F4D47C" stroke="#8F772F" stroke-width="2"/>')),
    (entry("benchtop-centrifuge", "台式离心机", "Benchtop centrifuge", ["centrifuge", "microcentrifuge", "离心机"], "instruments",
           ["centrifuge-body", "centrifuge-lid", "centrifuge-rotor", "centrifuge-display", "centrifuge-controls"], {"top": [120, 9], "bottom": [120, 163], "front": [120, 145]},
           ["body_color", "accent_color", "display_color", "uniform_scale"]),
     svg('<path id="centrifuge-lid" d="M57 61 Q60 20 94 10 H146 Q180 20 183 61 L169 68 Q120 44 71 68 Z" fill="#B6D8DE" stroke="#34545F" stroke-width="3"/>'
         '<ellipse id="centrifuge-lid-window" cx="120" cy="43" rx="43" ry="22" fill="#E7F2F4" stroke="#6E9DA7" stroke-width="2"/>'
         '<rect id="centrifuge-hinge" x="95" y="58" width="50" height="13" rx="5" fill="#526F79" stroke="#34545F" stroke-width="2"/>'
         '<path id="centrifuge-body" d="M38 76 Q39 63 55 60 H185 Q201 63 202 76 L195 151 Q194 162 182 163 H58 Q46 162 45 151 Z" fill="#E7EFF1" stroke="#34545F" stroke-width="3"/>'
         '<ellipse id="centrifuge-chamber" cx="120" cy="78" rx="66" ry="31" fill="#7896A0" stroke="#34545F" stroke-width="3"/>'
         '<ellipse id="centrifuge-rotor" cx="120" cy="78" rx="48" ry="23" fill="#2F4D57" stroke="#1E3942" stroke-width="3"/>'
         '<circle id="centrifuge-hub" cx="120" cy="78" r="9" fill="#A8C9D0" stroke="#496B75" stroke-width="2"/>'
         '<g id="centrifuge-wells"><ellipse id="centrifuge-well-1" cx="91" cy="70" rx="7" ry="6" fill="#D5EEF2"/><ellipse id="centrifuge-well-2" cx="111" cy="62" rx="7" ry="6" fill="#D5EEF2"/><ellipse id="centrifuge-well-3" cx="137" cy="64" rx="7" ry="6" fill="#D5EEF2"/><ellipse id="centrifuge-well-4" cx="149" cy="79" rx="7" ry="6" fill="#D5EEF2"/><ellipse id="centrifuge-well-5" cx="133" cy="94" rx="7" ry="6" fill="#D5EEF2"/><ellipse id="centrifuge-well-6" cx="105" cy="93" rx="7" ry="6" fill="#D5EEF2"/><ellipse id="centrifuge-well-7" cx="88" cy="83" rx="7" ry="6" fill="#D5EEF2"/></g>'
         '<rect id="centrifuge-panel" x="61" y="113" width="118" height="34" rx="8" fill="#C8D8DC" stroke="#607981" stroke-width="2"/>'
         '<rect id="centrifuge-display" x="73" y="121" width="55" height="18" rx="3" fill="#213E47" stroke="#132C34" stroke-width="2"/>'
         '<g id="centrifuge-controls"><circle id="centrifuge-start" cx="148" cy="130" r="8" fill="#4BB092" stroke="#2B7763" stroke-width="2"/><circle id="centrifuge-stop" cx="169" cy="130" r="8" fill="#E77F70" stroke="#A94D42" stroke-width="2"/></g>')),
    (entry("pcr-thermocycler", "PCR扩增仪", "PCR thermocycler", ["PCR machine", "thermal cycler", "PCR仪"], "instruments",
           ["pcr-body", "pcr-lid", "pcr-hinge", "pcr-block", "pcr-display", "pcr-controls"], {"top": [120, 10], "bottom": [120, 162], "sample": [120, 89]},
           ["body_color", "lid_color", "accent_color", "display_color", "uniform_scale"]),
     svg('<path id="pcr-lid" d="M69 61 L76 18 Q77 10 87 10 H166 Q176 10 177 19 L184 61 Z" fill="#6EA7B3" stroke="#35545F" stroke-width="3"/>'
         '<path id="pcr-heated-plate" d="M91 49 L95 25 H158 L162 49 Z" fill="#D7E3E6" stroke="#5C7881" stroke-width="2"/>'
         '<path id="pcr-lid-handle" d="M101 18 Q126 8 151 18" fill="none" stroke="#35545F" stroke-width="5" stroke-linecap="round"/>'
         '<rect id="pcr-hinge" x="93" y="55" width="55" height="14" rx="4" fill="#526F79" stroke="#35545F" stroke-width="2"/>'
         '<path id="pcr-body" d="M38 87 L58 62 H182 L202 87 L190 159 Q189 163 183 163 H57 Q51 163 50 159 Z" fill="#E8EFF1" stroke="#35545F" stroke-width="3" stroke-linejoin="round"/>'
         '<path id="pcr-block" d="M57 84 L75 67 H165 L183 84 L168 108 H72 Z" fill="#BBCED3" stroke="#58737C" stroke-width="2"/>'
         '<g id="pcr-wells"><circle id="pcr-well-1" cx="91" cy="77" r="4" fill="#4B7884"/><circle id="pcr-well-2" cx="110" cy="77" r="4" fill="#4B7884"/><circle id="pcr-well-3" cx="129" cy="77" r="4" fill="#4B7884"/><circle id="pcr-well-4" cx="148" cy="77" r="4" fill="#4B7884"/><circle id="pcr-well-5" cx="91" cy="89" r="4" fill="#4B7884"/><circle id="pcr-well-6" cx="110" cy="89" r="4" fill="#4B7884"/><circle id="pcr-well-7" cx="129" cy="89" r="4" fill="#4B7884"/><circle id="pcr-well-8" cx="148" cy="89" r="4" fill="#4B7884"/><circle id="pcr-well-9" cx="91" cy="101" r="4" fill="#4B7884"/><circle id="pcr-well-10" cx="110" cy="101" r="4" fill="#4B7884"/><circle id="pcr-well-11" cx="129" cy="101" r="4" fill="#4B7884"/><circle id="pcr-well-12" cx="148" cy="101" r="4" fill="#4B7884"/></g>'
         '<path id="pcr-front-panel" d="M59 119 H181 L176 151 H64 Z" fill="#CAD9DD" stroke="#607981" stroke-width="2"/>'
         '<rect id="pcr-display" x="72" y="126" width="62" height="18" rx="3" fill="#213E47" stroke="#132C34" stroke-width="2"/>'
         '<g id="pcr-controls"><circle id="pcr-control-1" cx="151" cy="130" r="5" fill="#DCE8EA" stroke="#56737C" stroke-width="2"/><circle id="pcr-control-2" cx="167" cy="130" r="5" fill="#DCE8EA" stroke="#56737C" stroke-width="2"/><circle id="pcr-control-3" cx="151" cy="143" r="5" fill="#4CB092" stroke="#2B7763" stroke-width="2"/><circle id="pcr-control-4" cx="167" cy="143" r="5" fill="#E77F70" stroke="#A94D42" stroke-width="2"/></g>')),
]

ASSETS.extend(extended_assets(entry, svg))


def main():
    for item, content in ASSETS:
        destination = ROOT / item["file"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    manifest = {
        "schema_version": "1.0", "library_name": "SVS Scientific Core Library",
        "provenance": "Independently authored generic scientific vectors; no vendor or third-party artwork.",
        "base_view_box": [0, 0, 240, 180], "asset_count": len(ASSETS),
        "assets": [item for item, _ in ASSETS]
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "asset_count": len(ASSETS), "library": str(ROOT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
