#!/usr/bin/env python3
#
# LISC toolkit
# Flat field processing
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
from scipy.ndimage import gaussian_filter

from .utils import correct_linearity, open_raw


@click.command(name="flat")
def CLI_flatfield():
    """Process frames for flat field calibration."""
    flatfield()
    print("Done.")


# TODO: Add parameters to CLI
# TODO: Generalize
def flatfield():
    offset = (6000 - 1320 * 4) / 31
    radius = 5  # degrees
    blur_radius = 1

    lin_data = pd.read_csv("linearity.csv")

    def shift(arr, x, y):
        arr = np.roll(arr, x, 1)
        if x > 0:
            arr[:, :x] = 0
        else:
            arr[:, x:] = 0
        arr = np.roll(arr, -y, 0)
        if y < 0:
            arr[:-y] = 0
        else:
            arr[-y:] = 0
        return arr

    dark = open_clipped("FLATFIELD/DARKS/*")
    light = np.zeros_like(dark, dtype=np.float64)
    count = np.zeros(dark.shape[:2], dtype=np.float64)

    fov = np.rad2deg(np.load(f"geometry.npy"))
    circle = fov < radius
    pixsixe = fov[0, fov.shape[1] // 2] / (fov.shape[0] / 2)
    blur = gaussian_filter(circle.astype(float), blur_radius / pixsixe)

    for fname in progressbar(glob_types("FLATFIELD/*"), redirect_stdout=True):
        foo, el, az = os.path.splitext(os.path.basename(fname))[0].split("_")
        el, az = float(el), float(az) - offset
        r = el / pixsixe
        x = int(round(r * np.sin(np.deg2rad(az))))
        y = -int(round(r * np.cos(np.deg2rad(az))))

        shifted = shift(blur, x, y)
        frame = correct_linearity(open_raw(fname) - dark, lin_data)

        count += shifted
        light += frame * shifted[..., None]

    light /= count[..., None]

    np.save("flatfield", light)
    np.save("flat_weight", count)
