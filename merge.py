#!/usr/bin/python3
import subprocess
import os
import sys
import re
from collections import defaultdict


def mux(short_name, series_name, dest):
    """Mux a specified short names files in destination directory using mkvmerge"""

    # Test mkvmerge
    try:
        # didn't know about python 3s use of run over call
        # also can't get it to work normally so going to concat into one string
        with open(os.devnull, "w") as f:
            proc = subprocess.run(["mkvmerge", "-V"], check=True, stdout=f)
    except subprocess.CalledProcessError as ex:
        print(ex)
        print("Mkvmerge error - may not have it installed")
        sys.exit(1)

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

    # Dict for each episode is created. Loop through and do mkvmerge commmands

    # Remember key is three digits with padded zeros. Check and see if three is really needed or just two
    pad_with_three = False
    for key in split_dict:
        if int(key.lstrip("0")) > 99:
            pad_with_three = True
            break

    # TODO: No idea how this implementation will work for more than 2 sub tracks in a language, like if there's
    # an additional commentary sub track. Right now it will sort them by size fine, but won't be able to name
    # them correctly since I don't know which is dialogue/commentary/whatever

    # Actually this a huge fucking oversight - I'm never planning on specifying subtitle track names

    print("For anime, auto-assign signs&songs and dialogue? (y/n)")
    check_signs_songs = input() == "y"

    for key, value in split_dict.items():
        if not pad_with_three:
            # pad with two instead of three. Yes, I know this is dumb, why even pad with three before?
            # cuz didn't write it to only pad with two before UNLESS it needed three in demux, always three instead
            ep_key = (key.lstrip("0")).rjust(2, "0")
        else:
            ep_key = key

        sub_files = [item for item in value if item.startswith("sub")]

        # separate sub files based on language
        sub_files_lang_dict = defaultdict(list)

        for sub in sub_files:
            pattern = re.compile(".*([a-z]{2})\.")
            sub_country = pattern.match(sub).group(1)
            sub_files_lang_dict[sub_country].append(sub)

        for key1, value1 in sub_files_lang_dict.items():
            # If checking for signs and songs, check if language has 2 or more sub tracks and then add smallest in front
            if check_signs_songs:
                if len(value1) >= 2:
                    filepaths = []
                    for subf in value1:
                        # append size to a new list to sort by size
                        filepaths.append([subf, os.path.getsize(subf)])
                    # smallest in the front
                    filepaths.sort(key=lambda filename: filename[1], reverse=False)
                    filepaths = [item[0] for item in filepaths]
                    sub_files_lang_dict[key1] = filepaths
            else:
                # Still want the track ids to be in the right order
                sub_files_lang_dict[key] = sorted(value)

        # TODO: Always making English default right now. Ask for this
        # TODO: Also I guess ask for subtitle titles if not signs and songs
        # TODO: I am assuming h264. This is pretty much OK but wouldn't be OK for 4k, and I don't personally
        #       care enough to add in 4k batching ability at the moment

        vid_resolution_pattern = re.compile(".*_([0-9]+(i|p))")
        vid_resolution = vid_resolution_pattern.match(''.join([item for item in value if item.startswith("vid")])).group(1)

        # aud_channels_pattern = re.compile(".*([0-9]+\.[0-9])")
        # aud_channels = aud_channels_pattern.match(''.join([item for item in value if item.startswith("aud")])).group(1)

        # If you want custom formatting you have to adjust this yourself. Screw actual usability!

        mkvmerge_string = "mkvmerge -o \"{0} - {1} [Blu-ray {2} h264 ".format(series_name, ep_key, vid_resolution)
        if any(".truehd" in s for s in value):
            mkvmerge_string += "TrueHD"
        elif any(".flac" in s for s in value):
            mkvmerge_string += "FLAC"
        elif any(".dts" in s for s in value):
            mkvmerge_string += "DTS-HDMA"
        if any(".pcm" in s for s in value):
            mkvmerge_string += "PCM"
        comp_str = "--compression 0:none"
        # Add chapters
        mkvmerge_string += " REMUX].mkv\" --chapters {}".format(''.join([item for item in value if item.startswith("chapters")]))
        # Add video
        mkvmerge_string += " {0} {1}".format(comp_str, ''.join([item for item in value if item.startswith("vid")]))

        # Add audio

        # Add subs
        for key1, value1 in sub_files_lang_dict.items():
            for val in value1:
                mkvmerge_string += " {0} --language 0:{1} ".format(comp_str, key1)
                # Add sub titles (right now, only if signs/songs is set)

        print(mkvmerge_string)
