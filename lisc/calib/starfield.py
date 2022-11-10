#!/usr/bin/env python3
#
# LISC toolkit
# Star field processing
#
# Author : Alexandre Simoneau
#
# Created: March 2021
# Edited: April 2021

import numpy as np
import yaml
from astropy.table import Table
from scipy.optimize import curve_fit, leastsq

from .utils import glob_types, open_raw


def angular_mean(a):
    return np.arctan2(np.mean(np.sin(a)), np.mean(np.cos(a)))


def align(coords, params):
    theta, phi = coords
    Theta, Phi, beta = params

    a = np.array(
        [
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta),
        ]
    )
    k = np.array(
        [
            np.sin(Theta) * np.cos(Phi),
            np.sin(Theta) * np.sin(Phi),
            np.cos(Theta),
        ]
    )
    b = (
        np.cos(beta) * a
        + np.sin(beta) * np.cross(k, a.T).T
        + np.dot(k, a) * (1 - np.cos(beta)) * k[:, None]
    )

    phip = np.arctan2(b[1], b[0]) % (2 * np.pi)
    thetap = np.arctan2(np.sqrt(b[0] ** 2 + b[1] ** 2), b[2])

    return thetap, phip


def error(params, y, x):
    ans = align(x, params)

    return (np.sin(y[0]) * np.cos(y[1]) - np.sin(ans[0]) * np.cos(ans[1])) ** 2 + (
        np.sin(y[0]) * np.sin(y[1]) - np.sin(ans[0]) * np.sin(ans[1])
    ) ** 2


def radial(alt, b, c, d, e):
    return b * alt + c * alt**2 + d * alt**3 + e * alt**4


def starfield():
    with open("params") as f:
        params = yaml.safe_load(f)
    psize = params["pixel_size"] / 1000 * 2
    f = params["focal_length"]

    im = open_raw(glob_types("STARFIELD/starfield")[0])
    Ny, Nx = im.shape[:2]

    db = Table.read("STARFIELD/corr.fits")

    xc = db["field_x"] / 2 - Nx / 2
    yc = Ny / 2 - db["field_y"] / 2
    az = np.arctan2(-xc, yc)
    alt = np.arctan(psize * np.sqrt(xc**2 + yc**2) / f)
    theta = np.pi / 2 + np.deg2rad(db["index_dec"])
    phi = np.deg2rad(db["index_ra"])

    p = (np.pi / 2, angular_mean(phi) - np.pi / 2, theta.mean())
    theta_r, phi_r = align((theta, phi), p)

    p0, foo = leastsq(error, (0, 0, 0), args=((alt, az), (theta_r, phi_r)))
    theta2, phi2 = align((theta_r, phi_r), p0)

    p1, foo = curve_fit(radial, alt, theta2)
    p2, foo = curve_fit(radial, theta2, alt)

    x = np.arange(Nx, dtype=float) - Nx / 2 + 0.5
    y = Ny / 2 - np.arange(Ny, dtype=float) + 0.5
    xx, yy = np.meshgrid(x, y)
    r = np.sqrt(xx**2 + yy**2)
    r2 = radial(np.arctan(psize * r / f), *p1)

    np.save("geometry", r2)

    def write_line(f, *vals):
        f.write(", ".join(f"{val}" for val in vals) + "\n")

    with open("geometry_params.dat", "w") as fout:
        write_line(fout, "params", Nx, Ny, f, psize)
        write_line(fout, "angle", *p)
        write_line(fout, "angle", *p0)
        write_line(fout, "radial", *p1)
        write_line(fout, "inv_radial", *p2)
