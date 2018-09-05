#!/usr/bin/python3
import subprocess
import sys
import os
import random
from argparse import ArgumentParser
import demux
import merge

# Define your eac3to and wine path
eac3to_cmd = "wine ~/Documents/Scripts/eac3to/eac3to.exe"

# Test eac3to
try:
    with open(os.devnull, "w") as f:
        subprocess.run([eac3to_cmd, "2>/dev/null"], shell=True, check=True, stdout=f, stderr=f)
except subprocess.CalledProcessError as ex:
    print(ex)
    print("Error with wine and eac3to path")
    sys.exit(1)

# Define what the program does
parser = ArgumentParser("Remuxin' with eac3to and mkvmerge in *nix CLI")

parser.add_argument('srcdest', metavar="src dest", type=str, nargs="+")
parser.add_argument("--mux-only", dest="mux_only", nargs="?", const="True",
                    help="Only mux and don't demux from BDMV. Ignores source if set")

# TODO: Actually ignore source if --mux-only is set
# Looking it up online this looks tough to do - optionally require an argument unless a different argument is specified

args = parser.parse_args()

source = args.srcdest[0]
dest = args.srcdest[1]

if not args.mux_only:
    # Check if BDMV folder exists
    err = True
    # Try block for if the folder doesn't exist
    try:
        for _, dirs, _ in os.walk(source):
            for d in dirs:
                if d == "BDMV":
                    err = False
    except OSError as ex:
        print(ex)
        print("Probably either the folder doesn't exist or you have the wrong permissions for the folder")
        sys.exit(1)

    if (err):
        print("BDMV folder not found")
        sys.exit(1)

    # Check if permissions are OK. What a pointless check
    BDMV_path = os.path.join(source, "BDMV")
    if not (os.access(BDMV_path, os.R_OK) and os.access(BDMV_path, os.X_OK)):
        print("Not correct permissions in BDMV folder")
        sys.exit(1)

    # Check for destination path, the permissions thing above is dumb so I won't do that
    if not (os.path.isdir(dest)):
        print("Destination path doesn't exist")
        sys.exit(1)

    print("Input series name")
    series_name = input()

    # Get short name for use in naming files - makes it probably unique as well
    # TODO: I don't like this. Don't know what you got with non-words. Would rather have first whole word.
    short_name = ''.join(random.choice(series_name.replace(" ", "")) for x in range(6))

    demux.demux(eac3to_cmd, short_name, os.path.normpath(source), os.path.normpath(dest))
    # Demux will exit right now on errors so no need to check for anything. Just going to go off of the shortname we have
    # and the files that exist in the destination directory.

    print("Done demuxing")
    print("Continue to muxing? (y/n)")
    muxing_continue = input() == "y"

    if muxing_continue:
        # just gonna assume mkvmerge is installed in a normal way and not create a passed var for its location
        merge.mux(short_name, series_name, os.path.normpath(dest))
else:
    print("Input short name for all files (i.e. in the filename, type_shortNameIsHere_*.ext)")
    short_name = input()
    print("Input name you want to name the series/movie")
    series_name = input()
    merge.mux(short_name, series_name, os.path.normpath(dest))
