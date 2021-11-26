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
from os.path import basename

import click
import numpy as np
import pandas as pd
import requests
import yaml
from progressbar import progressbar
from scipy.constants import N_A
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


def lowtran(wls):
    """Railegh molecular optical depth from eq.30 of Kneizys (1980).
    Expects wls in µm."""
    return 1 / ((wls ** 4 * 115.6406) - wls ** 2 * 1.335)


def aeronet(wls):
    """Railegh molecular optical depth from eq.30 of Bodhaide (1999).
    Expects wls in µm."""
    return (
        0.0021520
        * (1.0455996 - 341.29061 * wls ** (-2) - 0.90230850 * wls ** 2)
        / (1 + 0.0027059889 * wls ** (-2) - 85.968563 * wls ** 2)
    )


def photometry(r=50, drift_window=50):
    with open("PHOTOMETRY/photometry.params") as f:
        p = yaml.safe_load(f)
    r /= 2
    drift_window //= 2

    lin_data = pd.read_csv("linearity.csv")
    flat_data = np.load("flatfield.npy")

    dark = open_clipped("PHOTOMETRY/DARKS/*")

    idx, idy = p["star_position"]
    idx //= 2
    idy //= 2
    outs = pd.DataFrame(columns=["Filename", "SAT", "X", "Y", "R", "G", "B"])

    n = 0
    for fname in progressbar(
        sorted(glob_types(f"PHOTOMETRY/*")), redirect_stdout=True
    ):
        im = open_raw(fname)

        crop = im[
            idy - drift_window : idy + drift_window,
            idx - drift_window : idx + drift_window,
        ]

        blurred = gaussian_filter(crop.mean(2), 10, mode="constant")
        y, x = np.where(blurred == blurred.max())

        if (x[0] - drift_window) ** 2 + (y[0] - drift_window) ** 2 > 10 ** 2:
            print("Large drift detected, check images for clouds")
            n += 1
            if n >= 5:
                break
        else:
            n = 0

        idx += x[0] - drift_window
        idy += y[0] - drift_window
        print(f"Found star at: {idx*2}, {idy*2}")

        star_mask = circle_mask(idx, idy, im.shape, r)
        bgnd_mask = circle_mask(idx, idy, im.shape, 2 * r) & ~circle_mask(
            idx, idy, im.shape, 1.5 * r
        )

        sat = (im[star_mask] > 0.95).any()
        im = correct_flat(correct_linearity(im - dark, lin_data), flat_data)
        rad = np.sum(im[star_mask], 0) - (
            np.sum(im[bgnd_mask], 0) * (np.sum(star_mask) / np.sum(bgnd_mask))
        )

        outs.loc[len(outs)] = [basename(fname), sat, idx, idy, *rad]

    exp = exif_read(glob_types("PHOTOMETRY/*")[0])["ShutterSpeedValue"]

    with open("star_spectrum.dat", "wb") as f:
        f.write(
            requests.get(
                "http://nartex.fis.ucm.es/~ncl/rgbphot/asciisingle/"
                f"hr{p['star_id']:04}.txt"
            ).content
        )

    wls, star = np.loadtxt("star_spectrum.dat").T
    wls /= 10  # A -> nm
    star *= 1e-2  # ergs / s / cm^2 / A -> W / m^2 / nm

    cost = np.cos(np.deg2rad(p["theta"]))

    Tm_exp = np.exp(-p["pressure"] / 101.325 * aeronet(wls / 1000))  # in µm
    Tm_inf = Tm_exp ** (1 / np.exp(-p["altitude_pressure"] / 8000))
    Tm = Tm_inf ** (np.exp(-p["altitude"] / 8000) / cost)

    Ta_exp = np.exp(-p["aod"] * (wls / 500) ** (-p["alpha"]))
    Ta_inf = Ta_exp ** (1 / np.exp(-p["altitude_aod"] / 2000))
    Ta = Ta_inf ** (np.exp(-p["altitude"] / 2000) / cost)

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
