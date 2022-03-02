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

from .utils import (
    blur_image,
    exif_read,
    glob_types,
    open_clipped,
    open_raw,
    parallelize,
)


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

    images = glob_types("LINEARITY/*_*")
    darks = glob_types("LINEARITY/DARKS/*_*")

    def filter_fnames(fnames, ss):
        return [f for f in fnames if os.path.basename(f).startswith(f"{ss}_")]

    @parallelize
    def process(ss):
        images_names = filter_fnames(images, ss)
        darks_names = filter_fnames(darks, ss)
        frame = open_clipped(images_names)[mask]
        dark = blur_image(open_clipped(darks_names))[mask]
        exif = exif_read(images_names[0])
        return (exif["ShutterSpeedValue"], *(frame - dark).mean(0))

    data = process(sorted(set_times))

    df = pd.DataFrame(data, columns=["Exposure", "R", "G", "B"])
    df.to_csv("linearity.csv")
