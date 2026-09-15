# rgb565_palette_maker

Color palette generator and viewer for RGB565 embedded displays.

## What it is

A small utility pair for embedded/display work:

- `color_grabber.py` generates color palettes (random, analogous, complementary, triadic, and
  tetradic schemes) from a large list of named RGB565 color constants (`rgb565_colors.h`).
- `palette_viewer.py` is a Tkinter GUI for browsing and visualizing those palettes.

Built to pair with display-driving embedded projects like [esp32-sovereign-watch](https://github.com/ay2609/esp32-sovereign-watch).

## Stack

- Python, Tkinter

## Credits

`rgb565_colors.h` is from [newdigate/rgb565_colors](https://github.com/newdigate/rgb565_colors).

## Usage

```bash
python color_grabber.py
python palette_viewer.py
```
