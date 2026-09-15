"""
Script to generate random or harmony-based color palettes from the newdigate RGB565 colors list.

Requirements:
  - Python 3.x
  - Clone https://github.com/newdigate/rgb565_colors and place `rgb565_colors.h` in the same directory.

Usage:
  python generate_16bit_palette.py [--count N] [--scheme {random,analogous,complementary,triadic,tetradic}]

Examples:
  python generate_16bit_palette.py --count 5 --scheme triadic
"""
import re
import random
import argparse
import colorsys

# Parse rgb565_colors.h to extract (name, 16bit_value)
def load_rgb565_colors(header_path="rgb565_colors.h"):
    pattern = re.compile(r"#define\s+([A-Za-z0-9_()' ,-]+)\s+0x([0-9A-Fa-f]{4})")
    colors = []
    with open(header_path, 'r') as f:
        for line in f:
            m = pattern.search(line)
            if m:
                name = m.group(1).strip()
                val = int(m.group(2), 16)
                colors.append((name, val))
    return colors

# Convert 16-bit RGB565 to 8-bit-per-channel RGB tuple
def rgb565_to_rgb888(val):
    r = (val >> 11) & 0x1F
    g = (val >> 5) & 0x3F
    b = val & 0x1F
    # scale up to 0-255
    return (int(r * 255 / 31), int(g * 255 / 63), int(b * 255 / 31))

# Convert RGB888 to HSL (0-1 range)
def rgb_to_hsl(rgb):
    r, g, b = [c/255.0 for c in rgb]
    # colorsys uses HLS, so H, L, S = colorsys.rgb_to_hls
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, s, l  # return H, S, L for easier use

# Find the color entry closest in hue to a target hue
def closest_by_hue(colors_hsl, target_hue):
    # account for hue wrap-around
    def hue_dist(h): return min(abs(h - target_hue), 1 - abs(h - target_hue))
    return min(colors_hsl, key=lambda x: hue_dist(x[2]))  # x = (name, val, h, s, l)

# Generate a harmonious palette
def generate_harmony(colors, scheme='analogous', count=5):
    # preprocess HSL list
    colors_hsl = []
    for name, val in colors:
        rgb = rgb565_to_rgb888(val)
        h, s, l = rgb_to_hsl(rgb)
        colors_hsl.append((name, val, h, s, l))

    # pick a random base
    base = random.choice(colors_hsl)
    base_h = base[2]

    # define harmony angles
    schemes = {
        'analogous': [0, 1/12, -1/12],
        'complementary': [0, 0.5],
        'triadic': [0, 1/3, 2/3],
        'tetradic': [0, 0.5, 0.25, 0.75]
    }
    angles = schemes.get(scheme, [0])

    palette = []
    for ang in angles[:count]:
        target_h = (base_h + ang) % 1.0
        # find closest color by hue
        choice = closest_by_hue(colors_hsl, target_h)
        palette.append(choice)
    # if we need more random to fill count
    while len(palette) < count:
        palette.append(random.choice(colors_hsl))
    return palette

# Generate purely random palette
def generate_random(colors, count=5):
    return random.sample(colors, count)

# Format palette for display
def format_palette(palette):
    out = []
    for entry in palette:
        if len(entry) == 2:
            name, val = entry
        else:
            name, val = entry[0], entry[1]
        rgb = rgb565_to_rgb888(val)
        out.append(f"{name}: RGB565=0x{val:04X}, RGB888={rgb}")
    return "\n".join(out)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=5, help='Number of colors in palette')
    parser.add_argument('--scheme', choices=['random','analogous','complementary','triadic','tetradic'], default='random')
    parser.add_argument('--header', default='rgb565_colors.h', help='Path to rgb565_colors.h')
    args = parser.parse_args()

    colors = load_rgb565_colors(args.header)
    if args.scheme == 'random':
        pal = generate_random(colors, args.count)
    else:
        pal = generate_harmony(colors, scheme=args.scheme, count=args.count)
    print(format_palette(pal))
