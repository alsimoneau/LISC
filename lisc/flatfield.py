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

import click
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

from .utils import (
    blur_image,
    correct_linearity,
    glob_types,
    open_clipped,
    open_raw,
    parallelize,
)


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

    dark = blur_image(open_clipped("FLATFIELD/DARKS/*"))

    fov = np.rad2deg(np.load("geometry.npy"))
    circle = fov < radius
    pixsixe = fov[0, fov.shape[1] // 2] / (fov.shape[0] / 2)
    blur = gaussian_filter(circle.astype(float), blur_radius / pixsixe)

    @parallelize
    def process(fname, count, light):
        foo, el, az = os.path.splitext(os.path.basename(fname))[0].split("_")
        el, az = float(el), float(az) - offset
        r = el / pixsixe
        x = int(round(r * np.sin(np.deg2rad(az))))
        y = -int(round(r * np.cos(np.deg2rad(az))))

        shifted = shift(blur, x, y)
        frame = correct_linearity(open_raw(fname) - dark, lin_data)

        count += shifted
        light += frame * shifted[..., None]

    count = np.zeros(dark.shape[:2], dtype=np.float64)
    light = np.zeros_like(dark, dtype=np.float64)
    process(glob_types("FLATFIELD/*"), count, light)
    light /= count[..., None]
    flat = blur_image(light)

    np.save("flatfield", flat)
    np.save("flat_weight", count)
