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


def lowtran(wls, pressure, altitude, altitude_pressure):
    Tm_exp = np.exp(
        -(pressure / 101.3) / ((wls / 1000) ** 4 * 115.6406)
        - (wls / 1000) ** 2 * 1.335
    )
    Tm_inf = Tm_exp ** np.exp(altitude_pressure / 8000)
    return Tm_inf ** np.exp(-altitude / 8000)


def bodhaine(wls, pressure, altitude, altitude_pressure, CO2, latitude):
    pressure *= (1 - 0.0065 * (altitude - altitude_pressure) / 288.15) ** (
        (-9.80665 * 0.0289644) / (8.3144598 * -0.0065)
    )

    FO2 = 1.096 + 1.385e-3 * wls ** -2 + 1.448e-4 * wls ** -4
    FN2 = 1.034 + 3.17e-4 * wls ** -2
    Fair = (78.084 * FN2 + 20.946 * FO2 + 0.934 * 1.00 + CO2 * 1.15) / (
        78.084 + 20.946 + 0.934 + CO2
    )
    n300m1 = 1e-8 * (
        8060.51
        + 2480990 / (132.274 - (wls / 1e3) ** -2)
        + 17455.7 / (39.32957 - (wls / 1e3) ** -2)
    )  # lambda in um
    nCO2 = 1 + (n300m1 * (1 + 0.54 * (CO2 / 1e6 - 0.0003)))
    Ns = N_A / 22.4141 * 273.15 / 288.15 * 1e-3  # mol/cm^3
    sig = (
        (24 * np.pi ** 3 * (nCO2 ** 2 - 1) ** 2)
        / ((wls / 1e7) ** 4 * Ns ** 2 * (nCO2 ** 2 + 2) ** 2)
        * ((6 + 3 * Fair) / (6 - 7 * Fair))
    )  # lambda in cm

    gasses = np.array(
        [
            (78.084, 28.013),  # N2ROD
            (20.946, 31.999),  # O2
            (0.934, 39.948),  # Ar
            (1.80e-3, 20.18),  # Ne
            (5.20e-4, 4.003),  # He
            (1.10e-4, 83.8),  # Kr
            (5.80e-5, 2.016),  # H2
            (9.00e-6, 131.29),  # Xe
            (100 * CO2 / 1e6, 44.01),  # CO2
        ]
    )
    ma = np.dot(*gasses.T) / np.sum(gasses[:, 0])

    c2l = np.cos(2 * np.deg2rad(latitude))
    z = 0.73737 * altitude + 5517.56
    g = (
        (980.6160 * (1 - 2.6373e-3 * c2l + 5.9e-6 * c2l ** 2))
        - (3.085462e-4 + 2.27e-7 * c2l) * z
        + (7.254e-11 + 1.0e-13 * c2l) * z ** 2
        - (1.517e-17 + 6e-20 * c2l) * z ** 3
    )  # cm/s^2

    rod = sig * ((pressure * 1e4) * N_A) / (ma * g)  # kPa -> dyn/cm^2

    return np.exp(-rod)


def photometry(r=50, drift_window=200):
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

    Tm_exp = lowtran(wls, p["pressure"], p["altitude"], p["altitude_pressure"])
    Tm = Tm_exp ** np.exp(1 / np.cos(np.deg2rad(p["theta"])))

    Ta_exp = np.exp(-p["aod"] * (wls / 500) ** (-p["alpha"]))
    Ta_inf = Ta_exp ** (1 / np.exp(-p["altitude_aod"] / 2000))
    Ta = Ta_inf ** (
        np.exp(-p["altitude"] / 2000) / np.cos(np.deg2rad(p["theta"]))
    )

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
