# gitviz

This is a simple script in Python that allows you to make an animation of a single text file in GitHub repository based on previous commits.

Requirements: Python, PIL, [PyGithub](https://github.com/PyGithub/PyGithub).

The script outputs a series of PNGs, which can be merged into a video for example with ffmpeg:

     ffmpeg -framerate 60 -i images/out%05d.png -c:v libx264 -r 30 -pix_fmt yuv420p out.mp4

I wrote the script quickly and didn't test it very much, use at your own risk. Visualization of files that are being worked at in different branches a lot will probably not be very nice - the script simply takes all commits in sequential order, not taking branches into account, and executes them - once a merge commit is encountered, the file is loaded from GitHub as a whole and used from that commit on.

video example of [Bombman](https://github.com/drummyfish/bombman) (old version without syntax highlight):

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/6tryIhvMVj4/0.jpg)](https://www.youtube.com/watch?v=6tryIhvMVj4)]

Now the results look like this:
![](http://i.imgur.com/C6j9TUd.png)

