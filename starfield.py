#!/usr/bin/env python3
#
# LISC toolkit
# Star field processing
#
# Author : Alexandre Simoneau
#
# Created: March 2021
# Edited: March 2021

import click
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, leastsq
import yaml
from utils import cycle_mod

@click.command(name="starfield")
def CLI_starfield():
    """Process frames for star field calibration.
    """
    starfield()
    print("Done.")

def starfield():
    with open("config.ini") as f:
        config = yaml.safe_load(f)
    psize = config['pixel size'] / 1000
    Nx, Ny = config['resolution']
    f = config['focal lenght']

    def align(coords,params):
        theta,phi = coords
        Theta,Phi,beta = params

        a = np.array([ np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta) ])
        k = np.array([ np.sin(Theta)*np.cos(Phi), np.sin(Theta)*np.sin(Phi), np.cos(Theta) ])

        b = np.cos(beta) * a + np.sin(beta)*np.cross(k,a.T).T + np.dot(k,a)*(1-np.cos(beta))*k[:,None]

        phip = np.arctan2( b[1], b[0] ) % (2*np.pi)
        thetap = np.arctan2( np.sqrt( b[0]**2 + b[1]**2 ), b[2] )

        return thetap,phip

    def error(params,y,x):
        ans = align(x,params)
        return np.sin(y[1]) * (cycle_mod(y[0] - ans[0]))**2 + cycle_mod(y[1] - ans[1])**2

    def radial(alt,b,c,d,e):
        return b * alt + c * alt**2 + d * alt**3 + e * alt**4

    db = pd.read_csv("STARFIELD/starfield.csv")

    xc = db['X'].to_numpy() - Nx/2
    yc = Ny/2 - db['Y'].to_numpy()
    az = np.pi - np.arctan2(-xc,-yc)
    alt = np.arctan( psize * np.sqrt(xc**2 + yc**2) / f )
    theta = np.pi/2 - np.deg2rad(db['ALT'])
    phi = np.deg2rad(db['AZ'])

    p0,foo = leastsq( error, (1,1,1), args=((alt,az),(theta,phi)))
    theta2,phi2 = align((theta,phi),p0)

    p1,foo = curve_fit( radial, alt, theta2 )
    alt2 = radial(alt, *p1)

    x = np.arange(Nx,dtype=float) - Nx/2
    y = Ny/2 - np.arange(Ny,dtype=float)
    xx,yy = np.meshgrid(x,y)
    r = np.sqrt( xx**2 + yy**2 )
    r2 = radial( np.arctan( psize * r / f ), *p1 )
    err = np.sqrt( error( p0, (alt2,az), (theta,phi) ) )

    np.save("geometry",r2)
