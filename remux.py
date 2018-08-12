import subprocess
import sys
import os
from argparse import ArgumentParser
import demux
import merge

# Define your eac3to and wine path
eac3to_cmd = ""

# Test eac3to
try:
    proc = subprocess.call([eac3to_cmd, "2>/dev/null"], shell=True)
    if proc != 0:
        print("Returned error on user-defined eac3to & wine path")
        sys.exit(1)
except subprocess.CalledProcessError as ex:
    print(ex)
    sys.exit(1)

parser = ArgumentParser(
    "Define what I do"
)
parser.add_argument('source', type=str, help="BDMV source")
parser.add_argument("dest", type=str, help="Destination for demuxed files")
args = parser.parser_args()

# Check if BDMV folder exists
err = True
# Try block for if the folder doesn't exist
try:
    for _, dirs, _ in os.walk(args.source):
        if dirs == "BDMV":
            err=False
except OSError as ex:
    print(ex)
    print("Probably either the folder doesn't exist or you have the wrong permissions for the folder")
    sys.exit(1)

if (err):
    print("BDMV folder not found")
    sys.exit(1)

# Check if permissions are OK. What a pointless check
BDMV_path = os.path.join(args.source, "BDMV")
if not (os.access(BDMV_path, os.R_OK) and os.access(BDMV_path, os.X_OK)):
    print("Not correct permissions in BDMV folder")
    sys.exit(1)

# Check for destination path, the permissions thing above is dumb so I won't do that
if not (os.access(args.dest, os.F_OK)):
    print("Destination path doesn't exist")
    sys.exit(1)

demux(eac3to_cmd, args.source, args.dest)








