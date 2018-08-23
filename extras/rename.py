#!/usr/bin/python3
from argparse import ArgumentParser
import os
import re
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
            print("\n" + file1 + "\n")
            file_ep_num = file_ep_num_re.group(1)
            if file_ep_num in episode_map:
                # this is the file I need to rename

                def calc_rename(str1, new_ep_num):
                    return re.sub(r"(.* - )([0-9]+)( \[.*)", r"\1 {} \3".format(new_ep_num), str1)

                # check and see if it can be a ez rename
                if not new_ep_num in episode_map:
                    print("ez rename")
                    new_name = calc_rename(file1, new_ep_num)
                    print("Moving {0} to {1}".format(file1, new_name))
                    # move(file1, new_name)
                else:
                    print("not ez rename")
                    # rename the file to be this now
                    new_file1 = file1 + "z1"

                    #move(file1, new_file1)
                    print("Renaming {0} to {1}".format(file1, new_file1))

                    new_name = calc_rename(new_file1, new_ep_num)

                    print("Moving {0} to {1}".format(new_file1, new_name))
