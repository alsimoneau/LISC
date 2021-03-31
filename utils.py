import numpy as np
import rawpy
from astroscrappy import detect_cosmics
import exiftool
from glob import glob
import os
import pandas as pd

def open_raw(fname, normalize=False):
    print(f"Opening raw file '{fname}'")
    raw = rawpy.imread(fname)
    rgb = raw.postprocess(
        gamma = (1,1),
        output_bps = 16,
        no_auto_bright = True,
        user_flip = 0,
        demosaic_algorithm = rawpy.DemosaicAlgorithm(0)
    )

    if normalize:
        rgb /= 2**16 - 1

    return rgb

def compute_stats(fnames):
    # Taken from https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
    def _update(existingAggregate, newValue):
        (count, mean, M2) = existingAggregate
        count += 1
        delta = newValue - mean
        mean += delta / count
        delta2 = newValue - mean
        M2 += delta * delta2
        return (count, mean, M2)

    def _finalize(existingAggregate):
        (count, mean, M2) = existingAggregate
        return (mean, M2 / count)

    rgb = open_raw(fnames[0]).astype(np.float64)
    aggregate = (1,rgb,np.zeros_like(rgb))
    for fname in fnames[1:]:
        rgb = open_raw(fname)
        aggregate = _update(aggregate,rgb)
    mean, variance = _finalize(aggregate)
    return mean, np.sqrt(variance)

def open_clipped(fnames,mean=None,stdev=None,sigclip=5):
    basename = ""
    if type(fnames) == str:
        basename = fnames.replace("*","$").replace("?","&").replace(".","!")+".npy"
        if os.path.isfile(basename):
            print(f"Opening {fnames} from cache")
            return np.load(basename)
        fnames = glob_types(fnames)
    if mean is None or stdev is None:
        print("Computing statistics...")
        mean,stdev = compute_stats(fnames)
    print("Clipping files...")
    arr = open_raw(fnames[0]).astype(np.float64)
    for fname in fnames[1:]:
        rgb = open_raw(fname).astype(np.float64)
        rgb[np.abs(rgb-mean) > stdev*sigclip] = np.nan
        arr = np.nansum([arr,rgb],0)
    out = np.round(arr/len(fnames)).astype(np.uint16)
    if basename:
        np.save(basename,out)
    return out

def cosmicray_removal(image,**kwargs):
    if "sigclip" not in kwargs:
        kwargs['sigclip'] = 25
    if image.ndim == 3:
        new_data = np.stack( [
            detect_cosmics(image[:,:,i],**kwargs)[1] \
            for i in range(3)
        ], axis=2 )
    else:
        new_data = detect_cosmics(image,**kwargs)[1]
    return new_data

def sub(frame,dark):
    return frame.astype(np.int32)-dark

def cycle_mod(x,a=2*np.pi):
    pos = x%a
    neg = x%-a
    return np.where(np.abs(neg) < pos, neg, pos)

def glob_types(pattern="*",types=["ARW","arw"]):
    return sum( (glob(f"{pattern}.{t}") for t in types), [] )

def circle_mask(x,y,shape,r):
    Y,X = np.ogrid[:shape[0],:shape[1]]
    return (X-x)**2 + (Y-y)**2 < r**2

def correct_linearity(data,lin_data="linearity.csv"):
    if type(lin_data == str):
        lin_data = pd.read_csv(lin_data)

    dat = np.array([
        np.interp(
            data[:,:,i],
            lin_data[band][::-1],
            lin_data["Exposure"][::-1]
        ) for i,band in enumerate("RGB")
    ])

    return dat.transpose(1,2,0)
