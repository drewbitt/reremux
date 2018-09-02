#!/usr/bin/python3
from argparse import ArgumentParser
from whatanime import search
import screenshot

api_token = ""

def search_file(vid, api_t):
	save_path, frame = screenshot.screenshot(vid, "")
	r_js = search(api_t, os.path.join(save_path, frame + "jpeg"))
	print(r_js)
	screenshot.delete_all(save_path)

if __name__ == "__main__":
	parser = ArgumentParser("Screenshot and search with whatanime")
	parser.add_argument("vid", metavar="vid", type=str, help="Video file")
	args = parser.parse_args()

	search_file(args.vid, api_token)
