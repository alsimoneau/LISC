#!/usr/bin/env python3
#
# LISC toolkit
# Stellar photometry processing
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: March 2021

import click
import numpy as np
import pandas as pd
import rawpy
from glob import glob
import os
import exiftool
from utils import *
import requests

@click.command(name="photo")
def CLI_photometry():
    """Process frames for stellar photometry calibration.
    """
    photometry()
    print("Done.")

def photometry(r=10,initial=(2390,1642),drift_window=16,star_id=8819):
    if not os.path.isfile("photometry.csv"):
        dark = open_clipped("PHOTOMETRY/DARKS/*")

        idx,idy = initial
        outs = pd.DataFrame(columns=["Filename","SAT","X","Y","R","G","B","sR","sG","sB","bR","bG","bB"])
        for i,fname in enumerate(sorted(glob_types(f"PHOTOMETRY/*"))):
            im = sub(open_raw(fname), dark)
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

            outs.loc[i] = [
                fname[len("PHOTOMETRY/"):],
                (im[star_mask] > 60000).any(),
                idx, idy,
                *rad, *star, *bgnd
            ]

        outs.to_csv("photometry.csv")

    outs = pd.read_csv("photometry.csv")

    with open("star_spectrum.dat",'wb') as f:
        f.write(requests.get(f"http://nartex.fis.ucm.es/~ncl/rgbphot/asciisingle/hr{star_id:04}.txt").content)

    wls,star = np.loadtxt("star_spectrum.dat").T
    wls /= 10 # A -> nm
    star *= 1e-3 # ergs / s / cm^2 -> W / m^2

    for band in "RGB":
        dat = outs[band][~outs['SAT']].to_numpy()
        val = np.mean(dat[ np.abs(dat - np.mean(dat)) < np.std(dat) ])

        wlc,cam = np.loadtxt(f"{band}.spct").T
        cam /= np.max(cam) # max => 1
        cam_interp = np.interp(wls,wlc,cam)

        flux = np.trapz(star*cam_interp,wls)

        print(band,flux/val)
