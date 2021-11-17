import os as _os
from glob import glob as _glob

import numpy as _np
import pandas as _pd
import rawpy as _rawpy
from astroscrappy import detect_cosmics as _detect_cosmics
from exiftool import ExifTool as _ExifTool


def open_raw(fname, band_list="RGB"):
    print(f"Opening '{fname}'")
    raw = _rawpy.imread(fname)
    h = raw.sizes.height // 2
    w = raw.sizes.width // 2

    data = (
        raw.raw_image_visible.reshape(h, 2, w, 2)
        .transpose((1, 3, 0, 2))
        .reshape(4, h, w)
    ) / raw.white_level

    bands_mask = (
        _np.array(list(raw.color_desc.decode()))[raw.raw_pattern.flatten()]
        == _np.array(list(band_list))[:, None]
    )

    return _np.stack(
        [
            _np.mean(data[b], axis=0) if sum(b) > 1 else data[b][0]
            for b in bands_mask
        ],
        axis=-1,
    )


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
        "ExposureTime",
        "ImageHeight",
        "ImageWidth",
        "ISO",
        "LensModel",
        "Make",
        "Model",
        "ShutterSpeedValue",
    ]
    keys = {k: "EXIF:" + k for k in gen}

    make = exif[keys["Make"]]
    if make == "SONY":
        maker = {
            "ImageHeight": "MakerNotes:SonyImageHeightMax",
            "ImageWidth": "MakerNotes:SonyImageWidthMax",
            "ShutterSpeedValue": "MakerNotes:SonyExposureTime2",
        }
    else:
        maker = {
            "LensModel": None,
            "ShutterSpeedValue": None,
        }

    keys.update(maker)
    info = {
        k: safe_float(exif[v]) if v is not None else "----"
        for k, v in keys.items()
    }

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
        basename = (
            fnames.replace("*", "$").replace("?", "&").replace(".", "!")
            + ".npy"
        )
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
        rgb[_np.abs(rgb - mean) > stdev * sigclip] = _np.nan
        arr = _np.nansum([arr, rgb], 0)
    out = arr / len(fnames)

    if basename:
        _np.save(basename, out)

    return out


def cosmicray_removal(image, **kwargs):
    if "sigclip" not in kwargs:
        kwargs["sigclip"] = 25
    if image.ndim == 3:
        new_data = _np.stack(
            [
                _detect_cosmics(band, **kwargs)[1]
                for band in _np.moveaxis(image, -1, 0)
            ],
            axis=2,
        )
    else:
        new_data = _detect_cosmics(image, **kwargs)[1]
    return new_data


def cycle_mod(x, a=2 * _np.pi):
    pos, neg = x % a, x % -a
    return _np.where(_np.abs(neg) < pos, neg, pos)


def glob_types(pattern="*", types=["ARW", "arw"]):
    return sum((_glob(f"{pattern}.{t}") for t in types), [])


def circle_mask(x, y, shape, r):
    Y, X = _np.ogrid[: shape[0], : shape[1]]
    return (X - x) ** 2 + (Y - y) ** 2 < r ** 2


def correct_linearity(data, lin_data="linearity.csv"):
    if type(lin_data) == str:
        lin_data = _pd.read_csv(lin_data)

    return _np.stack(
        [
            _np.interp(layer, lin_data[band][::-1], c)
            for band, layer, c in zip(
                "RGB",
                _np.moveaxis(data, -1, 0),
                (
                    lin_data[band][6]
                    / lin_data["Exposure"][6]
                    * lin_data["Exposure"][::-1]
                    for band in "RGB"
                ),
            )
        ],
        axis=2,
    )


def correct_flat(data, flat_data="flatfield.npy"):
    if type(flat_data) == str:
        flat_data = _np.load(flat_data)

    return data / (flat_data / flat_data.max((0, 1)))
