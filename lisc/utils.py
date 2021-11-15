import numpy as _np
import rawpy as _rawpy
from astroscrappy import detect_cosmics as _detect_cosmics
from glob import glob as _glob
import os as _os
import pandas as _pd
from exiftool import ExifTool as _ExifTool


def open_raw(fname, band_list="RGB"):
    print(f"Opening '{fname}'")
    raw = _rawpy.imread(fname)

    order = [x[0] for x in sorted(
        _np.ndenumerate(raw.raw_pattern),
        key=lambda x: x[1]
    )]

    data = _np.stack([
        raw.raw_image_visible[i::2, j::2] for i, j in order
    ], axis=-1) / raw.white_level

    bands = _np.array(list(raw.color_desc.decode()))

    return _np.stack([
        _np.mean(data[..., bands == b], axis=-1) if sum(bands == b) > 1
        else data[..., _np.where(bands == b)[0][0]] for b in band_list
    ], axis=-1)


def exif_read(fname, raw=False):
    def safe_float(x):
        try:
            a = float(x)
        except ValueError:
            a = x
        else:
            if a == int(a):
                a = int(a)
        return a

    with _ExifTool() as et:
        exif = et.get_metadata(fname)

    if raw:
        return exif

    gen = [
        "Make", "Model", "LensModel",
        "ImageWidth", "ImageHeight",
        "ExposureTime", "ISO",
        "ShutterSpeedValue"
    ]
    keys = {k: "EXIF:"+k for k in gen}

    make = exif[keys['Make']]
    if make == "SONY":
        maker = {
            "ShutterSpeedValue": "MakerNotes:SonyExposureTime2",
            "ImageHeight": "MakerNotes:SonyImageHeightMax",
            "ImageWidth": "MakerNotes:SonyImageWidthMax"
        }
    else:
        maker = {
            "LensModel": None,
            "ShutterSpeedValue": None
        }

    keys.update(maker)
    info = {k: safe_float(exif[v]) if v is not None else '----'
            for k, v in keys.items()}

    return info


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

    rgb = open_raw(fnames[0])
    aggregate = (1, rgb, _np.zeros_like(rgb))
    for fname in fnames[1:]:
        rgb = open_raw(fname)
        aggregate = _update(aggregate, rgb)
    mean, variance = _finalize(aggregate)
    return mean, _np.sqrt(variance)


def open_clipped(fnames, mean=None, stdev=None, sigclip=5):
    basename = ""
    if type(fnames) == str:
        basename = fnames.replace("*", "$").replace("?", "&").replace(".", "!")+".npy"
        if _os.path.isfile(basename):
            print(f"Opening {fnames} from cache")
            return _np.load(basename)
        fnames = glob_types(fnames)
    if mean is None or stdev is None:
        print("Computing statistics...")
        mean, stdev = compute_stats(fnames)
    print("Clipping files...")
    arr = _np.zeros_like(mean)
    for fname in fnames:
        rgb = open_raw(fname)
        rgb[_np.abs(rgb-mean) > stdev*sigclip] = _np.nan
        arr = _np.nansum([arr, rgb], 0)
    out = arr/len(fnames)
    if basename:
        _np.save(basename, out)
    return out


def cosmicray_removal(image, **kwargs):
    if "sigclip" not in kwargs:
        kwargs['sigclip'] = 25
    if image.ndim == 3:
        new_data = _np.stack([
            _detect_cosmics(image[:, :, i], **kwargs)[1]
            for i in range(3)
        ], axis=2)
    else:
        new_data = _detect_cosmics(image, **kwargs)[1]
    return new_data


def sub(frame, dark):
    return frame-dark


def cycle_mod(x, a=2*_np.pi):
    pos = x % a
    neg = x % -a
    return _np.where(_np.abs(neg) < pos, neg, pos)


def glob_types(pattern="*", types=["ARW", "arw"]):
    return sum((_glob(f"{pattern}.{t}") for t in types), [])


def circle_mask(x, y, shape, r):
    Y, X = _np.ogrid[:shape[0], :shape[1]]
    return (X-x)**2 + (Y-y)**2 < r**2


def correct_linearity(data, lin_data="linearity.csv"):
    if type(lin_data) == str:
        lin_data = _pd.read_csv(lin_data)

    dat = _np.array([
        _np.interp(
            data[:, :, i],
            lin_data[band][::-1],
            lin_data["Exposure"][::-1]
        ) for i, band in enumerate("RGB")
    ])

    return dat.transpose(1, 2, 0)


def correct_flat(data, flat_data="flatfield.npy"):
    if type(flat_data) == str:
        flat_data = _np.load(flat_data)

    return data / (flat_data / flat_data.max((0, 1)))
