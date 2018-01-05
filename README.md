# Adafruit_CircuitPython_FancyLED
Helper functions to assist with porting FastLED Arduino projects to CircuitPython. This is NOT a complete port of FastLED, just a small subset of functions to get things moving. Also, as it's implemented in Python rather than C, it's not fast. The output of some functions (e.g. hsv2rgb_spectrum) may yield different results from FastLED. Aim here is just to have equivalent (ish) functions for the most oft-used calls, keeping the same names.

Currently-implemented functions include:

  * applyGamma_video()
  * napplyGamma_video()
  * fill_gradient_rgb()
  * loadDynamicGradientPalette()
  * ColorFromPalette()
  * hsv2rgb_spectrum()

### Roadmap

  * Always fit on Circuit Playground Express (.mpy format is fine) -- don't bloat up the code with every feature to the point that it only works on the highest-end boards! Just the most vital stuff.
  * Fix bugs as they're found.
  * Add more functions as they're needed (except where this would violate first item)
  * Improve performance where possible.
  * Improve compatibility with FastLED output where possible.
