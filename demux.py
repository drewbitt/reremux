#!/usr/bin/python3
import subprocess
import sys
import os
import re
import random
import country_list

def demux(eac3to_cmd, name, source, dest):

    # Get short name for use in naming files - makes it probably unique as well
    short_name = ''.join(random.choice(name.replace(" ", "")) for x in range(6))

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
        # If > 2, it's a range and not a number (we will assume it's not a string, else you'll get an error when
        # splitting below if it doesn't have a "-", or an error will occur when looping eac3to with the beg, last range)
        print("Choose the number of the episode to start numbering at")
        start_num = input()
        if len(start_num) == 1:
            start_num = "0" + start_num

        # Also remove space in case they did a range with a space and get range numbers
        range_playlist = range_playlist.replace(" ", "")
        beg, last = range_playlist.split("-")
    else:
        start_num = "main"
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
            str_output = proc.stdout.decode()

            # Reduce the output down to what I need
            pattern = re.compile("([1-9])+: (.*)")
            all_matches = pattern.findall(str_output)

            outer_arr = []

            convert_all_to_flac = True
            if twoch_to_flac_ans == "y":
                for k in all_matches:
                    pattern = re.compile("[0-9]+\.[0-9] ")
                    if pattern.search(k[1]) is not None and pattern.search(k[1]).group(0).strip() != "2.0":
                        convert_all_to_flac = False

            # loop for each track
            for counter, k in enumerate(all_matches):
                line_num = int(k[0])
                track_type = k[1]

                print(track_type)

                if "Chapters" in track_type:
                    to_add = "chapters" + "_" + short_name + "_" + start_num + ".txt"
                elif "h264" in track_type:
                    to_add = "vid" + "_" + short_name + "_" + start_num + ".h264"
                elif "PCM" in track_type:
                    if pcm_to_flac_ans == "y" or convert_all_to_flac:
                        to_add = "aud" + "_" + short_name + "_" + start_num + ".flac"
                    else:
                        to_add = "aud" + "_" + short_name + "_" + start_num + ".pcm"
                elif "TrueHD" in track_type:
                    if convert_all_to_flac:
                        to_add = "aud" + "_" + short_name + "_" + start_num + ".flac"
                    else:
                        to_add = "aud" + "_" + short_name + "_" + start_num + ".truehd"
                elif "DTS Master Audio" in track_type:
                    if convert_all_to_flac:
                        to_add = "aud" + "_" + short_name + "_" + start_num + ".flac"
                    else:
                        to_add = "aud" + "_" + short_name + "_" + start_num + ".dts"
                elif "PGS" in track_type:
                    # get language here
                    to_add = "sub" + "_" + short_name + "_" + start_num + "_track" + str(counter) + ".sup"
                outer_arr.append([line_num, to_add])

            print(outer_arr)
