#!/usr/bin/env python3
#
# LISC toolkit
# Stellar photometry processing
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: April 2021

import click
import numpy as np
import pandas as pd
import rawpy
from glob import glob
import os
import exiftool
from .utils import *
import yaml
import requests
from progressbar import progressbar

@click.command(name="photo")
@click.option("-r","--radius",type=float,default=10)
@click.option("-w","--drift-window",type=int,default=16)
def CLI_photometry(radius,drift_window):
    """Process frames for stellar photometry calibration.

    Integrates the stellar flux using a disk of radius RADIUS pixels.
    The star used is identified by it's ID in the Yale Bright Star Catalog.
    """

    photometry(
        r=radius,
        drift_window=drift_window
    )
    print("Done.")

# TODO: Use astrometry for star identification
def photometry(r=10,drift_window=16):
    with open("PHOTOMETRY/photometry.params") as f:
        p = yaml.safe_load(f)
    star_id=p["star_id"]
    initial=p["star_position"]
    aod=p["aod"]
    alpha=p["alpha"]
    theta=p["theta"]
    alt=p["altitude"]
    alt_aod=p["altitude_aod"]
    alt_p=p["altitude_pressure"]
    press=p["pressure"]

    lin_data = pd.read_csv("linearity.csv")
    flat_data = np.load("flatfield.npy")

    dark = open_clipped("PHOTOMETRY/DARKS/*")

    idx,idy = initial
    outs = pd.DataFrame(columns=["Filename","SAT","X","Y","R","G","B","sR","sG","sB","bR","bG","bB"])


    for fname in progressbar(sorted(glob_types(f"PHOTOMETRY/*")),redirect_stdout=True):
        im = correct_flat(correct_linearity(sub(open_raw(fname), dark),lin_data),flat_data)
        crop = im[idy-drift_window:idy+drift_window,idx-drift_window:idx+drift_window]
        y,x = np.where( np.sum(crop,2) == np.max(np.sum(crop,2)) )
        idx += x[0] - drift_window
        idy += y[0] - drift_window
        print(f"Found star at: {idx}, {idy}")

        star_mask = circle_mask(idx,idy,im.shape,r)
        star = np.sum(im[star_mask],0)
        bgnd_mask = circle_mask(idx,idy,im.shape,2*r) \
            & ~circle_mask(idx,idy,im.shape,1.5*r)
        bgnd = np.sum(im[bgnd_mask],0) * np.sum(star_mask) / np.sum(bgnd_mask)

        rad = star - bgnd

        outs.loc[len(outs)] = [
            fname[len("PHOTOMETRY/"):],
            (im[star_mask] > 60000).any(),
            idx, idy,
            *rad, *star, *bgnd
        ]

    outs.to_csv("photometry.csv")
    outs = pd.read_csv("photometry.csv")

    exp = exif_read(glob_types("PHOTOMETRY/*")[0])['ShutterSpeedValue']

    with open("star_spectrum.dat",'wb') as f:
        f.write(requests.get(f"http://nartex.fis.ucm.es/~ncl/rgbphot/asciisingle/hr{star_id:04}.txt").content)

    wls,star = np.loadtxt("star_spectrum.dat").T
    wls /= 10 # A -> nm
    star *= 1e-2 # ergs / s / cm^2 / A -> W / m^2 / nm

    Tm_inf = np.exp( -(press/101.3) / ( (wls/1000)**4 * 115.6406 - (wls/1000)**2 * 1.335) )
    Tm = Tm_inf ** ( np.exp( -(alt-alt_p)/8000 ) / np.cos(theta) )

    Ta_aod = np.exp( -aod * (wls/500)**(-alpha) )
    Ta_inf = Ta_aod ** ( -np.exp( -alt_aod/2000 ) )
    Ta = Ta_inf ** ( np.exp( -alt/2000 ) / np.cos(theta) )

    with open("photometry.dat",'w'):
        pass

    for band in "RGB":
        dat = outs[band][~outs['SAT']].to_numpy() / exp
        val = np.mean(dat[ np.abs(dat - np.mean(dat)) < np.std(dat) ])

        wlc,cam = np.loadtxt(f"{band}.spct").T
        cam /= np.max(cam) # max => 1
        cam_interp = np.interp(wls,wlc,cam)

        flux = np.trapz(Tm*Ta*star*cam_interp,wls)

        with open("photometry.dat",'a') as f:
            f.write(f"{flux/val}\n")
