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
all_files_ep_only = list(filter(pattern.match, all_files))

with open(args.file) as list_file:

    for line in list_file:
        line.replace(" ", "")
        if line != "":
            orig_ep_num, new_ep_num = line.split("->")

            for num, file in enumerate(all_files):
                file_ep_num_re = pattern.match(file)

                if file_ep_num_re is not None:
                    file_ep_num = file_ep_num_re.group(1)
                    if file_ep_num == orig_ep_num:
                        # this is the file I need to rename
                        # check and see if it can be a ez rename
                        if not any(orig_ep_num in s for s in all_files_ep_only):
                            print("ez rename")
                            new_name = re.sub(file, r"g<1>", new_ep_num)
                            # would move the file here instead of printing
                            print(new_name)

                            # adjust lists for future iterations
                            all_files[num] = new_name
                            all_files_ep_only.remove(orig_ep_num)
                            all_files_ep_only.append(new_ep_num)
                        else:
                            print("not ez rename")

