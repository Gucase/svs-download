"""Independently authored phase-two SVS asset definitions."""
from .biology import assets as biology_assets
from .instruments import assets as instrument_assets
from .labware import assets as labware_assets
from .medical import assets as medical_assets


def extended_assets(entry, svg):
    return (labware_assets(entry, svg) + instrument_assets(entry, svg) +
            biology_assets(entry, svg) + medical_assets(entry, svg))
