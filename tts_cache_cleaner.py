#!/usr/bin/env python
"""
TTS Cache Cleaner!
"""

import json
import multiprocessing
import os
import pathlib
import re
import sys
import time
from collections import defaultdict
from itertools import chain
from time import gmtime, strftime

# If your Tabletop Simulator data directory is in some alternative location,
# paste it in the quotes below.
TTS_DIR_OVERRIDE = r""


def tts_default_locations():
    """Attempt to guess the Tabletop Simulator data directory."""
    if sys.platform == "linux" or sys.platform == "linux2":
        return [
            os.path.join(
                str(pathlib.Path.home()),
                ".local",
                "share",
                "Tabletop Simulator",
            )
        ]
    elif sys.platform == "darwin":  # mac osx
        return [
            os.path.join(
                str(pathlib.Path.home()), "Library", "Tabletop Simulator"
            )
        ]
    elif sys.platform == "win32":
        return [
            os.path.join(
                os.environ["USERPROFILE"],
                "Documents",
                "My Games",
                "Tabletop Simulator",
            ),
            os.path.join(
                os.environ["USERPROFILE"],
                "OneDrive",
                "Documents",
                "My Games",
                "Tabletop Simulator",
            ),
        ]
    else:
        return [
            f"couldn't match platform {sys.platform}, so don't know save game location"
        ]


def read_file(filename):
    infile = open(filename, mode="r", encoding="utf-8")
    intext = infile.read()
    infile.close()
    return intext


def _urls_from_json_obj(obj, url_set):
    if isinstance(obj, str):
        if obj.startswith("http"):
            url_set.add(obj)
        if '"' in obj:
            for s in re.findall('"(http[^"]+)"', obj):
                url_set.add(s)
        if "'" in obj:
            for s in re.findall("'(http[^']+)'", obj):
                url_set.add(s)
    elif isinstance(obj, dict):
        for v in obj.values():
            _urls_from_json_obj(v, url_set)
    elif isinstance(obj, list):
        for item in obj:
            _urls_from_json_obj(item, url_set)


def urls_from_file(filename):
    url_set = set()
    _urls_from_json_obj(json.loads(read_file(filename)), url_set)
    return url_set


def urls_from_dir(dirname, pool=None):
    seen_paths = []
    for root, dirs, files in os.walk(dirname):
        for filename in files:
            if filename.endswith(".json"):
                full_path = os.path.join(root, filename)
                seen_paths.append(full_path)
    print(f"Found {len(seen_paths)} json files to examine.")
    url_set = set()
    if pool:
        for set2 in pool.map(urls_from_file, seen_paths):
            url_set.update(set2)
    else:
        for path in seen_paths:
            url_set.update(urls_from_file(path))
    return url_set


def urls_from_thing(path, pool=None):
    if os.path.isfile(path):
        return urls_from_file(path)
    elif os.path.isdir(path):
        return urls_from_dir(path, pool=pool)
    else:
        print("File or directory not found; skipping.")
        return set()


def url_to_cache_fnames(url):
    s = re.sub(r"[^a-zA-Z0-9]", "", url)
    l = [s]
    if s.startswith("httpcloud3steamusercontentcom"):
        l.append("httpssteamusercontentaakamaihdnet" + s[29:])
    elif s.startswith("httpssteamusercontentaakamaihdnet"):
        l.append("httpcloud3steamusercontentcom" + s[33:])
    return l


def examine_cache(tts_base_dirs, expected_cache_fnames):
    cache_mid_dirs = [
        "Assetbundles",
        "Audio",
        "Images",
        "Images Raw",
        "Models",
        "Models Raw",
        "PDF",
    ]
    cache_dirs = []
    for base_dir in tts_base_dirs:
        for cache_mid_dir in cache_mid_dirs:
            path = os.path.join(base_dir, "Mods", cache_mid_dir)
            if os.path.isdir(path):
                cache_dirs.append(path)
    cache_dirs.sort()
    cache_files = defaultdict(list)
    cache_unreferenced = defaultdict(list)
    for cache_dir in cache_dirs:
        for root, dirs, files in os.walk(cache_dir):
            for file in files:
                cache_files[cache_dir].append(os.path.join(root, file))
        cache_files[cache_dir].sort()
        for file_path in cache_files[cache_dir]:
            fname, ext = os.path.splitext(os.path.basename(file_path))
            if fname not in expected_cache_fnames:
                cache_unreferenced[cache_dir].append(file_path)
        cache_unreferenced[cache_dir].sort()
    for cache_dir in cache_dirs:
        print(cache_dir)
        print(
            "^ contains",
            len(cache_files[cache_dir]),
            "files, of which",
            len(cache_unreferenced[cache_dir]),
            "are not referenced.",
        )
    all_unreferenced_files = sorted(
        chain.from_iterable(cache_unreferenced.values())
    )
    for base_dir in tts_base_dirs:
        if not os.path.isdir(base_dir):
            continue
        report_path = os.path.join(base_dir, "unreferenced_cache_files.txt")
        f = open(report_path, "w")
        f.write("\n".join(all_unreferenced_files) + "\n")
        f.close()
        print(
            "Wrote list of",
            len(all_unreferenced_files),
            "unreferenced cache files to",
            report_path,
        )
    return all_unreferenced_files


if __name__ == "__main__":
    things = list(sys.argv[1:])
    if not things:
        if TTS_DIR_OVERRIDE:
            things = [TTS_DIR_OVERRIDE]
            print(
                f"No arguments given, so looking at TTS data dir {TTS_DIR_OVERRIDE}\nYou can change this by editing the script's value in TTS_DIR_OVERRIDE"
            )
        else:
            things = tts_default_locations()
            print(
                f"No arguments given, so guessing at TTS default data dir(s).\nYou can change this by editing the script's value in TTS_DIR_OVERRIDE"
            )
    url_set = set()
    with multiprocessing.Pool() as pool:
        for item in things:
            print(
                strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
                "Examining URLs in ",
                item,
            )
            url_set.update(urls_from_thing(item, pool=pool))
    print(
        strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
        "Found",
        len(url_set),
        "URLs referenced",
    )
    expected_cache_fnames = set()
    for url in url_set:
        expected_cache_fnames.update(url_to_cache_fnames(url))
    all_unreferenced_files = examine_cache(things, expected_cache_fnames)
    print(strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()), "Done examining cache.")
    if all_unreferenced_files:
        print(
            "Would you like to delete the",
            len(all_unreferenced_files),
            "unreferenced cache files? (y/n [enter])",
        )
        yn = input()
        if yn.lower().startswith("y"):
            print(strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()), "Deleting...")
            for file_path in all_unreferenced_files:
                os.remove(file_path)
    print(
        strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()), "Done. Press enter to exit."
    )
    input()
