# fancyled is sort of a mild CircuitPython interpretation of a subset
# of the FastLED library for Arduino.  This is mainly to assist with
# porting of existing Arduino projects to CircuitPython.
# It is NOT fast.  Whereas FastLED does a lot of bit-level numerical
# tricks for performance, we don't really have that luxury in Python,
# and the aim here is just to have equivalent (ish) functions for the
# most oft-used calls.

from math import pow

gfactor = 2.5  # Default gamma-correction factor for function below

# This approximates various invocations of FastLED's many-ways-overloaded
# applyGamma_video() function.
# ACCEPTS: One of three ways:
#          1. A single brightness level (0-255) and optional gamma-correction
#             factor (float usu. > 1.0, default if unspecified is 2.5).
#          2. A single RGB tuple (3 values 0-255) and optional gamma factor
#             or separate R, G, B gamma values.
#          3. A list of RGB tuples (and optional gamma(s)).
#          In the tuple/list cases, the 'inPlace' flag determines whether
#          a new tuple/list is calculated and returned, or the existing
#          value is modified in-place.  By default this is 'False'.
#          Can also use the napplyGamma_video() function to more directly
#          approximate FastLED syntax/behavior.
# RETURNS: Corresponding to above cases:
#          1. Single gamma-corrected brightness level (0-255).
#          2. A gamma-corrected RGB tuple (3 values 0-255).
#          3. A list of gamma-corrected RGB tuples (ea. 3 values 0-255).
#          In the tuple/list cases, there is NO return value if 'inPlace'
#          is true -- the original values are modified.
def applyGamma_video(n, gR=gfactor, gG=None, gB=None, inPlace=False):
	if isinstance(n, int):
		# Input appears to be a single integer
		result = int(pow(n / 255.0, gR) * 255.0 + 0.5)
		# Never gamma-adjust a positive number down to zero
		if result == 0 and n > 0: result = 1
		return result
	else:
		# Might be an RGB tuple, or a list of tuples, but
		# isinstance() doesn't seem to distinguish...so try
		# treating it as a list first, and if that fails,
		# fall back on the RGB tuple case.
		try:
			if inPlace:
				for i in range(len(n)):
					n[i] = applyGamma_video(n[i],
					  gR, gG, gB)
			else:
				newlist = []
				for i in n:
					newlist += applyGamma_video(i,
					  gR, gG, gB)
				return newlist
		except TypeError:
			if gG is None: gG = gR
			if gB is None: gB = gR
			if inPlace:
				n[0] = applyGamma_video(n[0], gR)
				n[1] = applyGamma_video(n[1], gG)
				n[2] = applyGamma_video(n[2], gB)
			else:
				return [
				  applyGamma_video(n[0], gR),
				  applyGamma_video(n[1], gG),
				  applyGamma_video(n[2], gB) ]


# In-place version of above (to match FastLED function name)
# This is for RGB tuples and tuple lists (not the above's integer case)
def napplyGamma_video(n, gR=gfactor, gG=None, gB=None):
	return applyGamma_video(n, gR=gfactor, gG=None, gB=None, inPlace=True)


# Sort-of-approximation of FastLED full_gradient_rgb() function.
# Fills subsection of palette with RGB color range.
# ACCEPTS: Palette to modify (must be a preallocated list with a suitable
#          number of elements), index of first entry to fill, RGB color of
#          first entry (as RGB tuple), index of last entry to fill, RGB
#          color of last entry (as RGB tuple).
# RETURNS: Nothing; palette list is modified in-place.
def fill_gradient_rgb(pal, startpos, startcolor, endpos, endcolor):
	if endpos < startpos:
		startpos  , endpos   = endpos  , startpos
		startcolor, endcolor = endcolor, startcolor

	dist = endpos - startpos
	if dist == 0:
		pal[startpos] = startcolor
		return

	deltaR = endcolor[0] - startcolor[0]
	deltaG = endcolor[1] - startcolor[1]
	deltaB = endcolor[2] - startcolor[2]

	for i in range(dist + 1):
		scale = i / dist
		pal[int(startpos + i)] = [
		  int(startcolor[0] + deltaR * scale),
		  int(startcolor[1] + deltaG * scale),
		  int(startcolor[2] + deltaB * scale) ]


# Kindasorta like FastLED's loadDynamicGradientPalette() function, with
# some gotchas.
# ACCEPTS: Gradient palette data as a 'bytes' type (makes it easier to copy
#          over gradient palettes from existing FastLED Arduino sketches)...
#          each palette entry is four bytes: a relative position (0-255)
#          within the overall resulting palette (whatever its size), and
#          3 values for R, G and B...and a destination palette list which
#          must be preallocated to the desired length (e.g. 16, 32 or 256
#          elements if following FastLED conventions, but can be other
#          lengths if needed, the palette lookup function doesn't care).
# RETURNS: Nothing; palette list data is modified in-place.
def loadDynamicGradientPalette(src, dst):
	palettemaxindex = len(dst) - 1  # Index of last entry in dst list
	startpos        = 0
	startcolor      = [ src[1], src[2], src[3] ]
	n               = 4
	while True:
		endpos     = src[n] * palettemaxindex / 255
		endcolor   = [ src[n+1], src[n+2], src[n+3] ]
		fill_gradient_rgb(dst, startpos, startcolor, endpos, endcolor)
		if src[n] >= 255: break  # Done!
		n         += 4
		startpos   = endpos
		startcolor = endcolor


# Approximates the FastLED ColorFromPalette() function
# ACCEPTS: color palette (list of ints or tuples), palette index (x16) +
# blend factor of next index (0-15) -- e.g. pass 32 to retrieve palette
# index 2, or 40 for an interpolated value between palette index 2 and 3,
# optional brightness (0-255), optiona blend flag (True/False)
# RETURNS: single RGB tuple (3 values 0-255, no gamma correction)
def ColorFromPalette(pal, index, brightness=255, blend=False):
	lo4 = index & 0xF # 0-15 blend factor to next palette entry
	hi4 = (index >> 4) % len(pal)
	c   = pal[hi4]
	hi4 = (hi4 + 1) % len(pal)
	if isinstance(pal[0], int):
		# Color palette is in packed integer format
		r1 = (c >> 16) & 0xFF
		g1 = (c >>  8) & 0xFF
		b1 =  c        & 0xFF
		c  = pal[hi4]
		r2 = (c >> 16) & 0xFF
		g2 = (c >>  8) & 0xFF
		b2 =  c        & 0xFF
	else:
		# Color palette is in RGB tuple format
		r1 = c[0]
		g1 = c[1]
		b1 = c[2]
		c  = pal[hi4]
		r2 = c[0]
		g2 = c[1]
		b2 = c[2]

	if blend and lo4 > 0:
		a2 = (lo4 * 0x11) + 1 # upper weighting 1-256
		a1 = 257 - a2         # lower weighting 1-256
		if brightness == 255:
			return [(r1 * a1 + r2 * a2) >> 8,
				(g1 * a1 + g2 * a2) >> 8,
				(b1 * a1 + b2 * a2) >> 8]
		else:
			brightness += 1 # 1-256
			return [(r1 * a1 + r2 * a2) * brightness >> 16,
				(g1 * a1 + g2 * a2) * brightness >> 16,
				(b1 * a1 + b2 * a2) * brightness >> 16]
	else:
		if brightness == 255:
			return [ r1, g1, b1 ]
		else:
			brightness += 1
			return [(r1 * brightness) >> 8,
			        (g1 * brightness) >> 8,
			        (b1 * brightness) >> 8]


# This is named the same thing as FastLED's simpler HSV to RGB function
# (spectrum, vs rainbow) but implementation is a bit different for the
# sake of getting something running (adapted from some NeoPixel code).
# ACCEPTS: HSV color as a 3-element tuple [hue, saturation, value], each
#          in the range 0 to 255.
# RETURNS: RGB color as a 3-element tuple [R, G, B]
def hsv2rgb_spectrum(hsv):
	h = hsv[0] * 6.0 / 256.0  # 0.0 to <6.0
        s = int(h)                # Sextant number; 0 to 5
	n = int((h - s) * 255)    # 0-254 within sextant (NOT 255!)

	if s == 0:    r, g, b = 255  ,   n  , 0      # R to Y
	elif s == 1:  r, g, b = 254-n, 255  , 0      # Y to G
	elif s == 2:  r, g, b =   0  , 255  , n      # G to C
	elif s == 3:  r, g, b =   0  , 254-n, 255    # C to B
	elif s == 4:  r, g, b =   n  ,   0  , 255    # B to M
	else:         r, g, b = 255  ,   0  , 254-n  # M to R

	v1 = 1 + hsv[2]    # value 1 to 256; allows >>8 instead of /255
	s1 = 1 + hsv[1]    # saturation 1 to 256; same reason
	s2 = 255 - hsv[1]  # 255 to 0

	return [ (((((r * s1) >> 8) + s2) * v1) >> 8) & 0xFF,
	         (((((g * s1) >> 8) + s2) * v1) >> 8) & 0xFF,
	         (((((b * s1) >> 8) + s2) * v1) >> 8) & 0xFF ]
