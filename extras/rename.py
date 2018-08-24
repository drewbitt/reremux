#!/usr/bin/python3
from argparse import ArgumentParser
import os
import re
import sys
from shutil import move

parser = ArgumentParser("Change episode numbers of already muxed files")

parser.add_argument('dest', metavar="dest", type=str, help="Folder to look for files to rename")
parser.add_argument("--file", dest="file", help="File location for file that specifies how to rename")
args = parser.parse_args()
# file format is
# 01 -> 10
# 10 -> 01
# etc, one renaming on each line split by ->

# Definitions

dest = os.path.normpath(args.dest)
# pattern to get episode number
pattern_ep_number = re.compile(r".* - ([0-9]+) \[.*")

def calc_rename(str1, new_ep_num):
    return re.sub(r"(.* -)( [0-9]+ )(\[.*)", r"\1 {} \3".format(new_ep_num), str1)

def find_file(episode_num, z1=False):
    if z1:
        matching_regex = re.compile(r".*- {} \[.*".format(episode_num))
        if len([matching_regex.match(i) for i in os.listdir(dest) if matching_regex.match(i)]) > 1:
            # found a z1 for the episode number
            matching_regex = re.compile(r".*- {} \[.*z1$".format(episode_num))
    else:
        matching_regex = re.compile(r".*- {} \[.*".format(episode_num))

    return "".join([matching_regex.match(i).group(0) for i in os.listdir(dest) if matching_regex.match(i)])

# Loops
with open(args.file) as list_file:
    episode_map = {}

    # iterate over list file and add to episode_map
    for line in list_file:
        line = line.replace(" ", "").rstrip()
        if line != "":
            orig_ep_num, new_ep_num = line.split("->")
            episode_map[orig_ep_num] = new_ep_num

    for count, key in enumerate(episode_map):
        # search only things I haven't processed yet
        # either do this or edit episode_map on the fly to delete seen elements
        if episode_map[key] in dict(list(episode_map.items())[count:]):
            # Not an easy rename - found another file that was specified to exist already
            # in the list file

            # rename episode of episode_map[key] to have "z1" at the end
            # first, have to find it
            rename_found_file = find_file(episode_map[key])
            # filename of episode I need to rename
            first_found_file = find_file(key)

            if not rename_found_file:
                print("Did not find an episode for {}".format(episode_map[key]))
                sys.exit(1)
            if not first_found_file:
                print("Did not find en episode for {}".format(key))
                sys.exit(1)

            print("Renaming {0} to {1}".format(rename_found_file, rename_found_file + "z1"))
            print("Moving {0} to {1}".format(first_found_file, rename_found_file))
        else:
            # Easier rename - the one I'm renaming to doesn't exist already
            # prioritize if it ends in "z1"
            found_file = find_file(key, z1=True)
            # compute new name
            new_name = calc_rename(found_file, episode_map[key]).rstrip("z1")
            print("Moving {0} to {1}".format(found_file, new_name))
