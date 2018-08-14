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
