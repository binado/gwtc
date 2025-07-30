import argparse
import logging
from pathlib import Path

import h5py

from gwtc.parse import get_maximum_likelihood_data, iterate_dir, read_event_file
from gwtc.utils import clean_outfile_name

description = """Extract posterior samples for the GW localization
(ra, dec, luminosity distance) from the LVK data releases.

You must have previously downloaded the .h5 files for each event.

The extracted samples are stored in an output directory in .zarr format.
"""

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    "get_maximum_likelihood_values",
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
    "--write-source",
    action="store_true",
    help="Whether to store classification of CBC based on approximants used for the analysis",
)


parser.add_argument(
    "--write-detectors",
    action="store_true",
    help="Whether to write per-event online detector network for each event",
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


def _get_maximum_likelihood_data_on_input(args):
    event_path, _, kwargs = args
    _, data = read_event_file(event_path)
    return get_maximum_likelihood_data(data, **kwargs)


def main():
    args = parser.parse_args()
    kwargs = {
        "write_source": args.write_source,
        "write_detectors": args.write_detectors,
        "write_skymap_stats": args.write_skymap_stats,
    }
    event_names, res = iterate_dir(
        args.directory,
        _get_maximum_likelihood_data_on_input,
        njobs=args.njobs,
        **kwargs,
    )
    outfile_name = clean_outfile_name(args.output_file, ".hdf5")
    with h5py.File(outfile_name, mode="w") as f:
        for event_name, (maxl_dict, event_kwargs) in zip(event_names, res):
            event_group = f.create_group(event_name)
            labels = list(maxl_dict.keys())
            event_group.attrs["labels"] = labels
            for k, v in event_kwargs.items():
                event_group.attrs[k] = v
            for label, maxl_dict_per_label in maxl_dict.items():
                label_group = event_group.create_group(label)
                for parameter, data in maxl_dict_per_label.items():
                    label_group.create_dataset(parameter, data=data)
