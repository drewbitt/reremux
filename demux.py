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
            proc = subprocess.run(cmd, shell=True, check=True, stderr=f)
    except subprocess.CalledProcessError as ex:
        print(ex)
        print("Eac3to error on source")
        sys.exit(1)

    print("Choose the number / range of playlists to demux (i.e. 1 or 2-10)")
    range_playlist = input()

    if len(range_playlist) > 2:
        # It's a range and not a number
        print("Choose the number of the episode to start numbering at")
        start_num = int(input())

        # Also remove space in case they did a range with a space and get range numbers
        range_playlist = range_playlist.replace(" ", "")
        beg, last = range_playlist.split("-")
    else:
        start_num = "1episode"
        beg, last = 1, 1

    print("If PCM is present, convert PCM to FLAC? (y/n)")
    pcm_to_flac_ans = input()

    print("If 2.0 is the only audio present, convert to FLAC? (y/n)")
    twoch_to_flac_ans = input()

    # Loop eac3to

    for i in range(int(beg), int(last)+1):
        cmd = eac3to_cmd + " \"" + source + "\" \"" + str(i) + ")\"" " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
        with open(os.devnull, "w") as f:
            proc = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=f)
            print(proc.stdout.decode())