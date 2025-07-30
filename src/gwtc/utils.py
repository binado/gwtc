import os
import re
from pathlib import Path
from typing import Union


def dir_exists_or_create(dirname: Union[str, Path]):
    if not Path(dirname).is_dir():
        os.makedirs(dirname)


def get_gw_event_from_filename(url: Union[str, Path]):
    # Regex pattern to match 'GW' followed by 6 digits, an underscore, and another 6 digits
    pattern = r"GW\d{6}_\d{6}"

    # Use re.search to find the pattern in the string
    match = re.search(pattern, str(url))
    return match.group(0) if match else ""


def clean_outfile_name(outfile: str, suffix: str) -> str:
    return str(Path(outfile).with_suffix(suffix))
