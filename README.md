# vol2nrrd

**Convert Morita `.vol` files to NRRD format**

## Overview

`vol2nrrd` is a small Python utility to convert 3D Morita `.vol` medical imaging files into the **NRRD** format.
It can optionally rotate volumes, extract XML headers, and generate gzip-compressed NRRD files.

## Features

- Convert `.vol` → `.nrrd` or `.nhdr`
- Supports rotation of the volume
- Extract and pretty-print the XML header to a separate `.xml` file
- Pure Python implementation, no external tools required

## Installation

You can install it via `pip` directly from the repository:

```sh
pip install git+https://github.com/aixp/vol2nrrd.git
```

## Usage

```sh
vol2nrrd [OPTIONS] PATH
```

**Options:**

* `--output-extension {auto,nrrd,nhdr}`

  Choose output extension. Default `auto`.

* `--extract-header`

  Extract the XML header and save it as a formatted `.xml` file.

**Examples:**

Convert a `.vol` file to `.nrrd` or `.nhdr`:

```sh
vol2nrrd CT_0.vol
```

Convert a `.vol` file to `.nhdr` (do not apply rotation):

```sh
vol2nrrd --output-extension nhdr CT_0.vol
```

## License

MIT License — see [LICENSE](LICENSE) for details.
