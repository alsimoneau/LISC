#!/usr/bin/env python3
#
# LISC toolkit
# Stellar photometry processing
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
import rawpy
import requests
import yaml
from progressbar import progressbar
from scipy.ndimage import gaussian_filter

from .utils import *


@click.command(name="photo")
@click.option("-r", "--radius", type=float, default=50)
@click.option("-w", "--drift-window", type=int, default=200)
def CLI_photometry(radius, drift_window):
    """Process frames for stellar photometry calibration.

    Integrates the stellar flux using a disk of radius RADIUS pixels.
    The star used is identified by it's ID in the Yale Bright Star Catalog.
    """

    photometry(r=radius, drift_window=drift_window)
    print("Done.")


# TODO: Use astrometry for star identification


def photometry(r=50, drift_window=200):
    with open("PHOTOMETRY/photometry.params") as f:
        p = yaml.safe_load(f)
    star_id = p["star_id"]
    initial = p["star_position"]
    aod = p["aod"]
    alpha = p["alpha"]
    theta = np.deg2rad(p["theta"])
    alt = p["altitude"]
    alt_aod = p["altitude_aod"]
    alt_p = p["altitude_pressure"]
    press = p["pressure"]
    r /= 2
    drift_window /= 2

    lin_data = pd.read_csv("linearity.csv")
    flat_data = np.load("flatfield.npy")

    dark = open_clipped("PHOTOMETRY/DARKS/*")

    idx, idy = initial
    idx /= 2
    idy /= 2
    outs = pd.DataFrame(
        columns=[
            "Filename",
            "SAT",
            "X",
            "Y",
            "R",
            "G",
            "B",
            "sR",
            "sG",
            "sB",
            "bR",
            "bG",
            "bB",
        ]
    )

    for fname in progressbar(
        sorted(glob_types(f"PHOTOMETRY/*")), redirect_stdout=True
    ):
        im = sub(open_raw(fname), dark)

        crop = im[
            idy - drift_window : idy + drift_window,
            idx - drift_window : idx + drift_window,
        ]

        blurred = gaussian_filter(crop.mean(2), 10, mode="constant")
        y, x = np.where(blurred == blurred.max())

        idx += x[0] - drift_window
        idy += y[0] - drift_window
        print(f"Found star at: {idx*2}, {idy*2}")

        star_mask = circle_mask(idx, idy, im.shape, r)
        bgnd_mask = circle_mask(idx, idy, im.shape, 2 * r) & ~circle_mask(
            idx, idy, im.shape, 1.5 * r
        )

        sat = (im[star_mask] > 60000).any()
        im = correct_flat(correct_linearity(im, lin_data), flat_data)

        star = np.sum(im[star_mask], 0)
        bgnd = np.sum(im[bgnd_mask], 0) * np.sum(star_mask) / np.sum(bgnd_mask)

        rad = star - bgnd

        outs.loc[len(outs)] = [
            fname[len("PHOTOMETRY/") :],
            sat,
            idx,
            idy,
            *rad,
            *star,
            *bgnd,
        ]

    exp = exif_read(glob_types("PHOTOMETRY/*")[0])["ShutterSpeedValue"]

    with open("star_spectrum.dat", "wb") as f:
        f.write(
            requests.get(
                f"http://nartex.fis.ucm.es/~ncl/rgbphot/asciisingle/hr{star_id:04}.txt"
            ).content
        )

    wls, star = np.loadtxt("star_spectrum.dat").T
    wls /= 10  # A -> nm
    star *= 1e-2  # ergs / s / cm^2 / A -> W / m^2 / nm

    Tm_exp = np.exp(
        -(press / 101.3)
        / ((wls / 1000) ** 4 * 115.6406 - (wls / 1000) ** 2 * 1.335)
    )
    Tm_inf = Tm_exp ** (1 / np.exp(-alt_p / 8000))
    Tm = Tm_inf ** (np.exp(-alt / 8000) / np.cos(theta))

    Ta_exp = np.exp(-aod * (wls / 500) ** (-alpha))
    Ta_inf = Ta_exp ** (1 / np.exp(-alt_aod / 2000))
    Ta = Ta_inf ** (np.exp(-alt / 2000) / np.cos(theta))

    with open("photometry.dat", "w"):
        pass

    for band in "RGB":
        dat = outs[band][~outs["SAT"].astype(bool)].to_numpy() / exp
        val = np.mean(dat[np.abs(dat - np.mean(dat)) < np.std(dat)])

        wlc, cam = np.loadtxt(f"{band}.spct").T
        cam /= np.max(cam)  # max => 1
        cam_interp = np.interp(wls, wlc, cam)

        flux = np.trapz(Tm * Ta * star * cam_interp, wls)

        with open("photometry.dat", "a") as f:
            f.write(f"{flux/val}\n")

        outs[band] = flux / (outs[band] / exp)
    outs.to_csv("photometry.csv")
