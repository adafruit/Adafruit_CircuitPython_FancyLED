# SPDX-FileCopyrightText: 2017 PaintYourDragon for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_fancyled.adafruit_fancyled`
====================================================

FancyLED is a CircuitPython library to assist in creating buttery smooth LED animation.
It's loosely inspired by the FastLED library for Arduino, and in fact we have a "helper"
library using similar function names to assist with porting of existing Arduino FastLED
projects to CircuitPython.

* Author(s): PaintYourDragon
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/Adafruit/Adafruit_CircuitPython_FancyLED.git"

from math import floor


# FancyLED provides color- and palette-related utilities for LED projects,
# offering a buttery smooth look instead of the usual 8-bit-like "blip blip"
# effects often seen with LEDs.  It's loosely inspired by, but NOT a drop-in
# replacement for, the FastLED library for Arduino.


class CRGB:
    """Color stored in Red, Green, Blue color space.

    One of two ways: separate red, gren, blue values (either as integers
    (0 to 255 range) or floats (0.0 to 1.0 range), either type is
    'clamped' to valid range and stored internally in the normalized
    (float) format), OR can accept a CHSV color as input, which will be
    converted and stored in RGB format.

    Following statements are equivalent - all return red:

    .. code-block:: python

          c = CRGB(255, 0, 0)
          c = CRGB(1.0, 0.0, 0.0)
          c = CRGB(CHSV(0.0, 1.0, 1.0))
    """

    def __init__(self, red, green=0.0, blue=0.0):
        # pylint: disable=too-many-branches
        if isinstance(red, CHSV):
            # If first/only argument is a CHSV type, perform HSV to RGB
            # conversion.
            hsv = red  # 'red' is CHSV, this is just more readable
            hue = hsv.hue * 6.0  # Hue circle = 0.0 to 6.0
            sxt = floor(hue)  # Sextant index is next-lower integer of hue
            frac = hue - sxt  # Fraction-within-sextant is 0.0 to <1.0
            sxt = int(sxt) % 6  # mod6 the sextant so it's always 0 to 5

            if sxt == 0:  # Red to <yellow
                r, g, b = 1.0, frac, 0.0
            elif sxt == 1:  # Yellow to <green
                r, g, b = 1.0 - frac, 1.0, 0.0
            elif sxt == 2:  # Green to <cyan
                r, g, b = 0.0, 1.0, frac
            elif sxt == 3:  # Cyan to <blue
                r, g, b = 0.0, 1.0 - frac, 1.0
            elif sxt == 4:  # Blue to <magenta
                r, g, b = frac, 0.0, 1.0
            else:  # Magenta to <red
                r, g, b = 1.0, 0.0, 1.0 - frac

            invsat = 1.0 - hsv.saturation  # Inverse-of-saturation

            self.red = ((r * hsv.saturation) + invsat) * hsv.value
            self.green = ((g * hsv.saturation) + invsat) * hsv.value
            self.blue = ((b * hsv.saturation) + invsat) * hsv.value
        else:
            # Red, green, blue arguments (normalized floats OR integers)
            self.red = clamp_norm(red)
            self.green = clamp_norm(green)
            self.blue = clamp_norm(blue)

    def __repr__(self):  # pylint: disable=invalid-repr-returned
        return (self.red, self.green, self.blue)

    def __str__(self):
        return "(%s, %s, %s)" % (self.red, self.green, self.blue)

    def __len__(self):
        """Retrieve total number of color-parts available."""
        return 3

    def __getitem__(self, key):
        """Retrieve red, green or blue value as iterable."""
        if key == 0:
            return self.red
        if key == 1:
            return self.green
        if key == 2:
            return self.blue
        raise IndexError

    def pack(self, white=None):
        """'Pack' a `CRGB` color into a 24-bit RGB integer, OR, optionally
        assign a white element for RGBW NeoPixels and return as a 4-tuple,
        either of which can be passed to the NeoPixel setter.
        WITH REGARD TO RGBW PIXELS, THIS PROBABLY DOESN'T DO WHAT YOU THINK.
        FancyLED is currently RGB-focused through and through and has no
        concept of RGBW. This function does NOT perform white component
        replacement on the RGB elements -- those values are returned
        unmodified, this just allows appending a white element to pass
        through to the NeoPixel setter with RGBW pixels.
        The reason for this peculiar return option is that the core NeoPixel
        library can't accept packed 32-bit values for RGBW, only 4-tuples.
        This is intentional and by design, because space-constrained devices
        don't support the full 32-bit integer range in CircuitPython (but
        24-bit RGB fits).
        Also note, if gamma_adjust() was applied to an RGB color that's then
        passed to this function, that adjustment is NOT automatically applied
        to the white element -- this must be explicitly handled in user code
        (gamma_adjust() can accept both tuples (for RGB) and single values
        (for white)).
        :param white: integer 0 to 255, float 0.0 to 1.0, or None (default).
        If specified, this value is returned as the last element of an
        integer 4-tuple. Values outside these ranges will be clamped, not
        throw an exception.
        :returns: 24-bit integer a la ``0x00RRGGBB`` if no argument passed,
        or 4-element integer tuple a la ``(R,G,B,W)`` if argument for fourth
        element is provided.
        :rtype: integer or 4-tuple.
        """

        if white:
            # So really this is a quick-fix to the FancyLED + RGBW NeoPixel
            # combination, which is rare and has only come up once. But if
            # this were to become a common thing in the future, a generally
            # more robust approach would be to implement a distinct CRGBW
            # class, which could then do things like gamma_adjust() on all
            # elements, perhaps white component replacement, etc., and would
            # do away with this gross special kludge case.
            # Initially this was done as an __add__ function before moving
            # it here into pack(), as the CRGB + value syntax was guaranteed
            # to cause confusion (it would be easily assumed that it increases
            # brightness, not appends a value). So, note to future self,
            # don't try to be clever that way, this was on purpose.
            if isinstance(white, float):
                white = denormalize(white)
            else:
                white = clamp(white, 0, 255)
            return (
                denormalize(self.red),
                denormalize(self.green),
                denormalize(self.blue),
                white,
            )
        return (
            (denormalize(self.red) << 16)
            | (denormalize(self.green) << 8)
            | (denormalize(self.blue))
        )


class CHSV:
    """Color stored in Hue, Saturation, Value color space.

    Accepts hue as float (any range) or integer (0-256 -> 0.0-1.0) with
    no clamping performed (hue can 'wrap around'), saturation and value
    as float (0.0 to 1.0) or integer (0 to 255), both are clamped and
    stored internally in the normalized (float) format.  Latter two are
    optional, can pass juse hue and saturation/value will default to 1.0.

    Unlike `CRGB` (which can take a `CHSV` as input), there's currently
    no equivalent RGB-to-HSV conversion, mostly because it's a bit like
    trying to reverse a hash...there may be multiple HSV solutions for a
    given RGB input.

    This might be OK as long as conversion precedence is documented,
    but otherwise (and maybe still) could cause confusion as certain
    HSV->RGB->HSV translations won't have the same input and output.
    """

    def __init__(self, h, s=1.0, v=1.0):
        if isinstance(h, float):
            self.hue = h  # Don't clamp! Hue can wrap around forever.
        else:
            self.hue = float(h) / 256.0
        self.saturation = clamp_norm(s)
        self.value = clamp_norm(v)

    def __repr__(self):  # pylint: disable=invalid-repr-returned
        return (self.hue, self.saturation, self.value)

    def __str__(self):
        return "(%s, %s, %s)" % (self.hue, self.saturation, self.value)

    def __len__(self):
        """Retrieve total number of 'color-parts' available."""
        return 3

    def __getitem__(self, key):
        """Retrieve hue, saturation or value as iterable."""
        if key == 0:
            return self.hue
        if key == 1:
            return self.saturation
        if key == 2:
            return self.value
        raise IndexError

    def pack(self, white=None):
        """'Pack' a `CHSV` color into a 24-bit RGB integer, OR, optionally
        assign a white element for RGBW NeoPixels and return as a 4-tuple,
        either of which can be passed to the NeoPixel setter.
        Please see notes accompanying CRGB.pack() for important RGBW
        peculiarities.
        :param white: integer 0 to 255, float 0.0 to 1.0, or None (default).
        If specified, this value is returned as the last element of a 4-tuple.
        Values outside these ranges will be clamped, not throw an exception.
        :returns: 24-bit integer a la ``0x00RRGGBB`` if no argument passed,
        or 4-element integer tuple a la ``(R,G,B,W)`` if argument for fourth
        element is provided.
        :rtype: integer or 4-tuple.
        """

        # Convert CHSV to CRGB, return packed result
        return CRGB(self).pack(white)


def clamp(val, lower, upper):
    """Constrain value within a numeric range (inclusive)."""
    return max(lower, min(val, upper))


def normalize(val, inplace=False):
    """Convert 8-bit (0 to 255) value to normalized (0.0 to 1.0) value.

    Accepts integer, 0 to 255 range (input is clamped) or a list or tuple
    of integers.  In list case, 'inplace' can be used to control whether
    the original list is modified (True) or a new list is generated and
    returned (False).

    Returns float, 0.0 to 1.0 range, or list of floats (or None if inplace).
    """

    if isinstance(val, int):
        # Divide by 255 (not 256) so maximum level is 1.0.
        return clamp(val, 0, 255) / 255.0

    # If not int, is assumed list or tuple.
    if inplace:
        # Modify list in-place (OK for lists, NOT tuples, no check made)
        for i, n in enumerate(val):
            val[i] = normalize(n)
        return None

    # Generate new list
    return [normalize(n) for n in val]


def clamp_norm(val):
    """Clamp or normalize a value as appropriate to its type. If a float is
    received, the return value is the input clamped to a 0.0 to 1.0 range.
    If an integer is received, a range of 0-255 is scaled to a float value
    of 0.0 to 1.0 (also clamped).
    """
    if isinstance(val, float):
        return clamp(val, 0.0, 1.0)
    return normalize(val)


def denormalize(val, inplace=False):
    """Convert normalized (0.0 to 1.0) value to 8-bit (0 to 255) value

    Accepts float, 0.0 to 1.0 range or a list or tuple of floats.  In
    list case, 'inplace' can be used to control whether the original list
    is modified (True) or a new list is generated and returned (False).

    Returns integer, 0 to 255 range, or list of integers (or None if
    inplace).
    """

    # 'Denormalizing' math varies slightly from normalize().  This is on
    # purpose.  Multiply by 256 (NOT 255) and clip.  This ensures that all
    # fractional values fall into the correct 'buckets' -- e.g. 0.999
    # should return 255, not 254 -- and that the buckets are all equal-
    # sized (usu. method of adding 0.5 before int() would miss this).
    if isinstance(val, float):
        return clamp(int(val * 256.0), 0, 255)

    # If not int, is assumed list or tuple.
    if inplace:
        # Modify the list in-place (OK for lists, NOT tuples, no check made)
        for i, n in enumerate(val):
            val[i] = denormalize(n)
        return None

    # Generate new list
    return [denormalize(n) for n in val]


def unpack(val):
    """'Unpack' a 24-bit color into a `CRGB` instance.

    :param int val:  24-bit integer a la ``0x00RRGGBB``.
    :returns: CRGB color.
    :rtype: CRGB
    """

    # See notes in normalize() for math explanation.  Large constants here
    # avoid the usual shift-right step, e.g. 16711680.0 is 255 * 256 * 256,
    # so we can just mask out the red and divide by this for 0.0 to 1.0.
    return CRGB(
        (val & 0xFF0000) / 16711680.0,  # Red
        (val & 0x00FF00) / 65280.0,  # Green
        (val & 0x0000FF) / 255.0,
    )  # Blue


def mix(color1, color2, weight2=0.5):
    """Blend between two colors using given ratio. Accepts two colors (each
    may be `CRGB`, `CHSV` or packed integer), and weighting (0.0 to 1.0)
    of second color.

    :returns: `CRGB` color in most cases, `CHSV` if both inputs are `CHSV`.
    """

    clamp(weight2, 0.0, 1.0)
    weight1 = 1.0 - weight2

    if isinstance(color1, CHSV):
        if isinstance(color2, CHSV):
            # Both colors are CHSV -- interpolate in HSV color space
            # because of the way hue can cross the unit boundary...
            # e.g. if the hues are 0.25 and 0.75, the center point is
            # 0.5 (cyan)...but if you want hues to wrap the other way
            # (with red at the center), you can have hues of 1.25 and 0.75.
            hue = color1.hue + ((color2.hue - color1.hue) * weight2)
            sat = color1.saturation * weight1 + color2.saturation * weight2
            val = color1.value * weight1 + color2.value * weight2
            return CHSV(hue, sat, val)
        # Else color1 is HSV, color2 is RGB.  Convert color1 to RGB
        # before doing interpolation in RGB space.
        color1 = CRGB(color1)
        # If color2 is a packed integer, convert to CRGB instance.
        if isinstance(color2, int):
            color2 = unpack(color2)
    else:
        if isinstance(color2, CHSV):
            # color1 is RGB, color2 is HSV.  Convert color2 to RGB
            # before interpolating in RGB space.
            color2 = CRGB(color2)
        elif isinstance(color2, int):
            # If color2 is a packed integer, convert to CRGB instance.
            color2 = unpack(color2)
        # If color1 is a packed integer, convert to CRGB instance.
        if isinstance(color1, int):
            color1 = unpack(color1)

    # Interpolate and return as CRGB type
    return CRGB(
        (color1.red * weight1 + color2.red * weight2),
        (color1.green * weight1 + color2.green * weight2),
        (color1.blue * weight1 + color2.blue * weight2),
    )


GFACTOR = 2.7  # Default gamma-correction factor for function below


def gamma_adjust(val, gamma_value=None, brightness=1.0, inplace=False):
    """Provides gamma adjustment for single values, `CRGB` and `CHSV` types
    and lists of any of these.

    Works in one of three ways:
      1. Accepts a single normalized level (0.0 to 1.0) and optional
         gamma-adjustment factor (float usu. > 1.0, default if
         unspecified is GFACTOR) and brightness (float 0.0 to 1.0,
         default is 1.0). Returns a single normalized gamma-corrected
         brightness level (0.0 to 1.0).
      2. Accepts a single `CRGB` or `CHSV` type, optional single gamma
         factor OR a (R,G,B) gamma tuple (3 values usu. > 1.0), optional
         single brightness factor OR a (R,G,B) brightness tuple.  The
         input tuples are RGB even when a `CHSV` color is passed. Returns
         a normalized gamma-corrected `CRGB` type (NOT `CHSV`!).
      3. Accept a list or tuple of normalized levels, `CRGB` or `CHSV`
         types (and optional gamma and brightness levels or tuples
         applied to all). Returns a list of gamma-corrected values or
         `CRGB` types (NOT `CHSV`!).

    In cases 2 and 3, if the input is a list (NOT a tuple!), the 'inplace'
    flag determines whether a new tuple/list is calculated and returned,
    or the existing value is modified in-place.  By default this is
    'False'.  If you try to inplace-modify a tuple, an exception is raised.

    In cases 2 and 3, there is NO return value if 'inplace' is True --
    the original values are modified.
    """
    # pylint: disable=too-many-branches

    if isinstance(val, float):
        # Input value appears to be a single float
        if gamma_value is None:
            gamma_value = GFACTOR
        return pow(val, gamma_value) * brightness

    if isinstance(val, (list, tuple)):
        # List or tuple of values
        if isinstance(val[0], float):
            # Input appears to be a list of floats
            if gamma_value is None:
                gamma_value = GFACTOR
            if inplace:
                for i, x in enumerate(val):
                    val[i] = pow(val[i], gamma_value) * brightness
                return None
            newlist = []
            for x in val:
                newlist.append(pow(x, gamma_value) * brightness)
            return newlist
        # List of CRGB or CHSV...we'll get back to that in a moment...
        # but first determine gamma-correction factors for R,G,B:
        if gamma_value is None:
            # No gamma specified, use default
            gamma_red, gamma_green, gamma_blue = GFACTOR, GFACTOR, GFACTOR
        elif isinstance(gamma_value, float):
            # Single gamma value provided, apply to R,G,B
            gamma_red, gamma_green, gamma_blue = (gamma_value, gamma_value, gamma_value)
        else:
            gamma_red, gamma_green, gamma_blue = (
                gamma_value[0],
                gamma_value[1],
                gamma_value[2],
            )
        if isinstance(brightness, float):
            # Single brightness value provided, apply to R,G,B
            brightness_red, brightness_green, brightness_blue = (
                brightness,
                brightness,
                brightness,
            )
        else:
            brightness_red, brightness_green, brightness_blue = (
                brightness[0],
                brightness[1],
                brightness[2],
            )
        if inplace:
            for i, x in enumerate(val):
                if isinstance(x, CHSV):
                    x = CRGB(x)
                val[i] = CRGB(
                    pow(x.red, gamma_red) * brightness_red,
                    pow(x.green, gamma_green) * brightness_green,
                    pow(x.blue, gamma_blue) * brightness_blue,
                )
            return None
        newlist = []
        for x in val:
            if isinstance(x, CHSV):
                x = CRGB(x)
            newlist.append(
                CRGB(
                    pow(x.red, gamma_red) * brightness_red,
                    pow(x.green, gamma_green) * brightness_green,
                    pow(x.blue, gamma_blue) * brightness_blue,
                )
            )
        return newlist

    # Single CRGB or CHSV value
    if gamma_value is None:
        # No gamma specified, use default
        gamma_red, gamma_green, gamma_blue = GFACTOR, GFACTOR, GFACTOR
    elif isinstance(gamma_value, float):
        # Single gamma value provided, apply to R,G,B
        gamma_red, gamma_green, gamma_blue = (gamma_value, gamma_value, gamma_value)
    else:
        gamma_red, gamma_green, gamma_blue = (
            gamma_value[0],
            gamma_value[1],
            gamma_value[2],
        )
    if isinstance(brightness, float):
        # Single brightness value provided, apply to R,G,B
        brightness_red, brightness_green, brightness_blue = (
            brightness,
            brightness,
            brightness,
        )
    else:
        brightness_red, brightness_green, brightness_blue = (
            brightness[0],
            brightness[1],
            brightness[2],
        )

    if isinstance(val, CHSV):
        val = CRGB(val)

    return CRGB(
        pow(val.red, gamma_red) * brightness_red,
        pow(val.green, gamma_green) * brightness_green,
        pow(val.blue, gamma_blue) * brightness_blue,
    )


def palette_lookup(palette, position):
    """Fetch color from color palette, with interpolation.

    :param palette: color palette (list of CRGB, CHSV and/or packed integers)
    :param float position: palette position (0.0 to 1.0, wraps around).

    :returns: `CRGB` or `CHSV` instance, no gamma correction applied.
    """

    position %= 1.0  # Wrap palette position in 0.0 to <1.0 range

    weight2 = position * len(palette)  # Scale position to palette length
    idx = int(floor(weight2))  # Index of 'lower' color (0 to len-1)
    weight2 -= idx  # Weighting of 'upper' color

    color1 = palette[idx]  # Fetch 'lower' color
    idx = (idx + 1) % len(palette)  # Get index of 'upper' color
    color2 = palette[idx]  # Fetch 'upper' color

    return mix(color1, color2, weight2)


def expand_gradient(gradient, length):
    """Convert gradient palette into standard equal-interval palette.

    :param sequence gradient: List or tuple of of 2-element lists/tuples
      containing position (0.0 to 1.0) and color (packed int, CRGB or CHSV).
      It's OK if the list/tuple elements are either lists OR tuples, but
      don't mix and match lists and tuples -- use all one or the other.

    :returns: CRGB list, can be used with palette_lookup() function.
    """

    gradient = sorted(gradient)  # Sort list by position values
    least = gradient[0][0]  # Lowest position value (ostensibly 0.0)
    most = gradient[-1][0]  # Highest position value (ostensibly 1.0)
    newlist = []

    for i in range(length):
        pos = i / float(length - 1)  # 0.0 to 1.0 in 'length' steps
        # Determine indices in list of item 'below' and 'above' pos
        if pos <= least:
            # Off bottom of list - use lowest index
            below, above = 0, 0
        elif pos >= most:
            # Off top of list - use highest index
            below, above = -1, -1
        else:
            # Seek position between two items in list
            below, above = 0, -1
            for n, x in enumerate(gradient):
                if pos >= x[0]:
                    below = n
            for n, x in enumerate(gradient[-1:0:-1]):
                if pos <= x[0]:
                    above = -1 - n

        # Range between below, above
        r = gradient[above][0] - gradient[below][0]
        if r <= 0:
            newlist.append(gradient[below][1])  # Use 'below' color only
        else:
            weight2 = (pos - gradient[below][0]) / r  # Weight of 'above' color
            color1 = gradient[below][1]
            color2 = gradient[above][1]
            # Interpolate and add to list
            newlist.append(mix(color1, color2, weight2))

    return newlist
