# LISC
Low Intensity Sensor Calibration software package.

This program calibrates raw images from a specific camera at a given ISO, focal lenght and focus. To do so, calibration files must be produced.

The details of this program's inner workings are described in **Simoneau et al. (2021)**. 

## Usage

The program provides a CLI through the `lisc` command and a python module of the same name.

Documentation for the modules is available using
```sh
lisc 'module_name' --help
```

The standard order of operations to produce calibration files is as follows:
```sh
lisc dir
lisc init
lisc geo
lisc lin
lisc flat
lisc photo
lisc save
```

Once that process is done, images can be calibrated from anywhere on the system using `lisc calib`.

## Known compatible camera models
- SONY
  - ILCE-7S

## Contributing

This research makes use of the code described in **van Dokkum (2001)** as implemented by **McCully (2014)** for cosmic rays removal.

## License

[MIT](./LICENSE) © 2021 Alexandre Simoneau
