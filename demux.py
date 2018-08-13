#!/usr/bin/python3
import subprocess
import sys
import os

def demux(eac3to_cmd, name, source, dest):
    try:
        # didn't know about python 3s use of run over call
        # also can't get it to work normally so going to concat into one string
        cmd = eac3to_cmd + " \"" + source + "\"" + " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
        with open(os.devnull, "w") as f:
            proc = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=f, universal_newlines=True)
    except subprocess.CalledProcessError as ex:
        print(ex)
        print("Eac3to error on source")
        sys.exit(1)

    print("Choose the range of playlists to demux (i.e. 2-10)")
    range = input()
    print("Choose the episode number to start numbering at")
    start_num = input()
    print("If PCM is present, convert PCM to FLAC? (y/n)")
    pcm_to_flac_ans = input()
