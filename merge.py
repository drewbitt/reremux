#!/usr/bin/python3
import subprocess
import os
import sys
import re
from collections import defaultdict


def create_episode_dict(short_name, dest):
    """ Separates each episode number into its own entry in the split_dict """

    # Reduce all files in destination to files with shortname
    pattern = "(vid|chapters|aud|sub)_{0}_((?!Log).)*$".format(short_name)
    pattern = re.compile(pattern)
    list_of_files = list(filter(pattern.match, os.listdir(dest)))

    # TODO: Make sure this works with just one episode to mux (i.e. a movie or individual episode)
    # if only one episode is found, maybe ask to name it without "01"?

    # split list of files into sublists for each episode
    split_dict = defaultdict(list)

    for file in list_of_files:
        # regex to just get episode number
        pattern = re.compile(".*?_.*?_([0-9]+)")
        episode_num = pattern.match(file).group(1)

        # add to dict
        split_dict[episode_num].append(file)

    return split_dict


def run_shell(cmd, stdout1=None):
    try:
        with open(os.devnull, "w") as f:
            proc = subprocess.run(cmd, shell=True, check=True, stderr=f, stdout=stdout1)
    except subprocess.CalledProcessError as ex:
        print(ex)
        sys.exit(1)
    return proc


def mkvmerge_string_dicts(sub_files_lang_dict, aud_files_lang_dict, check_signs_songs, mkvmerge_string, comp_str, dest):
    """ Adds audio and subs to the mkvmerge_string """

    # Audio first
    # Do english first in the muxing string
    for val in sorted(aud_files_lang_dict["en"]):
        mkvmerge_string += " {0} --language 0:{1} {2}".format(comp_str, "en", os.path.join(dest, val))

    # Then do other languages
    for key1, value1 in aud_files_lang_dict.items():
        if key1 != "en":
            for file in sorted(value1):
                mkvmerge_string += " {0} --language 0:{1} {2}".format(comp_str, key1, os.path.join(dest, file))

    # Subtitles
    for key1, value1 in sub_files_lang_dict.items():
        for count, val in enumerate(value1, 1):
            mkvmerge_string += " {0} --language 0:{1}".format(comp_str, key1)

            # Add sub track names if signs/songs is set
            if check_signs_songs:
                # Only do signs & songs for English for now
                if count == 1 and key1 == "en":
                    # not sure if I should make signs and songs forced here with --forced-track 0:true
                    mkvmerge_string += " --track-name 0:\"Signs & Songs\""
            # Add sub file
            mkvmerge_string += " {}".format(val)

    return mkvmerge_string


def compute_signs_and_songs(check_signs_songs, sub_files_lang_dict, dest):
    """ Computes signs and songs by comparing filesizes of subtitles and adjusts their order in the sub_files_lang_dict[lang_key] entry
        (meaning they're muxed first later) """

    for key1, value1 in sub_files_lang_dict.items():
        # If checking for signs and songs, check if language has 2 or more sub tracks and then add smallest in front
        if check_signs_songs:
            if len(value1) >= 2:
                filepaths = []
                for subf in value1:
                    # append size to a new list to sort by size
                    subf = os.path.join(dest, subf)
                    filepaths.append([subf, os.path.getsize(subf)])
                # smallest in the front
                filepaths.sort(key=lambda filename: filename[1], reverse=False)
                filepaths = [item[0] for item in filepaths]
                sub_files_lang_dict[key1] = filepaths
            else:
                print("Did not find two or more sub tracks in {} language".format(key1))
        else:
            # Still want the track ids to be in the right order
            sub_files_lang_dict[key1] = sorted(value1)

    return sub_files_lang_dict


def mux(short_name, series_name, dest):
    """Mux a specified short names files in destination directory using mkvmerge"""

    # Test mkvmerge
    try:
        # didn't know about python 3s use of run over call
        # also can't get it to work normally so going to concat into one string
        with open(os.devnull, "w") as f:
            subprocess.run(["mkvmerge", "-V"], check=True, stdout=f)
    except subprocess.CalledProcessError as ex:
        print(ex)
        print("mkvmerge error - may not have it installed")
        sys.exit(1)

    split_dict = create_episode_dict(short_name, dest)

    # Dict for each episode is created. Loop through and do mkvmerge commmands

    # Remember key is three digits with padded zeros. Check and see if three is really needed or just two
    pad_with_three = False
    for key in split_dict:
        if int(key.lstrip("0")) > 99:
            pad_with_three = True
            break

    print("For anime, auto-assign signs&songs and dialogue (looking at size)? (y/n)")
    check_signs_songs = input() == "y"

    all_mkvmerge_string = []
    for key, value in split_dict.items():
        if not pad_with_three:
            # pad with two instead of three. Yes, I know this is dumb, why even pad with three before?
            # cuz didn't write it to only pad with two before UNLESS it needed three in demux, always three instead
            ep_key = (key.lstrip("0")).rjust(2, "0")
        else:
            ep_key = key

        sub_files = [item for item in value if item.startswith("sub")]

        # Separate sub files based on language
        sub_files_lang_dict = make_dict_by_country(sub_files)
        # Calculate order in dict for signs and songs
        sub_files_lang_dict = compute_signs_and_songs(check_signs_songs, sub_files_lang_dict, dest)

        '''
        TODO: Always making English default right now. Ask for this
        TODO: Also I guess ask for subtitle titles if not signs and songs
        TODO: I am assuming h264. This is pretty much OK but wouldn't be OK for 4k, and I don't personally
              care enough to add in 4k batching ability at the moment
        '''

        vid_resolution_pattern = re.compile(".*_([0-9]+(i|p))")
        vid_resolution = vid_resolution_pattern.match(
            ''.join([item for item in value if item.startswith("vid")])).group(1)

        # aud_channels_pattern = re.compile(".*([0-9]+\.[0-9])")
        # aud_channels = aud_channels_pattern.match(''.join([item for item in value if item.startswith("aud")])).group(1)

        # If you want custom formatting you have to adjust this yourself. Screw actual usability!

        mkvmerge_string = "mkvmerge -o "

        # Create file name path
        mkvmerge_out_path = "\"{0} - {1} [Blu-ray {2} h264 ".format(series_name, ep_key, vid_resolution)
        if any(".truehd" in s for s in value):
            mkvmerge_out_path += "TrueHD"
        elif any(".flac" in s for s in value):
            mkvmerge_out_path += "FLAC"
        elif any(".dtsma" in s for s in value):
            mkvmerge_out_path += "DTS-HDMA"
        if any(".pcm" in s for s in value):
            mkvmerge_out_path += "PCM"
        comp_str = "--compression 0:none"
        mkvmerge_out_path += " REMUX].mkv\""
        mkvmerge_string += os.path.join(dest, mkvmerge_out_path)

        # Add chapters
        mkvmerge_string += " --chapters {}".format(
            os.path.join(dest, ''.join([item for item in value if item.startswith("chapters")])))
        # Add video
        mkvmerge_string += " {0} {1}".format(comp_str, os.path.join(dest, ''.join(
            [item for item in value if item.startswith("vid")])))

        # Add audio

        # First create dict by languages
        aud_files = [item for item in value if item.startswith("aud")]
        aud_files_lang_dict = make_dict_by_country(aud_files)

        # Do audio and subtitle dict work
        mkvmerge_string = mkvmerge_string_dicts(sub_files_lang_dict, aud_files_lang_dict, check_signs_songs,
                                                mkvmerge_string, comp_str, dest)

        print(mkvmerge_string)
        all_mkvmerge_string.append(mkvmerge_string)

    # outside of for-loop
    print("Continue to muxing? (y/n)")

    # Run actual muxing command
    if input() == "y":
        for m_str in all_mkvmerge_string:
            run_shell(m_str)
    print("Done muxing")


def make_dict_by_country(list_of_files):
    files_lang_dict = defaultdict(list)

    for file in list_of_files:
        pattern = re.compile(r".*([a-z]{2})\.")
        country = pattern.match(file).group(1)
        files_lang_dict[country].append(file)
    return files_lang_dict
