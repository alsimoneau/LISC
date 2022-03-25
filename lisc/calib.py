#!/usr/bin/env python3
#
# LISC toolkit
# Image calibration
#
# Author : Alexandre Simoneau
#
# Created: March 2021
# Edited: April 2021

import os
from glob import glob

import click
import imageio
import numpy as np
import pandas as pd

from .utils import (
    correct_flat,
    correct_linearity,
    cosmicray_removal,
    exif_read,
    open_clipped,
    open_raw,
)


@click.command(name="calib")
@click.argument("cam_key")
@click.argument("images")
@click.argument("darks", nargs=-1)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["NPY", "TIF"], case_sensitive=False),
    default="NPY",
    help="Converted file format. (Default: NPY)",
)
@click.option(
    "-s",
    "--sigma",
    type=float,
    default=5,
    help="Standard deviation used for cosmicray filtering. (Default: 5)",
)
def CLI_calib(cam_key, images, darks, format, sigma):
    """Image calibration pipeline.

    CAM_KEY: Camera key for calibration. See the available options with `lisc
    list`.\n
    IMAGES: Image to convert. Altenatively, one can process multiple images by
    passing a string containing a wildcard.\n
    DARKS: Dark images to use for calibration.
    """
    calib(
        cam_key,
        glob(os.path.expanduser(images)),
        darks,
        fmt=format.lower(),
        sigclip=sigma,
    )
    print("Done.")


def calib(cam_key, images, darks, fmt="npy", sigclip=5):
    if fmt not in ["npy", "tif"]:
        print(f"ERROR: Unrecognized format '{fmt}'")
        return

    datadir = os.path.expanduser(f"~/.LISC/{cam_key}/")
    lin_data = pd.read_csv(datadir + "linearity.csv")
    flat_data = np.load(datadir + "flatfield.npy")
    dark = open_clipped(darks)
    photo = np.loadtxt(datadir + "photometry.dat")

    new_names = []
    for fname in images:
        print(f"Calibrating '{fname}'...")
        data = (
            correct_flat(
                correct_linearity(
                    cosmicray_removal(open_raw(fname) - dark, sigclip=sigclip),
                    lin_data,
                ),
                flat_data,
            )
            * (photo / exif_read(fname)["ShutterSpeedValue"])
        )

        new_name = fname.rsplit(".", 1)[0]
        if fmt == "npy":
            np.save(new_name, data)
        elif fmt == "tif":
            imageio.imsave(new_name + ".tif", data)

        new_names.append(f"{new_name}.{fmt}")
    return new_names
