#!/usr/bin/env python3
#
# LISC toolkit
# Stellar photometry processing
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: February 2021

import click

@click.command(name="photometry")
def CLI_photometry():
    """Process frames for stellar photometry calibration.
    """
    photometry()

def photometry():
    pass
