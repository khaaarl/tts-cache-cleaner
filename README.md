# tts-cache-cleaner

This is a relatively simple Python script that looks through your Tabletop Simulator (TTS) save files, saved objects, and subscribed workshop mods to see what URLs they reference, then looks through your TTS cached files to see what cached files don't correspond to any URL you are still using. It writes the list of unreferenced cache files to a .txt file for you to examine if you wish. It then asks you whether it should delete the unreferenced cache files for you.

## How to use:

1. Have Python installed: https://www.python.org/downloads/
2. Have the `tts_cache_cleaner.py` script somewhere on your computer. Double-click it to run. You should see a window with text in it, it should work for a while, then tell you to press enter to exit.
    2a. If the window doesn't show up or shows up for just a split second, you have some sort of permissions problem specific to your computer, and you might need to google for how to run a python script from the internet.
3. If you run the script on its own, it will attempt to guess your TTS data folder and examine everything in it. If it does not find the correct directory, you can put the preferred path into TTS_DIR_OVERRIDE.

## FAQ:

Q: Will this work with ForceOrg, which uses a nonstandard method of storing objects?

A: Yes; to determine which URLs are in use, it both looks for strings in the .json files that start with 'http' and also substrings that look like URLs in single or double quotes within those strings. That should cover most bespoke "smart" bag implementations, including that of ForceOrg's tiles.
