#!/usr/bin/env python3
#
# LISC toolkit
# Linearity processing
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: April 2021

import os
from glob import glob

import click
import exiftool
import numpy as np
import pandas as pd
import yaml
from progressbar import progressbar

from .utils import glob_types
from .utils import open_clipped as Open
from .utils import sub


@click.command(name="lin")
@click.option(
    "-s",
    "--size",
    type=int,
    default=50,
    help="Size of the window to process. (Default: 50)",
)
def CLI_linearity(size):
    """Process frames for linearity calibration."""
    linearity(size)
    print("Done.")


def linearity(size=50):
    size //= 2
    set_times = {
        int(fname.split(os.sep)[-1].split("_")[0]) for fname in glob("LINEARITY/*.*")
    }

    with open("params") as f:
        params = yaml.safe_load(f)
    Nx = params["width"] // 2
    Ny = params["height"] // 2
    mask = np.zeros((Ny, Nx), dtype=np.bool8)
    mask[
        Ny // 2 - size : Ny // 2 + size + 1, Nx // 2 - size : Nx // 2 + size + 1
    ] = True

    data = []
    for ss in progressbar(sorted(set_times), redirect_stdout=True):
        frame = Open(f"LINEARITY/{ss}_*")
        with exiftool.ExifTool() as et:
            exif = et.get_metadata(glob_types(f"LINEARITY/{ss}_*")[0])
        exp = exif["MakerNotes:SonyExposureTime2"]
        dark = Open(f"LINEARITY/DARKS/{ss}_*")
        frame = sub(frame, dark)

        print(exp, *frame[mask].mean(0))
        data.append((exp, *frame[mask].mean(0)))

    pd.DataFrame(data, columns=["Exposure", "R", "G", "B"]).to_csv("linearity.csv")
