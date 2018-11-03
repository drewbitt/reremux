#!/usr/bin/python3
import os
import re
import subprocess
import sys
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


def create_dict_by_country(list_of_files):
    """ Creates a dict from a list of files, using each files language as a key
        Also returns notice, which is False unless there are multiple files of the same language, and is used
        elsewhere to notify the user (so they can change title for commentary or whatever) """

    files_lang_dict = defaultdict(list)

    # var set if multiple files of same language exist (possibly need to change merging string for titles)
    notice = False

    for file in list_of_files:
        pattern = re.compile(r".*([a-z]{2})\.")
        country = pattern.match(file).group(1)
        files_lang_dict[country].append(file)
        # Check if multiple audio files for a single language and return notice if so
        if len(files_lang_dict[country]) == 2:
            notice = country
    return notice, files_lang_dict


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
            mkvmerge_string += " {}".format(os.path.join(dest, val))

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
                    filepaths.append([subf, os.path.getsize(os.path.join(dest, subf))])
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


def pad_three(split_dict):
    """ Returns boolean. Remember key is three digits with padded zeros. Check and see if three is really needed or just two """
    for key in split_dict:
        if int(key.lstrip("0")) > 99:
            return True
    return False


def mux(short_name, series_name, dest):
    """Mux a specified short names files in destination directory using mkvmerge"""

    # Test mkvmerge
    try:
        with open(os.devnull, "w") as f:
            subprocess.run(["mkvmerge", "-V"], check=True, stdout=f)
    except subprocess.CalledProcessError as ex:
        print(ex)
        print("mkvmerge error - may not have it installed")
        sys.exit(1)

    split_dict = create_episode_dict(short_name, dest)

    # Dict for each episode is created. Loop through and do mkvmerge commmands

    # Remember key is three digits with padded zeros. Check and see if three is really needed or just two
    pad_with_three = pad_three(split_dict)

    print("For anime, auto-assign signs&songs and dialogue (looking at size)? (y/n)")
    check_signs_songs = input() == "y"

    # Vars for storing all notices and mkvmerge_strings between loop iterations
    all_notices = []
    all_mkvmerge_string = []

    for key, value in split_dict.items():
        ''' Loop that goes through all items for each unique playlist/episode and creates a muxing command in mkvmerge_string (local loop var),
            then appends this string to all_mkvmerge_string at the end of the loop iteration. '''

        if not pad_with_three:
            # pad with two instead of three. Yes, I know this is dumb, why even pad with three before?
            # cuz didn't write it to only pad with two before UNLESS it needed three in demux, always three instead
            ep_key = (key.lstrip("0")).rjust(2, "0")
        else:
            ep_key = key

        sub_files = [item for item in value if item.startswith("sub")]

        # Separate sub files based on language
        _, sub_files_lang_dict = create_dict_by_country(sub_files)
        # Check for signs and songs. If we are checking for that, the order of the items in each dict key may change.
        sub_files_lang_dict = compute_signs_and_songs(check_signs_songs, sub_files_lang_dict, dest)

        '''
        TODO: Always making English default right now. Ask for this
        TODO: Figure out a way to ask for track titles? Not sure of a good way to do this and still batch unless I checked for pattern
        TODO: I am assuming h264. This is pretty much OK but wouldn't be OK for 4k, and I don't personally
              care enough to add in 4k batching ability at the moment
        '''

        # Get video resolution - 1080p, 480p etc. used in the filename path.
        vid_resolution_pattern = re.compile(".*_([0-9]+(i|p))")
        vid_resolution = vid_resolution_pattern.match(
            ''.join([item for item in value if item.startswith("vid")])).group(1)

        mkvmerge_string = "mkvmerge -o "

        # Create file name path in mkvmerge_out_path
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

        # Append the file name path to mkvmerge_string
        mkvmerge_string += os.path.join(dest, mkvmerge_out_path)

        # Add chapters to mkvmerge_string
        mkvmerge_string += " --chapters {}".format(
            os.path.join(dest, ''.join([item for item in value if item.startswith("chapters")])))
        # Add video to mkvmerge_string
        mkvmerge_string += " {0} {1}".format(comp_str, os.path.join(dest, ''.join(
            [item for item in value if item.startswith("vid")])))

        # Add audio to mkvmerge_string
        # First create dict by languages
        aud_files = [item for item in value if item.startswith("aud")]
        notice, aud_files_lang_dict = create_dict_by_country(aud_files)

        # Append notice to all_notices (means there are multiple audio files of same language)
        if notice:
            all_notices.append([ep_key, notice])

        # Do audio and subtitle dict work in mkvmerge_string_dicts()
        mkvmerge_string = mkvmerge_string_dicts(sub_files_lang_dict, aud_files_lang_dict, check_signs_songs,
                                                mkvmerge_string, comp_str, dest)

        # Print the muxing string so the user can make sure it looks OK
        print(mkvmerge_string)

        ''' Append mkvmerge_string to the all_mkvmerge_string array at the end of the loop so that I can
            iterate over the array (executing the commands) once the user confirms they want to mux '''
        all_mkvmerge_string.append(mkvmerge_string)

    # Outside of for-loop

    # If found nothing to mux, exit the program
    if not all_mkvmerge_string:
        print("Error: Found nothing to mux. Dest: {}".format(dest))
        sys.exit(1)

    # Print notices
    for n in all_notices:
        print("For episode {0}, found multiple audio files for lang {1}".format(n[0], n[1]))

    print("Continue to muxing? (y/n)")

    # Run actual muxing command
    if input() == "y":
        for m_str in all_mkvmerge_string:
            run_shell(m_str)
    print("Done muxing")
