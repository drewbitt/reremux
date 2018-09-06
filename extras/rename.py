#!/usr/bin/python3
from argparse import ArgumentParser
import os
import re
import sys
from shutil import move


def rename(dest, file = False, dic=False):
    # Rename files matching a regex as specified in either a file converted to a dict or a passed dict

    '''
    # file format is
    # 01 -> 10
    # 10 -> 01
    # etc, one renaming on each line split by ->
    '''

    # Definitions/Helper methods
    dest = os.path.normpath(args.dest)

    def calc_rename(str1, new_ep_num):
        # Calculate new string to rename file as
        return re.sub(r"(.* -)( [0-9]+ )(\[.*)", r"\1 {} \3".format(new_ep_num), str1)

    def find_file(episode_num, z1=False):
        # Find file with passed episode number in dest directory
        matching_regex = re.compile(r".*- {} \[.*\.mkv$".format(episode_num))
        matching_regex_z1 = re.compile(r".*- {} \[.*\.mkvz1$".format(episode_num))
        if z1 and [matching_regex_z1.match(i) for i in os.listdir(dest) if matching_regex_z1.match(i)]:
            # found a z1 for the episode number
            matching_regex = matching_regex_z1

        return "".join([matching_regex.match(i).group(0) for i in os.listdir(dest) if matching_regex.match(i)])

    def to_d(vr):
        # add dest to path
        return os.path.join(dest, vr)

    # Loops
    if not dic:
        with open(to_d(file)) as list_file:
            episode_map = {}

            # iterate over list file and add to episode_map
            for line in list_file:
                line = line.replace(" ", "").rstrip()
                if line != "":
                    orig_ep_num, new_ep_num = line.split("->")
                    episode_map[orig_ep_num] = new_ep_num
    else:
        # expects dict like {"04": "03", "03": "04"}
        episode_map = dic

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
            first_found_file = find_file(key, z1=True)

            if not rename_found_file:
                print("Did not find an episode for {}".format(episode_map[key]))
                sys.exit(1)
            if not first_found_file:
                print("Did not find en episode for {}".format(key))
                sys.exit(1)

            print("Renaming {0} to {1}".format(rename_found_file, rename_found_file + "z1"))
            move(to_d(rename_found_file), to_d(rename_found_file + "z1"))
            print("Moving {0} to {1}".format(first_found_file, rename_found_file))
            move(to_d(first_found_file), to_d(rename_found_file))
        else:
            # Easier rename - the one I'm renaming to doesn't exist already
            # prioritize if it ends in "z1"
            found_file = find_file(key, z1=True)
            # compute new name
            new_name = calc_rename(found_file, episode_map[key]).rstrip("z1")
            print("Moving {0} to {1}".format(found_file, new_name))
            move(to_d(found_file), to_d(new_name))


if __name__ == "__main__":
    parser = ArgumentParser("Change episode numbers of already muxed files")

    parser.add_argument('dest', metavar="dest", type=str, help="Folder to look for files to rename")
    parser.add_argument("--file", dest="file", help="File location for file that specifies how to rename")
    args = parser.parse_args()

    if not args.file:
        print("Please specify a file (--file) to read the renaming layout from")
        sys.exit(1)

    rename(args.dest, file=args.file)
