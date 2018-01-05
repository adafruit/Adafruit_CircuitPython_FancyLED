# The MIT License (MIT)
#
# Copyright (c) 2017 PaintYourDragon for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_CircuitPython_FancyLED`
====================================================

TODO(description)

* Author(s): PaintYourDragon
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/Adafruit/Adafruit_CircuitPython_FancyLED.git"


"""
FancyLED is sort of a mild CircuitPython interpretation of a subset
of the FastLED library for Arduino.  This is mainly to assist with
porting of existing Arduino projects to CircuitPython.
It is NOT fast.  Whereas FastLED does a lot of bit-level numerical
tricks for performance, we don't really have that luxury in Python,
and the aim here is just to have equivalent (ish) functions for the
most oft-used calls.
"""

GFACTOR = 2.5  # Default gamma-correction factor for function below

def applyGamma_video(n, g_r=GFACTOR, g_g=None, g_b=None, inplace=False):
    """ Approximates various invocations of FastLED's many-ways-overloaded
    applyGamma_video() function.

    ACCEPTS: One of three ways:
      1. A single brightness level (0-255) and optional gamma-correction
         factor (float usu. > 1.0, default if unspecified is 2.5).
      2. A single RGB tuple (3 values 0-255) and optional gamma factor
         or separate R, G, B gamma values.
      3. A list of RGB tuples (and optional gamma(s)).
      In the tuple/list cases, the 'inplace' flag determines whether
      a new tuple/list is calculated and returned, or the existing
      value is modified in-place.  By default this is 'False'.
      Can also use the napplyGamma_video() function to more directly
      approximate FastLED syntax/behavior.

    RETURNS: Corresponding to above cases:
      1. Single gamma-corrected brightness level (0-255).
      2. A gamma-corrected RGB tuple (3 values 0-255).
      3. A list of gamma-corrected RGB tuples (ea. 3 values 0-255).
      In the tuple/list cases, there is NO return value if 'inplace'
      is true -- the original values are modified.
    """

    if isinstance(n, int):
        # Input appears to be a single integer
        result = int(pow(n / 255.0, g_r) * 255.0 + 0.5)
        # Never gamma-adjust a positive number down to zero
        if result == 0 and n > 0:
            result = 1
        return result
    else:
        # Might be an RGB tuple, or a list of tuples, but
        # isinstance() doesn't seem to distinguish...so try
        # treating it as a list first, and if that fails,
        # fall back on the RGB tuple case.
        try:
            if inplace:
                for i in range(len(n)):
                    n[i] = applyGamma_video(n[i], g_r, g_g, g_b)
            else:
                newlist = []
                for i in n:
                    newlist += applyGamma_video(i, g_r, g_g, g_b)
                return newlist
        except TypeError:
            if g_g is None:
                g_g = g_r
            if g_b is None:
                g_b = g_r
            if inplace:
                n[0] = applyGamma_video(n[0], g_r)
                n[1] = applyGamma_video(n[1], g_g)
                n[2] = applyGamma_video(n[2], g_b)
            else:
                return [applyGamma_video(n[0], g_r),
                        applyGamma_video(n[1], g_g),
                        applyGamma_video(n[2], g_b)]


def napplyGamma_video(n, g_r=GFACTOR, g_g=None, g_b=None):
    """ In-place version of applyGamma_video() (to mimic FastLED function
    name).  This is for RGB tuples and tuple lists (not the prior function's
    integer case)
    """

    return applyGamma_video(n, g_r, g_g, g_b, inplace=True)


def fill_gradient_rgb(pal, startpos, startcolor, endpos, endcolor):
    """ Sort-of-approximation of FastLED full_gradient_rgb() function.
    Fills subsection of palette with RGB color range.

    ACCEPTS: Palette to modify (must be a preallocated list with a suitable
             number of elements), index of first entry to fill, RGB color of
             first entry (as RGB tuple), index of last entry to fill, RGB
             color of last entry (as RGB tuple).
    RETURNS: Nothing; palette list is modified in-place.
    """

    if endpos < startpos:
        startpos, endpos = endpos, startpos
        startcolor, endcolor = endcolor, startcolor

    dist = endpos - startpos
    if dist == 0:
        pal[startpos] = startcolor
        return

    delta_r = endcolor[0] - startcolor[0]
    delta_g = endcolor[1] - startcolor[1]
    delta_b = endcolor[2] - startcolor[2]

    for i in range(dist + 1):
        scale = i / dist
        pal[int(startpos + i)] = [
            int(startcolor[0] + delta_r * scale),
            int(startcolor[1] + delta_g * scale),
            int(startcolor[2] + delta_b * scale)]


def loadDynamicGradientPalette(src, dst):
    """ Kindasorta like FastLED's loadDynamicGradientPalette() function,
    with some gotchas.

    ACCEPTS: Gradient palette data as a 'bytes' type (makes it easier to copy
             over gradient palettes from existing FastLED Arduino sketches)...
             each palette entry is four bytes: a relative position (0-255)
             within the overall resulting palette (whatever its size), and
             3 values for R, G and B...and a destination palette list which
             must be preallocated to the desired length (e.g. 16, 32 or 256
             elements if following FastLED conventions, but can be other
             lengths if needed, the palette lookup function doesn't care).
    RETURNS: Nothing; palette list data is modified in-place.
    """

    palettemaxindex = len(dst) - 1  # Index of last entry in dst list
    startpos = 0
    startcolor = [src[1], src[2], src[3]]
    n = 4
    while True:
        endpos = src[n] * palettemaxindex / 255
        endcolor = [src[n+1], src[n+2], src[n+3]]
        fill_gradient_rgb(dst, startpos, startcolor, endpos, endcolor)
        if src[n] >= 255:
            break  # Done!
        n += 4
        startpos = endpos
        startcolor = endcolor


def ColorFromPalette(pal, index, brightness=255, blend=False):
    """ Approximates the FastLED ColorFromPalette() function

    ACCEPTS: color palette (list of ints or tuples), palette index (x16) +
             blend factor of next index (0-15) -- e.g. pass 32 to retrieve
             palette index 2, or 40 for an interpolated value between
             palette index 2 and 3, optional brightness (0-255), optional
             blend flag (True/False)
    RETURNS: single RGB tuple (3 values 0-255, no gamma correction)
    """

    lo4 = index & 0xF # 0-15 blend factor to next palette entry
    hi4 = (index >> 4) % len(pal)
    color = pal[hi4]
    hi4 = (hi4 + 1) % len(pal)
    if isinstance(pal[0], int):
        # Color palette is in packed integer format
        red1 = (color >> 16) & 0xFF
        green1 = (color >>  8) & 0xFF
        blue1 = color & 0xFF
        color = pal[hi4]
        red2 = (color >> 16) & 0xFF
        green2 = (color >>  8) & 0xFF
        blue2 = color & 0xFF
    else:
        # Color palette is in RGB tuple format
        red1 = color[0]
        green1 = color[1]
        blue1 = color[2]
        color = pal[hi4]
        red2 = color[0]
        green2 = color[1]
        blue2 = color[2]

    if blend and lo4 > 0:
        weight2 = (lo4 * 0x11) + 1 # upper weighting 1-256
        weight1 = 257 - weight2    # lower weighting 1-256
        if brightness == 255:
            return [(red1   * weight1 + red2   * weight2) >> 8,
                    (green1 * weight1 + green2 * weight2) >> 8,
                    (blue1  * weight1 + blue2  * weight2) >> 8]
        brightness += 1 # 1-256
        return [(red1   * weight1 + red2   * weight2) * brightness >> 16,
                (green1 * weight1 + green2 * weight2) * brightness >> 16,
                (blue1  * weight1 + blue2  * weight2) * brightness >> 16]

    if brightness == 255:
        return [red1, green1, blue1]

    brightness += 1
    return [(red1   * brightness) >> 8,
            (green1 * brightness) >> 8,
            (blue1  * brightness) >> 8]


def hsv2rgb_spectrum(hsv):
    """ This is named the same thing as FastLED's simpler HSV to RGB function
    (spectrum, vs rainbow) but implementation is a bit different for the
    sake of getting something running (adapted from some NeoPixel code).

    ACCEPTS: HSV color as a 3-element tuple [hue, saturation, value], each
             in the range 0 to 255.
    RETURNS: RGB color as a 3-element tuple [R, G, B]
    """

    hue = hsv[0] * 6.0 / 256.0    # 0.0 to <6.0
    sxt = int(hue)                # Sextant number; 0 to 5
    frac = int((hue - sxt) * 255) # 0-254 within sextant (NOT 255!)

    if sxt == 0: # R to Y
        r, g, b = 255, frac, 0
    elif sxt == 1: # Y to G
        r, g, b = 254-frac, 255, 0
    elif sxt == 2: # G to C
        r, g, b = 0, 255, frac
    elif sxt == 3: # C to B
        r, g, b = 0, 254-frac, 255
    elif sxt == 4: # B to M
        r, g, b = frac, 0, 255
    else: # M to R
        r, g, b = 255, 0, 254-frac

    val1 = 1 + hsv[2]    # value 1 to 256; allows >>8 instead of /255
    sat1 = 1 + hsv[1]    # saturation 1 to 256; same reason
    sat2 = 255 - hsv[1]  # 255 to 0

    return [(((((r * sat1) >> 8) + sat2) * val1) >> 8) & 0xFF,
            (((((g * sat1) >> 8) + sat2) * val1) >> 8) & 0xFF,
            (((((b * sat1) >> 8) + sat2) * val1) >> 8) & 0xFF]
