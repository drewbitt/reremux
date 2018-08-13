#!/usr/bin/python3
import subprocess
import sys
import os
from argparse import ArgumentParser
import demux
import merge

# Define your eac3to and wine path
eac3to_cmd = "wine ~/Documents/Scripts/eac3to/eac3to.exe"

# Test eac3to
try:
    with open(os.devnull, "w") as f:
        proc = subprocess.call([eac3to_cmd, "2>/dev/null"], shell=True, stdout=f, stderr=f)
        if proc != 0:
            print("Returned error on user-defined eac3to & wine path")
            sys.exit(1)
except subprocess.CalledProcessError as ex:
    print(ex)
    sys.exit(1)

parser = ArgumentParser(
    "Define what I do"
)
parser.add_argument('srcdest', metavar="src dest", type=str, nargs="+")
parser.add_argument("--mux-only", dest="mux_only", nargs="?", const="True", help="Only mux and don't demux from BDMV. Ignores source if set")
args = parser.parse_args()

source = (args.srcdest)[0]
dest = (args.srcdest)[1]

# Check if BDMV folder exists
err = True
# Try block for if the folder doesn't exist
try:
    for _, dirs, _ in os.walk(source):
        for d in dirs:
            if (d == "BDMV"): err = False
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

demux.demux(eac3to_cmd, series_name, os.path.normpath(source), os.path.normpath(dest))
