#!/usr/bin/env python3
#
# LISC toolkit
# Flat field processing
#
# Author : Alexandre Simoneau
#
# Created: February 2021
# Edited: February 2021

import click

@click.command(name="flatfield")
def CLI_flatfield():
    """Process frames for flat field calibration.
    """
    flatfield()

def flatfield():
    pass
