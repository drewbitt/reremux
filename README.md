# reremux

Remux script meant to run on Linux, so eac3to in wine and mkvmerge. 
Demuxes with eac3to to filenames that contains all information needed to later mux together.

Very specific to my use-case, so there's going to be some issues/to-dos, namely:
* Can't name subtitle tracks
* Can't name any track actually, I never prompt for it
* If eac3to can even do 4K, it still will name the files with h264 since I didn't put h264/h265 in the filename to mux with
* Has English audio always as default
* Has very limited testing so surely things will be broken
* ``--mux-only` actually still requires a source AND it to be like `source dest --mux-only`.
* Error catching or notifying is bad. I can't help this easily since eac3to usually returns non-zero return codes for errors but does not in wine. An alternative is to parse for known error strings.
