import os
import re
import sys

import numpy

import split_video


def demux_m2ts(stdout, source, dest, start_num, pcm_to_flac_ans, twoch_to_flac_ans, name_chapters):
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

    # Start demuxing


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
