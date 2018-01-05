# Simple fancyled example for Circuit Playground Express

from adafruit_circuitplayground.express import cpx
import fancyled

# A dynamic gradient palette is a compact representation of a color palette
# that lists only the key points (specific positions and colors), which are
# later interpolated to produce a full 'normal' color palette.
# This one happens to be a blackbody spectrum, it ranges from black to red
# to yellow to white...
blackbody = bytes([
    0,   0,   0,   0,
   85, 255,   0,   0,
  170, 255, 255,   0,
  255, 255, 255, 255 ])

# Here's where we convert the dynamic gradient palette to a full normal
# palette.  First we need a list to hold the resulting palette...it can be
# filled with nonsense but the list length needs to match the desired
# palette length (in FastLED, after which fancyled is modeled, color
# palettes always have 16, 32 or 256 entries...we can actually use whatever
# length we want in CircuitPython, but for the sake of consistency, let's
# make it a 16-element palette...
palette = [0] * 16
fancyled.loadDynamicGradientPalette(blackbody, palette)

# The dynamic gradient step is optional...some projects will just specify
# a whole color palette directly on their own, not expand it from bytes.

# This function fills the Circuit Playground Express NeoPixels from a
# color palette plus an offset to allow us to 'spin' the colors.  In
# fancyled (a la FastLED), palette indices are multiples of 16 (e.g.
# first palette entry is index 0, second is index 16, third is 32, etc)
# and indices between these values will interpolate color between the
# two nearest palette entries.
def FillLEDsFromPaletteColors(palette, offset):
	for i in range(10):
		# This looks up the color in the palette, scaling from
		# 'palette space' (16 colors * 16 interp position = 256)
		# to 'pixel space' (10 NeoPixels):
		c = fancyled.ColorFromPalette(palette,
		  int(i * len(palette) * 16 / 10 + offset), 255, True)
		# Gamma correction gives more sensible-looking colors
		cpx.pixels[i] = fancyled.applyGamma_video(c)

# This is an offset (0-255) into the color palette to get it to 'spin'
adjust = 0

while True:
	FillLEDsFromPaletteColors(palette, adjust)
	adjust += 4  # Bigger number = faster spin
	if adjust >= 256: adjust -= 256
