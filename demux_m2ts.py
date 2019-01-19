import os
import re
import subprocess
import sys
from shutil import move

import numpy

import country_list
import demux
import split_video


def demux_m2ts(stdout, source, dest, oldcdw, start_num, pcm_to_flac_ans, twoch_to_flac_ans, name_chapters, eac3to_cmd,
               short_name, chapters_only):
    """ Demuxes using m2ts directly (not playlists) and split chapters automatically using video times """

    m2ts_arr = get_m2ts_order(stdout)
    m2ts_arr_paths = [os.path.join(source, "BDMV/STREAM/" + str(x) + ".m2ts") for x in m2ts_arr]
    print("Getting m2ts lengths...")
    m2ts_arr_paths_lengths = [(split_video.getLength(x), x) for x in m2ts_arr_paths if
                              split_video.getLength(x) != "N/A"]

    # Going to remove smaller m2ts from demuxing, likely to be credits.
    # Hopefully small extras or anything important wouldn't be included here.
    # If they were, they'll be removed. If not removed, they'd mess up episode numbering anyway
    m2ts_arr_paths_lengths = remove_outliers(m2ts_arr_paths_lengths)
    print("Chosen m2ts paths with lengths: {}\n".format(m2ts_arr_paths_lengths))

    if not chapters_only:
        demux.demux_loop(eac3to_cmd, "", dest, start_num, m2ts_arr_paths_lengths, twoch_to_flac_ans, short_name,
                        pcm_to_flac_ans, name_chapters, m2ts=True)

    playlist_output = first_playlist_string(eac3to_cmd, source, dest)
    found_chapters = do_chapters(eac3to_cmd, source, dest, short_name, start_num, name_chapters, m2ts_arr_paths_lengths,
                                 playlist_output)

    if not chapters_only:
        # Replace audio languages in files with audio language of munknown
        replace_languages(playlist_output, short_name, found_chapters)

        # lazy hack for eac3to path issue
        os.chdir(oldcdw)


def get_m2ts_order(strd):
    """ Returns m2ts order from the stdout, looking at the first playlist """

    pattern = re.compile(r"\[([0-9\+]+)\].m2ts")
    match = pattern.search(strd)
    if match:
        combo = match.group(1).rstrip()
        combo = combo.split("+")
        return [i.zfill(5) for i in combo]

    # other possible pattern
    pattern = re.compile(r"([0-9]+)\.m2ts")
    match = pattern.findall(strd)
    if match:
        return match

    print("Did not find m2ts in the first playlist, exiting")
    sys.exit(1)


def remove_outliers(arr):
    """ Removes outliers by comparing m2ts lengths """
    # arr from demux_m2ts is [(length, fullpath), (length, fullpath)] etc

    print("Removing outliers\n")
    new_arr = numpy.empty(len(arr))
    for count, ele in enumerate(arr):
        new_arr[count] = ele[0]

    mean = numpy.mean(new_arr, axis=0)
    sd = numpy.std(new_arr, axis=0)
    final_list = []

    # Check if within 2 stds, if not remove from list.
    for count, ele in enumerate(new_arr):
        if ele > mean - 2 * sd:
            # Also remove everything under 10 seconds... lazy fix to a std error, could probably be increased too
            if ele > 10:
                final_list.append((ele, arr[count][1]))
    return final_list


def do_chapters(eac3to_cmd, source, dest, short_name, start_num, name_chapters, m2ts_arr_paths_lengths, str_output):
    """ Since chapters are only in the playlist, special treatment. Returns true if found chapters, false if not"""

    print("Extracting chapter file from first playlist\n")

    # Run regex to get track number of the chapters (usually track 1)
    pattern = re.compile(r"([1-9])+: Chapters")
    match = pattern.search(str_output)
    if match:
        chap_track = match.group(1)
    else:
        print("Did not find chapters")
        return False

    # Get command ready to execute
    chap_name = "all_chapters" + "_" + short_name + ".txt"
    eac3to_cmd_execute = eac3to_cmd + " \"" + os.path.relpath(source,
                                                              start=dest) + "\" \"1)\" " + chap_track + ":" + chap_name + " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
    print(eac3to_cmd_execute)

    # Execute command, getting chapter file on disk
    demux.run_shell(eac3to_cmd_execute, stderr1=None)

    print("\nSplitting chapter file based on video times")

    # TODO: Might want to check if its on disk first
    # TODO: I am looking at m2ts times to do this. I already demuxed to h264, might use that
    # TODO: By calling split_by_video, I am getting m2ts times a second time, when I already did that
    #       in order to remove outliers.

    paths = [x[1] for x in m2ts_arr_paths_lengths]
    n_format = "chapters_{}_%n".format(short_name)

    if name_chapters:
        split_video.split_by_video(chap_name, True, paths, offset=int(start_num), file_name_format=n_format)
    else:
        split_video.split_by_video(chap_name, False, paths, offset=int(start_num), file_name_format=n_format)

    return True


def first_playlist_string(eac3to_cmd, source, dest):
    print("\nRunning command for info from first playlist...")
    cmd = eac3to_cmd + " \"" + os.path.relpath(source,
                                               start=dest) + "\" \"1)\" 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
    proc = demux.run_shell(cmd, stdout1=subprocess.PIPE)
    return proc.stdout.decode()


def replace_languages(str_output, short_name, found_chapters):
    """ Replaces unknown audio/sub languages, since m2ts files often don't have language info, just playlists.
     This currently does not work for audio/subs not present in the playlist, like one m2ts containing commentary
     but playlist eac3to output doesnt have that listed"""

    # Get muknown files
    search_str = ("(sub|aud)_{}_.*track([0-9]+).*munknown.*$").format(short_name)
    file_pattern = re.compile(search_str)
    list_of_files = list(filter(file_pattern.match, os.listdir(os.getcwd())))

    # Create dictionary from playlist info
    playlist_pattern = re.compile(r"([1-9])+: (.*?), ([a-zA-Z]+)")  # may need to add additional unicode letters like å
    match = playlist_pattern.findall(str_output)
    track_lang_dict = dict()
    for d in match:
        track_lang_dict[d[0]] = (d[1], d[2])

    # PROBLEM: since mpls has chapters, 1 extra track, so track numbers will be off. Check if chapters and adjust when needed.

    print("Adding languages to subtitle and audio track filenames")
    for i in list_of_files:
        f = file_pattern.search(i)

        type = f.group(1)
        track_num = f.group(2)
        if found_chapters:
            track_num = str(int(track_num) + 1)
        try:
            dict_info = track_lang_dict[track_num]
        except KeyError:
            print(
                "Error with the episode for {}, has an extra track, all track languages could be messed up so please manually check".format(
                    i))
            continue

        if (type == "sub" and "Subtitle" in dict_info[0]) or (type != "sub" and not ("Subtitle" in dict_info[0])):
            # doing the != since aud could be truehd, pgs, dts, etc and I didnt wanna list out rn

            country_code = [item[0] for item in country_list.iso_639_choices if item[1] == dict_info[1]]
            country_code = "".join(country_code)
            new_name = i.replace("munknown", country_code)
            print("Moving {0} to {1}".format(i, new_name))
            move(i, new_name)
