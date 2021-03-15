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

@click.command(name="starfield")
def CLI_starfield():
    """Process frames for star field calibration.
    """
    starfield()

def starfield():
    pass
