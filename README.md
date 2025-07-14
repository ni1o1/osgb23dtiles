# osgb23dtiles

A Python package to convert OSGB files to 3D Tiles. Build based on [https://github.com/fanvanzh/3dtiles](https://github.com/fanvanzh/3dtiles)

## Installation

```bash
pip install .
```

## Usage

```python
from osgb23dtiles import osgb_to_b3dm_3dtiles, osgb_to_glb

# Convert OSGB directory to 3D Tiles
osgb_to_b3dm_3dtiles('input_dir', 'output_dir')

# Convert single OSGB to GLB
osgb_to_glb('input.osgb', 'output.glb')
```

For Windows, ensure the DLL dependencies are in PATH.

## Documentation

See the docs built with MkDocs.