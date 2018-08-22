#!/usr/bin/python3
import subprocess
import sys
import os
import re
import country_list
from split_chapters import split_file


def demux(eac3to_cmd, short_name, source, dest):
    """ Guided demux using eac3to """

    try:
        # didn't know about python 3s use of run over call
        # also can't get it to work normally so going to concat into one string
        cmd = eac3to_cmd + " \"" + source + "\"" + " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
        with open(os.devnull, "w") as f:
            subprocess.run(cmd, shell=True, check=True, stderr=f)
    except subprocess.CalledProcessError as ex:
        print(ex)
        print("Eac3to error on source")
        sys.exit(1)

    print("Choose the number / range of playlists to demux (i.e. 1 or 2-10)")
    range_playlist = input()

    print("Choose the number of the episode to start numbering at")
    start_num = input().rjust(3, "0")

    # Split for range

    # Remove space in case space was used for range
    range_playlist = range_playlist.replace(" ", "")
    # If input had "-", range, else just one playlist is specified
    if "-" in range_playlist:
        beg, last = range_playlist.split("-")
    else:
        beg, last = 1, 1

    print("If PCM is present, convert PCM to FLAC? (y/n)")
    pcm_to_flac_ans = input() == "y"

    print("If 2.0 is the only audio present, convert to FLAC? (y/n)")
    twoch_to_flac_ans = input() == "y"

    # TODO: Notice that there are no chapters but the first playlist has chapters, then ask
    #       to split BD chapters based off of video times automatically - splitBDchapters plus vid times

    print("Name chapters generic names (Chapter 01, Chapter 02 etc.)? (y/n)")
    name_chapters = input() == "y"

    # Loop eac3to
    for i in range(int(beg), int(last) + 1):
        cmd = eac3to_cmd + " \"" + source + "\" \"" + str(i) + ")\"" " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
        try:
            with open(os.devnull, "w") as f:
                proc = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=f)
        except subprocess.CalledProcessError as ex:
            print(ex)
            sys.exit(1)

        str_output = proc.stdout.decode()

        # Reduce the output down to what I need (the tracks)
        pattern = re.compile("([1-9])+: (.*)")
        all_matches = pattern.findall(str_output)

        # outer array that holds all filename information after looping for each track
        outer_arr = []

        convert_all_to_flac = False

        # check if we need to convert everything to flac if user specified this check for 2.0
        if twoch_to_flac_ans:
            convert_all_to_flac = True
            for k in all_matches:
                pattern = re.compile("[0-9]+\.[0-9] ")
                if pattern.search(k[1]) is not None and pattern.search(k[1]).group(0).strip() != "2.0":
                    convert_all_to_flac = False

        # loop for each track
        for k in all_matches:
            track_num = int(k[0])
            track_type = k[1]

            ''' The layout is:
            sub_shortName_episodeNum_subTrackNumber_countryCode.sup
            aud_shortName_episodeNum_channels_countryCode.ext
            vid_shortName_episodeNum_dimensions.h264
            chapters_shortName_episodeNum.txt
            '''

            if "Chapters" in track_type:
                to_add = "chapters" + "_" + short_name + "_" + start_num + ".txt"
            elif "h264" in track_type:
                # get dimensions
                pattern = re.compile(".*?, (.*?(i|p))")
                resolution = pattern.match(track_type).group(1)

                to_add = "vid" + "_" + short_name + "_" + start_num + "_" + resolution + ".h264"
            elif "PCM" in track_type or "TrueHD" in track_type or "DTS Master Audio" in track_type:
                # Get iso 639 country code from full name of country
                pattern = re.compile(".*?, (.*?), ([0-9]+\.[0-9])")
                match = pattern.match(track_type)
                country_code = [item[0] for item in country_list.iso_639_choices if item[1] == match.group(1)]
                channels = match.group(2)

                if convert_all_to_flac:
                    to_add = "aud" + "_" + short_name + "_" + start_num + "_" + channels + "_" + "".join(
                        country_code) + ".flac"
                elif "PCM" in track_type:
                    if pcm_to_flac_ans:
                        to_add = "aud" + "_" + short_name + "_" + start_num + "_" + channels + "_" + "".join(
                            country_code) + ".flac"
                    else:
                        to_add = "aud" + "_" + short_name + "_" + start_num + "_" + channels + "_" + "".join(
                            country_code) + ".pcm"
                elif "TrueHD" in track_type:
                    to_add = "aud" + "_" + short_name + "_" + start_num + "_" + channels + "_" + "".join(
                        country_code) + ".truehd"
                elif "DTS Master Audio" in track_type:
                    to_add = "aud" + "_" + short_name + "_" + start_num + "_" + channels + "_" + "".join(
                        country_code) + ".dts"
            elif "PGS" in track_type:
                pattern = re.compile("^.*?, ([a-zA-Z]*)")
                match = pattern.match(track_type).group(1)
                country_code = [item[0] for item in country_list.iso_639_choices if item[1] == match]

                to_add = "sub" + "_" + short_name + "_" + start_num + "_track" + str(track_num) + "_" + "".join(
                    country_code) + ".sup"
            outer_arr.append([track_num, to_add])

        # Prepare eac3to outside of track loop but in playlist loop

        # eac3to breaks with absolute paths AND doesnt have the ability to set a destination folder for muxing
        # so this is gonna get messy

        source = os.path.abspath(source)
        # Can't do different folder natively in eac3to it seems - need to change cwd
        oldcdw = os.getcwd()
        os.chdir(dest)

        # Write command
        eac3to_cmd_execute = eac3to_cmd + " \"" + os.path.relpath(source, start=dest) + "\" \"" + str(
            i) + ")\" "

        for entry in outer_arr:
            eac3to_cmd_execute += str(entry[0]) + ":" + entry[1] + " "
        eac3to_cmd_execute += " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
        print(eac3to_cmd_execute)
        # Execute command
        try:
            with open(os.devnull, "w") as f:
                subprocess.run(eac3to_cmd_execute, shell=True, check=True, stderr=f)
        except subprocess.CalledProcessError as ex:
            print(ex)
            print("Eac3to error when demuxing")
            # probably should terminate here
            sys.exit(1)

        # Now that chapter file has been created, add chapter titles if requested
        if name_chapters:
            for entry in outer_arr:
                if entry[1].startswith("chapters"):
                    split_file(entry[1], "", True, "")
                    break  # should only be one chapter file but eh oh well

        # Start num is converted to a string to have padding of 0s
        # Increase start num (i.e. episode number) by one every loop iteration
        if start_num.isnumeric(): start_num = str(int(start_num) + 1).rjust(3, "0")

        # lazy hack for eac3to path issue
        os.chdir(oldcdw)
