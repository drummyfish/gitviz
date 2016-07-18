#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is a simple script in Python that allows you to make an animation of
# a single text file in GitHub repository based on previous commits.
#
# copyright Miloslav Číž, 2016
#
# This software is provided under WTFPL license: http://www.wtfpl.net/.

from github import Github
from PIL import Image
import ssl
import urllib2
import re

#======================================================================

# Fill in these constants:

REPOSITORY_NAME = "drummyfish/bombman"
FILE_NAME = "bombman.py"
USERNAME = ""  # add your github username and password here to get bigger API request limit!
PASSWORD = ""
LANGUAGE = "python"   # for very simple syntax highlight, possible values: "none", "python", "c++"
IMAGE_RESOLUTION = (1366,768)
COLUMN_WIDTH = 200
MAX_COMMITS = 1000

NORMAL_COLOR = (0,0,0)
KEYWORD_COLOR = (200,0,0)
COMMENT_COLOR = (97,85,201)

#======================================================================

PYTHON_KEYWORDS = ["and","as","assert","break","class","continue","def","del","elif","else","except","exec","finally",
  "for","from","global","if","import","in","is","lambda","not","or","pass","print","raise","return","try","while",
  "with","yield","True","False","None"]
CPP_KEYWORDS = ["and","asm","auto","bitand","bitor","bool","break","case","catch","char","class","compl","const",
  "const_cast","continue","default","delete","do","double","dynamic_cast","else","enum","explicit","export","extern",
  "false","float","for","friend","goto","if","inline","int","long","mutable","namespace","new","not","not_eq","operator",
  "or","or_eq","private","protected","public","register","return","short","signed","sizeof","static","static_cast","struct",
  "switch","template","this","throw","true","try","typedef","typeid","typename","union","unsigned","using","virtual",
  "void","volatile","while","xor","xor_eq"]

CHARACTER_BRIGHTNESS_VALUES = {
  "a" : 0.31,
  "b" : 0.27,
  "c" : 0.4,
  "d" : 0.27,
  "e" : 0.25,
  "f" : 0.43,
  "g" : 0.31,
  "h" : 0.29,
  "i" : 0.59,
  "j" : 0.43,
  "k" : 0.31,
  "l" : 0.47,
  "m" : 0.25,
  "n" : 0.27,
  "o" : 0.27,
  "p" : 0.25,
  "q" : 0.25,
  "r" : 0.41,
  "s" : 0.35,
  "t" : 0.4,
  "u" : 0.41,
  "v" : 0.41,
  "w" : 0.27,
  "x" : 0.25,
  "y" : 0.26,
  "z" : 0.31,

  "A" : 0.01,
  "B" : 0.0,
  "C" : 0.31,
  "D" : 0.01,
  "E" : 0.0,
  "F" : 0.01,
  "G" : 0.02,
  "H" : 0.0,
  "I" : 0.04,
  "J" : 0.02,
  "K" : 0.01,
  "L" : 0.02,
  "M" : 0.0,
  "N" : 0.01,
  "O" : 0.01,
  "P" : 0.01,
  "Q" : 0.01,
  "R" : 0.01,
  "S" : 0.02,
  "T" : 0.02,
  "U" : 0.02,
  "V" : 0.02,
  "W" : 0.0,
  "X" : 0.0,
  "Y" : 0.02,
  "Z" : 0.02,

  "0" : 0.0,
  "1" : 0.08,
  "2" : 0.04,
  "3" : 0.04,
  "4" : 0.04,
  "5" : 0.04,
  "6" : 0.03,
  "7" : 0.04,
  "8" : 0.02,
  "9" : 0.02,

  " " : 1.0,
  "!" : 0.2,
  "?" : 0.14,
  "." : 0.97,
  "," : 0.96,
  ";" : 0.59,
  "-" : 0.78,
  "_" : 0.75,
  "\"" : 0.2,
  "'" : 0.8,
  "/" : 0.4,
  "\\" : 0.4,
  "=" : 0.12,
  ":" : 0.31,
  "*" : 0.2,
  "~" : 0.4,
  "^" : 0.31,
  "#" : 0.0,
}

LINE_ADDED = 0
LINE_DELETED = 1
LOAD_ANEW = 2                  # = download the file from raw url if there was merge
 
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

# Returns a list of color corresponding to each line character.
 
def highlight_line(line_string, language_string):
  result = []

  is_comment = False
  comment_start_position = -1

  for i in range(len(line_string)):
    character = line_string[i]

    if character == " ":
      color = (255,255,255)
    else:
      if character != " ":
        if language_string == "python":
          if character == "#":
            is_comment = True
        elif language_string == "c++":
          if character == "/" and i < len(line_string) - 1 and line_string[i + 1] == "/":
            is_comment = True
      
      if is_comment:
        if comment_start_position < 0:
          comment_start_position = i

        color = COMMENT_COLOR
      else:
        color = NORMAL_COLOR

    if character in CHARACTER_BRIGHTNESS_VALUES:
      character_brightness = CHARACTER_BRIGHTNESS_VALUES[character]
      addition = int(200 * character_brightness)
      color = (
        min(255,int(color[0] + addition)),
        min(255,int(color[1] + addition)),
        min(255,int(color[2] + addition)))

    result.append(color)

  # highlight keywords:

  if language_string != "none":
    keyword_list = PYTHON_KEYWORDS if language_string == "python" else CPP_KEYWORDS

    for keyword in keyword_list:
      for where in re.finditer("(^|[ ])(" + keyword + ")[$ ]",line_string):
        if comment_start_position < 0 or where.start(2) < comment_start_position:
          for i in range(where.start(2),where.end(2)):
            result[i] = KEYWORD_COLOR

  return result

def save_file_lines_as_image(lines, filename, resolution, commit_number, total_commits):
  print("saving image " + filename)
  image = Image.new("RGB",resolution,"white")
 
  pixels = image.load() # create the pixel map
 
  for j in range(len(lines)):
    line = lines[j]
    character_colors = highlight_line(line,LANGUAGE) 

    for i in range(len(line)):
      character = line[i]

      character_brightness = 0
      color = character_colors[i]

      x = i + COLUMN_WIDTH * (j / (resolution[1] - 1))
      y = j % (resolution[1] - 1)
 
      try:
        pixels[x,y] = color
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

#============================================
# main:

github = Github(USERNAME,PASSWORD)
repository = github.get_repo(REPOSITORY_NAME)
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
      if one_file.filename == FILE_NAME:
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
