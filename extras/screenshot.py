# Screenshot a mkv just one frame at a time. Full featured @ https://github.com/drewbitt/vs-screen/blob/master/vs-screen.py
# I am using this right now for 1) accuracy and 2) good jpeg support. However, indexing times for remuxes sucks. May adjust to mpv if it works just for the speed.

import vapoursynth as vs
import random
import os
import re
import shutil

core = vs.core

def open_clip(path: str) -> vs.VideoNode:
    """Load clip into vapoursynth"""
    print("Indexing... may take a while")
    clip = core.ffms2.Source(path)
    clip = clip.resize.Spline36(format=vs.RGB24, matrix_in_s='709' if clip.height > 576 else '470bg')
    return clip

def get_frame_number(clip):
    length = len(open_clip(clip))
    return random.randint(int(length/4), int(length/4)*3)

def delete_all(save_path):
    """ Delete all files (and the save_path folder) in save_path"""
    try:
        shutil.rmtree(save_path)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    else:
        print("Removed {}".format(save_path))

def screenshot(file, dest):
    """Screenshot to file in a new folder in dest. Returns the save path"""

    frame = get_frame_number(file)
    print('Requesting frame:', frame)

    if hasattr(core, 'imwri'):
        imwri = core.imwri
    elif hasattr(core, 'imwrif'):
        imwri = core.imwrif
    else:
        raise AttributeError('Either imwri or imwrif must be installed.')

    name = re.split(r'[\\/]', file)[-1].rsplit('.', 1)[0]
    save_path = os.path.join(dest, name)
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    clip = open_clip(file)
    clip = imwri.Write(clip, 'jpeg', os.path.join(save_path, '%d.jpeg'), quality=90)
    print('Writing {:s}/{:d}.jpeg'.format(save_path, frame))
    clip.get_frame(frame)

    print(clip)
    return save_path, frame
