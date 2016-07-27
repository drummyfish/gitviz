# gitviz

This is a simple script in Python that allows you to make an animation of a single text file in GitHub repository based on previous commits. To use just fill in the required info on the top of the script file and run it with python.

Requirements: Python, PIL, [PyGithub](https://github.com/PyGithub/PyGithub).

The script outputs a series of PNGs, which can be merged into a video for example with ffmpeg:

     ffmpeg -framerate 60 -i images/out%05d.png -c:v libx264 -r 30 -pix_fmt yuv420p out.mp4

You can also make gif out of the video:

     ffmpeg -i out.mp4 -vf "palettegen" -y palette.png
     ffmpeg -i out.mp4 -i palette.png -lavfi "paletteuse" -y out.gif

I wrote the script quickly and didn't test it very much, use at your own risk. Visualization of files that are being worked at in different branches a lot will probably not be very nice - the script simply takes all commits in sequential order, not taking branches into account, and executes them - once a merge commit is encountered, the file is loaded from GitHub as a whole and used from that commit on.

C++ gif example of [utf.hpp](https://github.com/jalfd/utf.hpp):

![gif](http://i.giphy.com/l41Ya4SKT4KQHHyBG.gif)

Python video example of [Bombman](https://github.com/drummyfish/bombman) (older version):

[![video](https://img.youtube.com/vi/eb6huI4Bm3Q/0.jpg)](https://www.youtube.com/watch?v=eb6huI4Bm3Q)]

