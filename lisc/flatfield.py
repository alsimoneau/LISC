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
import yaml
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
    offset = (6000 - 1442 * 4) * 3 / 31
    radius = 5  # degrees
    blur_radius = 1

    lin_data = pd.read_csv("linearity.csv")

    def shift(arr, x, y):
        arr = np.roll(arr, x, 1)
        if x > 0:
            arr[:, :x] = 0
        else:
            arr[:, x:] = 0
        arr = np.roll(arr, y, 0)
        if y > 0:
            arr[:y] = 0
        else:
            arr[y:] = 0
        return arr

    dark = blur_image(open_clipped("FLATFIELD/DARKS/*"))

    if os.path.isfile("geometry.npy"):
        fov = np.load("geometry.npy")
    else:
        with open("params") as f:
            params = yaml.safe_load(f)
        psize = params["pixel_size"] / 1000 * 2
        f = params["focal_length"]

        Ny, Nx = dark.shape[:2]
        x = np.arange(Nx, dtype=float) - Nx / 2 + 0.5
        y = Ny / 2 - np.arange(Ny, dtype=float) + 0.5
        xx, yy = np.meshgrid(x, y)
        r = np.sqrt(xx ** 2 + yy ** 2)
        fov = np.arctan(psize * r / f)

    fov = np.rad2deg(fov)
    circle = fov < radius
    pixsixe = fov[0, fov.shape[1] // 2] / (fov.shape[0] / 2)
    blur = gaussian_filter(circle.astype(float), blur_radius / pixsixe)

    @parallelize
    def process(fname, count, light):
        foo, el, az = os.path.splitext(os.path.basename(fname))[0].split("_")
        el, az = float(el), -float(az) - offset
        r = el / pixsixe
        x = int(round(r * np.cos(np.deg2rad(az))))
        y = int(round(r * np.sin(np.deg2rad(az))))

        shifted = shift(blur, x, y)
        frame = correct_linearity(open_raw(fname) - dark, lin_data)
        # frame = open_raw(fname) - dark

        count += shifted
        light += frame * shifted[..., None]

    count = np.zeros(dark.shape[:2], dtype=np.float64)
    light = np.zeros_like(dark, dtype=np.float64)
    process(glob_types("FLATFIELD/*"), count, light)
    light /= count[..., None]
    flat = blur_image(light)

    np.save("flatfield", flat)
    np.save("flat_weight", count)
