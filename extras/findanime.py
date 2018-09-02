#!/usr/bin/python3
from argparse import ArgumentParser
import os
import base64
import json
from whatanime import search
import screenshot

api_token = ""

def search_file(vid, api_t):
    save_path, frame = screenshot.screenshot(vid, "")
    fl = os.path.join(save_path, str(frame) + ".jpeg")

    with open(fl, "rb") as img_f:
        encoded_str = base64.b64encode(img_f.read())

    r_js = search(api_t, encoded_str)
    print(json.dumps(r_js, indent=2))
    screenshot.delete_all(save_path)

if __name__ == "__main__":
    parser = ArgumentParser("Screenshot and search with whatanime")
    parser.add_argument("vid", metavar="vid", type=str, help="Video file")
    args = parser.parse_args()

    search_file(args.vid, api_token)

