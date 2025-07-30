import logging
from typing import Literal, Optional

from pesummary.gw.file.formats.pesummary import PESummary

SOURCE_TYPES = ("ALL", "BBH", "NSBH", "BNS")
DEFAULT_SOURCE_TYPE = "ALL"

SourceTypes = Literal["ALL", "BBH", "NSBH", "BNS"]
BBH_WAVEFORMS = {"Mixed", "IMRPhenomXPHM", "SEOBNRv4PHM"}
BNS_WAVEFORMS = {"IMRPhenomPv2_NRTidal:HighSpin", "IMRPhenomPv2_NRTidal:LowSpin"}
NSBH_WAVEFORMS = {
    "IMRPhenomNSBH:HighSpin",
    "IMRPhenomNSBH:LowSpin",
    "IMRPhenomXPHM:HighSpin",
    "IMRPhenomXPHM:LowSpin",
    "Mixed",
    "Mixed:NSBH:HighSpin",
    "Mixed:NSBH:LowSpin",
    "SEOBNRv4PHM",
    "SEOBNRv4_ROM_NRTidalv2_NSBH:HighSpin",
    "SEOBNRv4_ROM_NRTidalv2_NSBH:LowSpin",
}
ALL_WAVEFORMS = {*BBH_WAVEFORMS, *BNS_WAVEFORMS, *NSBH_WAVEFORMS}

WAVEFORMS_PER_SOURCE = [
    ("BBH", BBH_WAVEFORMS),
    ("BNS", BNS_WAVEFORMS),
    ("NSBH", NSBH_WAVEFORMS),
]

logger = logging.getLogger(__name__)


def label_to_approximant(label: str) -> str:
    return label.lstrip("C01:")


def approximant_to_label(approximant: str) -> str:
    return "C01:" + approximant


def infer_source_type(data: PESummary, raise_exception: bool = False) -> Optional[str]:
    for source, waveforms in WAVEFORMS_PER_SOURCE:
        if all([label_to_approximant(label) in waveforms for label in data.labels]):
            return source

    if raise_exception:
        raise ValueError("Source could not be detected")

    return None


def check_source(
    data: PESummary,
    source: SourceTypes = DEFAULT_SOURCE_TYPE,
    raise_exception: bool = False,
) -> tuple[Optional[str], bool]:
    event_source = infer_source_type(data, raise_exception=raise_exception)
    is_correct_source = source is None or source in {event_source, DEFAULT_SOURCE_TYPE}
    return event_source, is_correct_source
