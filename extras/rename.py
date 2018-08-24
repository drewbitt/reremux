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

dest = os.path.normpath(args.dest)

pattern = re.compile(r".* - ([0-9]+) \[.*")

all_files = os.listdir(dest)

with open(args.file) as list_file:
    episode_map = {}
    for line in list_file:
        line = line.replace(" ", "").rstrip()
        if line != "":
            orig_ep_num, new_ep_num = line.split("->")
            episode_map[orig_ep_num] = new_ep_num

    for num, file1 in enumerate(all_files):
        file_ep_num_re = pattern.match(file1)

        if file_ep_num_re is not None:
            file_ep_num = file_ep_num_re.group(1)
            print(file_ep_num)
            if file_ep_num in episode_map:
                # rename file_ep_num to episode_map[file_ep_num]

                def calc_rename(str1, new_ep_num):
                    return re.sub(r"(.* -)( [0-9]+ )(\[.*)", r"\1 {} \3".format(new_ep_num), str1)

                # check and see if it can be a ez rename
                if not file_ep_num in episode_map:
                    new_name = calc_rename(file1, new_ep_num).rstrip("z1")
                    print("Moving {0} to {1}".format(file1, new_name))
                    # move(file1, new_name)
                else:
                    # Means there's en existing file with this episode number
                    # Find it in the directory
                    matching_regex = re.compile(r".*- {} \[.*(?<!z1)$".format(episode_map[file_ep_num]))
                    matching_file_move_to = "".join([matching_regex.match(i).group(0) for i in os.listdir(dest) if matching_regex.match(i)])

                    print(episode_map)
                    print(episode_map[file_ep_num])


                    if matching_file_move_to:
                        print("Renaming {0} to {1}".format(matching_file_move_to, matching_file_move_to + "z1"))
                        move(os.path.join(dest, matching_file_move_to), os.path.join(dest, matching_file_move_to + "z1"))

                        new_name = calc_rename(matching_file_move_to, episode_map[file_ep_num])

                        print("Moving {0} to {1}".format(file1, new_name))
                        move(os.path.join(dest, file1), os.path.join(dest, new_name))
                    else:
                        print("Error")
                        sys.exit(1)

                # remove from episode map now that processed it
                del episode_map[file_ep_num]