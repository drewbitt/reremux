#!/usr/bin/python3
import subprocess
import sys
import os
import re
import country_list
from split_chapters import split_file
from demux_m2ts import demux_m2ts


def ask_stuff():
    """ Ask for various settings (guided remux) """

    # May want to do some smart asking (looking at eac3to output) to reduce potential choices
    print('1) Specify and demux playlists 2) Demux in order of m2ts in first playlist 3) Demux based on m2ts order (using playlists) 4) Demux based on the m2ts in the first playlist (directly) ?')
    playlist_ordering = int(input()[0])

    if playlist_ordering == 1:
        print("Choose the number / range of playlists to demux (i.e. 1 or 2-10)")
        range_playlist = input()
    else:
        range_playlist = "doesn't matter"

    print("Choose the number of the episode to start numbering files at ")
    start_num = input().rjust(3, "0")

    print("If PCM is present, convert PCM to FLAC? (y/n)")
    pcm_to_flac_ans = input() == "y"

    print("If 2.0 is the only audio present, convert to FLAC? (y/n)")
    twoch_to_flac_ans = input() == "y"

    print("Name chapters generic names (Chapter 01, Chapter 02 etc.)? (y/n)")
    name_chapters = input() == "y"

    return range_playlist, start_num, playlist_ordering, pcm_to_flac_ans, twoch_to_flac_ans, name_chapters


def calculate_range(range_playlist):
    """ From user input, get a range of the playlists to loop over """
    range_playlist = range_playlist.replace(" ", "")
    # If input had "-", range, else just one playlist is specified
    if "-" in range_playlist:
        beg, last = range_playlist.split("-")
    elif "," in range_playlist:
        # TODO: Allow for list of playlists, just requires a rewrite to be from a loop
        #       that is strictly a range, to a loop that is either a range or a for-loop over a list
        print("Currently not supporting not single playlists or ranges")
        sys.exit(1)
    else:
        beg, last = range_playlist, range_playlist

    return int(beg), int(last)+1


def run_shell(cmd, stdout1=None, stdin1=None, stderr1="default"):
    """ Run given cmd in the system using subprocess.run and return the CompletedProcess """
    try:
        with open(os.devnull, "w") as f:
            if stderr1 == "default":
                stderr1 = f
            proc = subprocess.run(cmd, shell=True, check=True, stderr=stderr1, stdout=stdout1, stdin=stdin1)
    except subprocess.CalledProcessError as ex:
        print(ex)
        sys.exit(1)
    return proc


def check_twoch_flac(all_matches):
    """ Calculate if everything is two channels, and if so, set that everything be converted to FLAC """
    convert_all_to_flac = True
    for k in all_matches:
        pattern = re.compile(r"[0-9]+\.[0-9] ")
        if pattern.search(k[1]) is not None and pattern.search(k[1]).group(0).strip() != "2.0":
            convert_all_to_flac = False
    return convert_all_to_flac


def name_chaps(outer_arr):
    """ Calls split_chapters to add generic names to chapters """
    for entry in outer_arr:
        if entry[1].startswith("chapters"):
            split_file(entry[1], "", True, "")
            break  # should only be one chapter file but eh oh well


def calculate_m2ts_order(strd):
    """ Gets m2ts order (looking at the first playlist) and muxes their respective playlists in the new order,
        instead of the order of playlists """

    # Get first playlist [01+02+etc].m2ts ordering
    pattern = re.compile(r"\[([0-9\+]+)\].m2ts")
    match = pattern.search(strd)

    if match:
        combo = match.group(1).rstrip()
        combo = combo.split("+")

        # combo now is the m2ts numbers, 1 or two digits

        return_arr = []
        for i in combo:
            # find the playlist for the m2ts
            pattern = re.compile(r"([0-9]+)\).*{}\.m2ts.*".format(i.zfill(5)))
            match = pattern.search(strd)
            if match:
                return_arr.append(match.group(1))
        return return_arr
    print("Did not find m2ts in the first playlist, exiting")
    sys.exit(1)


def overall_m2ts_order(strd):
    """ Gets m2ts order by looking at all the m2ts in the playlists and determining the order. Pretty much the same as calculate_m2ts_order
    but works when the first playlist doesn't have the order as well. May be able to get rid of calculate_m2ts_order.
    TODO: This would not work for any playlists with multiple m2ts right now"""

    # get all the m2ts in the playlists
    pattern = re.compile(r"([0-9]+).*\.mpls, ([0-9]+)\.m2ts")
    match = pattern.findall(strd)

    return_arr = []
    if match:
        match_m2ts_num = [m[1] for m in match]

        for mat in sorted(match_m2ts_num):
            return_arr.append(''.join([m[0] for m in match if m[1] == mat]))
        return return_arr
    print("Error getting overall m2ts order")
    sys.exit(1)

def change_dirs(source, dest):
    """ Fix for eac3to to save files in an alternate destination. Also sets absolute paths so that we can get relative
        paths later, needed for eac3to afaik """
    source = os.path.abspath(source)
    dest = os.path.abspath(dest)
    # Can't do different folder natively in eac3to it seems - need to change cwd
    oldcdw = os.getcwd()
    os.chdir(dest)

    return source, dest, oldcdw


def demux(eac3to_cmd, short_name, source, dest):
    """ Guided demux using eac3to """

    cmd = eac3to_cmd + " \"" + source + "\"" + " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
    proc = run_shell(cmd, stdout1=subprocess.PIPE)
    print(proc.stdout.decode())

    # Because eac3to and paths sucks, change cdw
    source, dest, oldcdw = change_dirs(source, dest)

    # Prompt the user for various things (guided remux)
    range_playlist, start_num, playlist_ordering, pcm_to_flac_ans, twoch_to_flac_ans, name_chapters = ask_stuff()

    if playlist_ordering == 1:
        # Split range and calulate it for loop from input
        beg, last = calculate_range(range_playlist)
        order = range(beg, last)
    elif playlist_ordering == 2:
        order = calculate_m2ts_order(proc.stdout.decode())
    elif playlist_ordering == 3:
        order = overall_m2ts_order(proc.stdout.decode())
    elif playlist_ordering == 4:
        return demux_m2ts(proc.stdout.decode(), source, dest, start_num, pcm_to_flac_ans, twoch_to_flac_ans, name_chapters)

    # Loop eac3to
    for i in order:
        cmd = eac3to_cmd + " \"" + os.path.relpath(source, start=dest) + "\" \"" + str(i) + ")\"" " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
        proc = run_shell(cmd, stdout1=subprocess.PIPE)
        str_output = proc.stdout.decode()

        # Reduce the output down to what I need (the tracks)
        pattern = re.compile(r"([1-9])+: (.*)")
        all_matches = pattern.findall(str_output)

        # outer array that holds all filename information after looping for each track
        outer_arr = []

        # check if we need to convert everything to flac if user specified this check for 2.0
        convert_all_to_flac = False
        if twoch_to_flac_ans:
            convert_all_to_flac = check_twoch_flac(all_matches)

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
                pattern = re.compile(r".*?, (.*?(i|p))")
                resolution = pattern.match(track_type).group(1)

                to_add = "vid" + "_" + short_name + "_" + start_num + "_" + resolution + ".h264"
            elif "PCM" in track_type or "TrueHD" in track_type or "DTS Master Audio" in track_type:
                # Get iso 639 country code from full name of country
                pattern = re.compile(r".*?, (.*?), ([0-9]+\.[0-9])")
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
                        country_code) + ".dtsma"
            elif "PGS" in track_type:
                pattern = re.compile(r"^.*?, ([a-zA-Z]*)")
                match = pattern.match(track_type).group(1)
                country_code = [item[0] for item in country_list.iso_639_choices if item[1] == match]

                to_add = "sub" + "_" + short_name + "_" + start_num + "_track" + str(track_num) + "_" + "".join(
                    country_code) + ".sup"
            outer_arr.append([track_num, to_add])

        # Prepare eac3to outside of track loop but in playlist loop

        # Write command
        eac3to_cmd_execute = eac3to_cmd + " \"" + os.path.relpath(source, start=dest) + "\" \"" + str(
            i) + ")\" "
        for entry in outer_arr:
            eac3to_cmd_execute += str(entry[0]) + ":" + entry[1] + " "
        eac3to_cmd_execute += " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""

        # Print and execute command
        print(eac3to_cmd_execute)
        run_shell(eac3to_cmd_execute, stderr1=None)

        # Now that chapter file has been created, add chapter titles if requested
        if name_chapters:
            name_chaps(outer_arr)

        # Start num is converted to a string to have padding of 0s
        # Increase start num (i.e. episode number) by one every loop iteration
        if start_num.isnumeric(): start_num = str(int(start_num) + 1).rjust(3, "0")
    # lazy hack for eac3to path issue
    os.chdir(oldcdw)
