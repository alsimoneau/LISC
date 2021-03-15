#!/usr/bin/env python3
#
# LISC toolkit
# Flat field processing
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: March 2021

import click
import numpy as np
from glob import glob
import os
from scipy.ndimage import gaussian_filter
from utils import open_clipped, open_raw, sub

@click.command(name="flatfield")
def CLI_flatfield():
    """Process frames for flat field calibration.
    """
    flatfield()
    print("Done.")

def flatfield():
    offset = (6000 - 1320*4) / 31
    radius = 5 #degrees
    blur_radius = 1

    def shift(arr,x,y):
        arr = np.roll(arr, x, 1)
        if x>0:
            arr[:,:x] = 0
        else:
            arr[:,x:] = 0
        arr = np.roll(arr, -y, 0)
        if y<0:
            arr[:-y] = 0
        else:
            arr[-y:] = 0
        return arr

    dark = open_clipped("FLATFIELD/DARKS/*")
    light = np.zeros_like(dark, dtype=np.float64)
    count = np.zeros(dark.shape[:2],dtype=np.float64)

    fov = np.rad2deg( np.load(f"geometry.npy") )
    circle = fov < radius
    pixsixe = fov[0,fov.shape[1]//2] / (fov.shape[0]/2)
    blur = gaussian_filter(circle.astype(float),blur_radius/pixsixe)

    for fname in glob("FLATFIELD/*.arw"):
        foo, el, az = os.path.splitext(os.path.basename(fname))[0].split('_')
        el, az = float(el), float(az)-offset
        r = el/pixsixe
        x = int(round(r * np.sin(np.deg2rad(az))))
        y = -int(round(r * np.cos(np.deg2rad(az))))

        shifted = shift(blur,x,y)
        frame = sub(open_raw(fname),dark)

        count += shifted
        light += frame*shifted[...,None]

    light /= count[...,None]

    np.save("flatfield",light)
    np.save("flat_weight",count)
