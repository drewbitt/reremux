#!/usr/bin/python3
import subprocess
import os
import sys
import re
from collections import defaultdict


def mux(short_name, dest):
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
            key = (key.lstrip("0")).rjust(2, "0")

        sub_files = [item for item in value if item.startswith("sub")]

        # separate sub files based on language
        sub_files_lang_dict = defaultdict(list)

        for sub in sub_files:
            pattern = re.compile(".*([a-z]{2})\.")
            sub_country = pattern.match(sub).group(1)
            sub_files_lang_dict[sub_country].append(sub)

        print("Sub files lang dict: {}".format(sub_files_lang_dict))

        # track 5 smaller one
        if check_signs_songs:
            for key, value in sub_files_lang_dict:
                print(value)
                if len(value) >= 2:
                    filepaths = []
                    for subf in value:
                        filepaths.append(subf, os.path.getsize(subf))
                    # smallest in the front
                    filepaths.sort(key=lambda filename: filename[1], reverse=False)
                    value = filepaths
            print("After adjusting for signs and songs {}".format(sub_files_lang_dict))

        # TODO: Always making English default right now. Ask for this
        # TODO: Also I guess ask for subtitle titles if not signs and songs
        mkvmerge_string = ""
