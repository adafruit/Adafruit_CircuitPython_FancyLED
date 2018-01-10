""" Simple FancyLED example for NeoPixel strip
"""

import board
import neopixel
import adafruit_fancyled as fancy

# Function names are kept the same as FastLED examples, which normally
# upsets pylint.  Disable name-checking so this passes muster.
# pylint: disable=invalid-name

NUM_LEDS = 23

# A dynamic gradient palette is a compact representation of a color palette
# that lists only the key points (specific positions and colors), which are
# later interpolated to produce a full 'normal' color palette.
# This one is an RGB spectrum -- red to yellow, green, blue, ... back to red.
RAINBOW = bytes([
    0, 255, 0, 0,
    32, 171, 85, 0,
    64, 171, 171, 0,
    96, 0, 255, 0,
    128, 0, 171, 85,
    160, 0, 0, 255,
    192, 85, 0, 171,
    224, 171, 0, 85,
    255, 255, 0, 0])

# Here the gradient palette is converted to a full normal palette.
# First we need a list to hold the resulting palette...it can be
# filled with nonsense but the list length needs to match the desired
# palette length (in FastLED, after which FancyLED is modeled, color
# palettes always have 16, 32 or 256 entries...we can actually use whatever
# length we want in CircuitPython, but for the sake of consistency, let's
# make it a 256-element palette...
PALETTE = [0] * 256
fancy.loadDynamicGradientPalette(RAINBOW, PALETTE)

# The dynamic gradient step is optional...some projects will just specify
# a whole color palette directly on their own, not expand it from bytes.

# Declare a NeoPixel object on pin D6 with NUM_LEDS pixels, no auto-write
PIXELS = neopixel.NeoPixel(board.D6, NUM_LEDS, brightness=1.0,
                           auto_write=False)

def FillLEDsFromPaletteColors(palette, offset):
    """ This function fills the global PIXELS NeoPixel strip from a color
    palette plus an offset to allow us to 'spin' the colors.  In FancyLED
    (a la FastLED), palette indices are multiples of 16 (e.g. first palette
    entry is index 0, second is index 16, third is 32, etc) and indices
    between these values will interpolate color between the two nearest
    palette entries.
    """

    for i in range(NUM_LEDS):
        # This looks up the color in the palette, scaling from
        # 'palette space' to 'pixel space':
        color = fancy.ColorFromPalette(
            palette, int(i * len(palette) * 16 / NUM_LEDS + offset),
            255, True)
        # Gamma correction gives more sensible-looking colors
        PIXELS[i] = fancy.applyGamma_video(color)

# This is an offset (0-4095) into the color palette to get it to 'spin'
ADJUST = 0

while True:
    FillLEDsFromPaletteColors(PALETTE, ADJUST)
    PIXELS.show()
    ADJUST += 50  # Bigger number = faster spin
    if ADJUST >= 4096:
        ADJUST -= 4096
