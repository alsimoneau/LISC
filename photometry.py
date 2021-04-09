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
from utils import *
import requests

@click.command(name="photo")
@click.argument("id",type=int,required=True)
@click.argument("radius",type=float,default=10)
@click.option('-i',"--initial",type=(float,float),help="Initial star position in pixels. (X,Y)")
@click.option('-d',"--drift_window",type=float,default=16,help="Size of the window to look for the star each frame. Used to compensate for drift due to earth's rotation. (Default: 16)")
@click.option('-z',"--theta",type=float,required=True,help="Zenith angle of the star")
@click.option('-t',"--aod",type=float,required=True,help="Aerosol optical depth. Obtained from AERONET station.")
@click.option('-a',"--alpha",type=float,required=True,help="Angstrom coefficient. Obtained from AERONET station.")
@click.option('-p',"--pressure",type=float,default=101.3,help="Air pressure. (Default: 1atm)")
@click.option('-h',"--alt",type=float,default=0,help="Altitude of the measurement site. (Default: 0m)")
@click.option('--alt_aod',type=float,required=False,help="Altitude of the AERONET station used. (Default: alt)")
@click.option("--alt_p",type=float,required=False,help="Altitude of the site where the pressure was measured. (Default: alt)")
def CLI_photometry(radius,id,initial,drift_window,aod,alpha,theta,pressure,alt,alt_aod,alt_p):
    """Process frames for stellar photometry calibration.

    Integrates the stellar flux using a disk of radius RADIUS pixels.
    The star used is identified by it's ID in the Yale Bright Star Catalog.
    """
    photometry(
        r=radius,
        star_id=id,
        initial=initial,
        drift_window=drift_window,
        aod=aod,
        alpha=alpha,
        theta=theta,
        alt=alt,
        alt_aod=alt_aod,
        alt_p=alt_p,
        press=pressure
    )
    print("Done.")

# TODO: Use astrometry for star identification
def photometry(r=10,initial=(2390,1642),drift_window=16,star_id=8819,
    aod=0.074,alpha=0.978,theta=58.,alt=319,alt_aod=251,alt_p=241,press=99.3):
    lin_data = pd.read_csv("linearity.csv")
    flat_data = np.load("flatfield.npy")

    dark = open_clipped("PHOTOMETRY/DARKS/*")

    idx,idy = initial
    outs = pd.DataFrame(columns=["Filename","SAT","X","Y","R","G","B","sR","sG","sB","bR","bG","bB"])
    for i,fname in enumerate(sorted(glob_types(f"PHOTOMETRY/*"))):
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

        outs.loc[i] = [
            fname[len("PHOTOMETRY/"):],
            (im[star_mask] > 60000).any(),
            idx, idy,
            *rad, *star, *bgnd
        ]

    outs.to_csv("photometry.csv")
    outs = pd.read_csv("photometry.csv")

    with exiftool.ExifTool() as et:
        exif = et.get_metadata(glob_types("PHOTOMETRY/*")[0])
    exp = float(exif['MakerNotes:SonyExposureTime2'])

    with open("star_spectrum.dat",'wb') as f:
        f.write(requests.get(f"http://nartex.fis.ucm.es/~ncl/rgbphot/asciisingle/hr{star_id:04}.txt").content)

    wls,star = np.loadtxt("star_spectrum.dat").T
    wls /= 10 # A -> nm
    star *= 1e-2 # ergs / s / cm^2 / A -> W / m^2 / nm

    Tm = np.exp( -(press/101.3) / ( (wls/1000)**4 * 115.6406 - (wls/1000)**2 * 1.335) )
    Tm_inf = Tm ** ( np.exp( -(alt-alt_p)/2000 ) / np.cos(theta) )

    Ta = np.exp( -aod * (wls/500)**(-alpha) )
    Ta_inf = Ta ** ( np.exp( -(alt-alt_aod)/2000 ) / np.cos(theta) )

    with open("photometry.dat",'w'):
        pass

    for band in "RGB":
        dat = outs[band][~outs['SAT']].to_numpy() / exp
        val = np.mean(dat[ np.abs(dat - np.mean(dat)) < np.std(dat) ])

        wlc,cam = np.loadtxt(f"{band}.spct").T
        cam /= np.max(cam) # max => 1
        cam_interp = np.interp(wls,wlc,cam)

        flux = np.trapz(Tm_inf*Ta_inf*star*cam_interp,wls)

        with open("photometry.dat",'a') as f:
            f.write(f"{flux/val}\n")
