import argparse
from pathlib import Path

from gwtc.events import LOCALIZATION_KEYS
from gwtc.parse import parse_dir
from gwtc.source import DEFAULT_SOURCE_TYPE, SOURCE_TYPES

description = """Extract posterior samples for the GW localization
(ra, dec, luminosity distance) from the LVK data releases.

You must have previously downloaded the .h5 files for each event.

The extracted samples are stored in an output .hdf5 file.
"""

parser = argparse.ArgumentParser(
    description=description,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "directory", type=Path, help="Path to directory containing .h5 files with samples"
)
parser.add_argument(
    "-o",
    "--output-file",
    type=Path,
    default="gwtc_localizations.hdf5",
    help="Output file",
)

parser.add_argument(
    "--source",
    type=str,
    choices=SOURCE_TYPES,
    default=DEFAULT_SOURCE_TYPE,
    help="CBC source type",
)

parser.add_argument(
    "--write-snrs",
    action="store_true",
    help="Whether to write detector SNRs to output file",
)

parser.add_argument(
    "--write-skymap-stats",
    action="store_true",
    help="Whether to write stats from ligo.skymap to output file (if available)",
)

parser.add_argument(
    "-n",
    "--njobs",
    type=int,
    default=1,
    help="Number of jobs for parallel processing",
)


def main():
    args = parser.parse_args()
    dir = Path(args.directory)
    parse_dir(
        dir,
        args.output_file,
        LOCALIZATION_KEYS,
        source=args.source,
        njobs=args.njobs,
        write_snrs=args.write_snrs,
        write_skymap_stats=args.write_skymap_stats,
    )
