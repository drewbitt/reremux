import os
import re
import subprocess
import sys

import numpy

import split_video
import demux


def demux_m2ts(stdout, source, dest, start_num, pcm_to_flac_ans, twoch_to_flac_ans, name_chapters, eac3to_cmd,
               short_name):
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

    demux_m2ts(eac3to_cmd, source, dest, start_num, m2ts_arr_paths_lengths, twoch_to_flac_ans, short_name,
               pcm_to_flac_ans, name_chapters, m2ts=True)

    do_chapters(eac3to_cmd, source, dest, short_name, start_num, name_chapters, m2ts_arr_paths_lengths)


def get_m2ts_order(strd):
    """ Returns m2ts order from the stdout, looking at the first playlist """

    pattern = re.compile(r"\[([0-9\+]+)\].m2ts")
    match = pattern.search(strd)
    if match:
        combo = match.group(1).rstrip()
        combo = combo.split("+")
        return [i.zfill(5) for i in combo]
    print("Did not find m2ts in the first playlist, exiting")
    sys.exit(1)


def remove_outliers(arr):
    """ Removes outliers by comparing m2ts lengths """

    # arr from demux_m2ts is [(length, fullpath), (length, fullpath)] etc
    new_arr = numpy.empty(len(arr))
    for count, ele in enumerate(arr):
        new_arr[count] = ele[0]

    mean = numpy.mean(new_arr, axis=0)
    sd = numpy.std(new_arr, axis=0)
    final_list = []

    # Check if within 2 stds, if not remove from list.
    for count, ele in enumerate(new_arr):
        if ele > mean - 2 * sd:
            final_list.append((ele, arr[count][1]))
    return final_list


def do_chapters(eac3to_cmd, source, dest, short_name, start_num, name_chapters, m2ts_arr_paths_lengths):
    """ Since chapters are only in the playlist, special treatment """

    # Get info of first playlist
    cmd = eac3to_cmd + " \"" + os.path.relpath(source,
                                               start=dest) + "\" \"1)\" 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
    proc = demux.run_shell(cmd, stdout1=subprocess.PIPE)
    str_output = proc.stdout.decode()

    # Run regex to get track number of the chapters (usually track 1)
    pattern = re.compile(r"([1-9])+: Chapters")
    match = pattern.search(str_output)

    # Get command ready to execute
    chap_name = "all_chapters" + "_" + short_name + ".txt"
    eac3to_cmd_execute = eac3to_cmd + " \"" + os.path.relpath(source, start=dest) + "\" \"1)\" " + match[
        0] + ":" + chap_name + " 2>/dev/null | tr -cd \"\\11\\12\\15\\40-\\176\""
    print(eac3to_cmd_execute)

    # Execute command, getting chapter file on disk
    demux.run_shell(eac3to_cmd_execute, stderr1="")

    # TODO: Might want to check if its on disk first

    paths = [x[1] for x in m2ts_arr_paths_lengths]
    n_format = "chapters_{}_%n".format(short_name)

    if name_chapters:
        split_video.split_by_video(chap_name, True, paths, offset=start_num, file_name_format=n_format)
    else:
        split_video.split_by_video(chap_name, False, paths, offset=start_num, file_name_format=n_format)
