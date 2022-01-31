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
import numpy as np
import pandas as pd
from progressbar import progressbar

from .utils import blur_image, exif_read, glob_types, open_clipped, open_raw


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
        int(fname.split(os.sep)[-1].split("_")[0])
        for fname in glob("LINEARITY/*.*")
    }

    Ny, Nx = open_raw(glob_types("LINEARITY/*")[0]).shape[:2]
    mask = np.zeros((Ny, Nx), dtype=np.bool8)
    mask[
        Ny // 2 - size : Ny // 2 + size + 1,
        Nx // 2 - size : Nx // 2 + size + 1,
    ] = True

    data = []
    for ss in progressbar(sorted(set_times), redirect_stdout=True):
        frame = open_clipped(f"LINEARITY/{ss}_*")
        dark = blur_image(open_clipped(f"LINEARITY/DARKS/{ss}_*"))
        exif = exif_read(glob_types(f"LINEARITY/{ss}_*")[0])
        data.append((exif["ShutterSpeedValue"], *(frame - dark)[mask].mean(0)))

    df = pd.DataFrame(data, columns=["Exposure", "R", "G", "B"])
    df.to_csv("linearity.csv")
