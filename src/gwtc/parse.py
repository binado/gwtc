import logging
import multiprocessing
from pathlib import Path
from typing import Callable, Iterable, Optional, Union

import h5py
import pesummary.io
from pesummary.gw.file.formats.pesummary import PESummary

from gwtc.source import (
    DEFAULT_SOURCE_TYPE,
    SourceTypes,
    check_source,
    infer_source_type,
)
from gwtc.utils import (
    clean_outfile_name,
    get_gw_event_from_filename,
)

# Set up logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def get_detectors_from_pesummary_file(data: PESummary) -> list[str]:
    detectors = set()
    detectors_per_label = data.detectors
    for detector_list in detectors_per_label:
        if all([isinstance(det, str) for det in detector_list]):
            detectors.update(*detector_list)
    return list(detectors)


def get_skymap_stats_from_pesummary_file(data: PESummary) -> dict[str, float]:
    skymap_stats = {}
    for k, extra_kwargs in zip(data.labels, data.extra_kwargs):
        skymap_stats[k] = {}
        if "other" not in extra_kwargs:
            continue
        for label in ("area50", "area90"):
            if label in extra_kwargs["other"]:
                skymap_stats[k][label] = extra_kwargs["other"][label]
    return skymap_stats


def get_maximum_likelihood_data(
    data: PESummary,
    write_source: bool = True,
    write_detectors: bool = True,
    write_skymap_stats: bool = True,
):
    maxl_data = {k: data.samples_dict[k].maxL for k in data.samples_dict}
    kwargs = {}
    if write_source:
        source = infer_source_type(data, raise_exception=False)
        kwargs["source_type"] = source
    if write_detectors:
        detectors = get_detectors_from_pesummary_file(data)
        kwargs["detectors"] = detectors
    if write_skymap_stats:
        skymap_stats = get_skymap_stats_from_pesummary_file(data)
        kwargs.update(skymap_stats)
    return maxl_data, kwargs


def parse_event_data(
    data: PESummary,
    output_group: h5py.Group,
    keys: Iterable[str],
    write_snrs: bool = True,
    write_skymap_stats: bool = True,
) -> None:
    for analysis, detectors, kwargs in zip(
        data.labels, data.detectors, data.extra_kwargs
    ):
        has_detectors = all([detector is not None for detector in detectors])
        samples = data.samples_dict[analysis]
        analysis_group = output_group.create_group(analysis)
        analysis_group.attrs["nsamples"] = samples.number_of_samples
        analysis_group.attrs["detectors"] = detectors if has_detectors else []
        if write_skymap_stats:
            skymap_kwargs = kwargs.get("other")
            if skymap_kwargs is not None and "area90" in skymap_kwargs:
                analysis_group.attrs["area90"] = float(skymap_kwargs["area90"])
        snr_keys = []
        if write_snrs and has_detectors:
            for detector in detectors:
                snr_keys += [
                    f"{detector}_optimal_snr",
                    f"{detector}_matched_filter_snr",
                    f"{detector}_matched_filter_abs_snr",
                ]
        _keys = list(keys) + snr_keys
        for key in _keys:
            try:
                dataset = samples[key]
                analysis_group.create_dataset(key, data=dataset)
            except KeyError:
                logger.info(
                    "Unable to get key %s for analysis %s in event %s",
                    key,
                    analysis,
                    output_group.name,
                )


def read_event_file(event_path: Union[str, Path]) -> tuple[str, PESummary]:
    event_filename = str(event_path)
    event_name = get_gw_event_from_filename(event_filename)
    logger.info("Processing event %s", event_name)
    return event_name, pesummary.io.read(event_filename, package="gw")


def parse_event_file(
    event_path: Path,
    keys: Iterable[str],
    source: SourceTypes = DEFAULT_SOURCE_TYPE,
    write_snrs: bool = True,
    write_skymap_stats: bool = True,
) -> Optional[str]:
    event_name, data = read_event_file(event_path)
    event_source, is_correct_source = check_source(data, source, raise_exception=False)
    if event_source is None:
        logger.info("Could not infer source type for event %s", event_name)
    else:
        logger.info("Event %s inferred source type: %s", event_name, event_source)
    if not is_correct_source:
        logger.info("Event %s does not match source type %s", event_name, source)
        return None
    output_file = clean_outfile_name(event_name, ".hdf5")
    with h5py.File(output_file, mode="w") as f:
        if event_source is not None:
            f.attrs["source_type"] = event_source
        parse_event_data(
            data,
            f,
            keys,
            write_snrs=write_snrs,
            write_skymap_stats=write_skymap_stats,
        )
    return output_file


def _parse_event_file_single_input(args) -> Optional[str]:
    event_path, keys, kwargs = args
    return parse_event_file(event_path, keys, **kwargs)


def iterate_dir(input_dir: Path, fn: Callable, *args, njobs: int = 1, **kwargs):
    if not input_dir.is_dir():
        raise ValueError(f"dir argument {dir} is not a directory")
    use_multiprocessing = njobs > 1
    logger.info("Using multiple processes: %s", use_multiprocessing)
    event_names = list(map(get_gw_event_from_filename, input_dir.iterdir()))
    args_iterable = [(event_path, args, kwargs) for event_path in input_dir.iterdir()]
    if use_multiprocessing:
        with multiprocessing.Pool(processes=njobs) as p:
            res = p.map(fn, args_iterable)
    else:
        res = list(map(fn, args_iterable))
    return event_names, res


def parse_dir(
    input_dir: Path,
    output_file: str,
    keys: Iterable[str],
    source: SourceTypes = DEFAULT_SOURCE_TYPE,
    njobs: int = 1,
    write_snrs: bool = True,
    write_skymap_stats: bool = True,
):
    kwargs = {
        "source": source,
        "write_snrs": write_snrs,
        "write_skymap_stats": write_skymap_stats,
    }
    event_names, parsed_filenames = iterate_dir(
        input_dir, _parse_event_file_single_input, keys, njobs=njobs, **kwargs
    )
    outfile_name = clean_outfile_name(output_file, ".hdf5")
    with h5py.File(outfile_name, mode="w") as f:
        for event_name, input_filename in zip(event_names, parsed_filenames):
            if input_filename is None:
                logger.info("Skipping writing event %s to output file", event_name)
                continue

            with h5py.File(input_filename, mode="r") as input_file:
                input_file.copy(input_file.name, f, event_name)
