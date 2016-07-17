#!/usr/bin/python
# -*- coding: utf-8 -*-
 
from github import Github
from PIL import Image
import ssl
import urllib2

repository_name = "drummyfish/bombman"
filename = "bombman.py"

USERNAME = ""  # add your github username and password here to get bigger API request limit!
PASSWORD = ""

LINE_ADDED = 0
LINE_DELETED = 1
LOAD_ANEW = 2       # download the file from raw url if there was merge
IMAGE_RESOLUTION = (1366,768)
COLUMN_WIDTH = 175

MAX_COMMITS = 1000
 
# return list of changes in format: (line number, added/deleted, line text, is last change in commit, commit_number)
 
def patch_to_changes(patch_string, commit_number):
  result = []
 
  lines = patch_string.split("\n")
 
  current_line_old = 0
  current_line_new = 0
 
  for i in range(len(lines)):
    line = lines[i]
 
    if len(line) > 0:
      if line[0] == "@":
        pos1 = 4
        pos2 = line.find(",")
        current_line_old = int(line[pos1:pos2])
        pos1 = line.find("+") + 1
        pos2 = line.find(",",pos1)
        current_line_new = int(line[pos1:pos2])
      elif line[0] == "+":
        result.append([current_line_new,LINE_ADDED,line[1:],False,commit_number])
        current_line_new += 1
      elif line[0] == "-":
        current_line_old += 1
        result.append([current_line_new,LINE_DELETED,line[1:],False,commit_number])
      else:
        current_line_old += 1
        current_line_new += 1
 
  result[-1][3] = True   # mark last change
   
  return result
 
def save_file_lines_as_image(lines, filename, resolution, commit_number, total_commits):
  print("saving image " + filename)
  image = Image.new("RGB",resolution,"white")
 
  pixels = image.load() # create the pixel map
 
  for j in range(len(lines)):
    line = lines[j]
 
    for i in range(len(line)):
      if line[i] != " ":
        x = i + COLUMN_WIDTH * (j / (resolution[1] - 1))
        y = j % (resolution[1] - 1)
 
        try:
          pixels[x,y] = (0,0,0)
        except Exception:
          pass

  for i in range(total_commits): # progress bar
    color = (255,0,0) if i < commit_number else (100,100,100)
    pixels[i,resolution[1] - 1] = color        

  image.save(filename,"PNG")
 
def save_file_lines_as_file(lines, filename):
  print("saving file " + filename)
  output_file = open(filename,"w")
 
  for line in lines:
    output_file.write(line.encode("utf-8") + "\n")
 
  output_file.close()

github = Github(USERNAME,PASSWORD)
repository = github.get_repo(repository_name)
commits = list(repository .get_commits())
 
max_commits = MAX_COMMITS
commit_number = 0
try_again_counter = 0
 
change_list = []
 
was_merge = False
 
while commit_number < len(commits):
  try:
    print("loading commit " + str(commit_number + 1))
    commit = commits[-1 * (commit_number + 1)]
 
    print("message: " + commit.commit.message)
 
    if len(commit.parents) > 1:   # was merge => load the file from raw url next time
      was_merge = True
      print("Merge commit")
 
    files = commit.files
 
    commit_number += 1
 
    for one_file in files:
      if one_file.filename == filename:
        if was_merge:
          was_merge = False
          change_list += [(0,LOAD_ANEW,one_file.raw_url,True,commit_number)]
        else:
          patch = one_file.patch
          change_list += patch_to_changes(patch,commit_number)
        
        break
 
    max_commits -= 1
 
    if max_commits < 0:
      break
 
    try_again_counter = 5
  except ssl.SSLError:
    print("timeout, trying again...")
    try_again_counter -= 1
 
    if try_again_counter < 0:
      print("failed too many times, stopping")
      break
 
file_lines = []  # start with file with one empty line
 
change_number = 0

for change in change_list:
  try:
    if change[1] == LINE_ADDED:
      file_lines.insert(change[0] - 1,change[2])
    elif change[1] == LINE_DELETED:
      del file_lines[change[0] - 1]
    elif change[1] == LOAD_ANEW:
      print("reloading the file after commit")
      data = urllib2.urlopen(change[2])
      file_lines = data.read().decode("utf-8").split("\n")
 
  except Exception as e:
    print(e)
    print("some error happened, but going on...")
 
  print(str(int((change_number + 1) / float(len(change_list)) * 100)) + "%")
 
  if change[3]:  # last change in commit
    print("commit done")
 
  save_file_lines_as_image(file_lines,"images/out" + str(change_number).zfill(5) + ".png",IMAGE_RESOLUTION,change[4],len(commits))
  change_number += 1

save_file_lines_as_file(file_lines,"final file for check.txt")
