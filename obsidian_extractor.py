# obsidian notes extractor
# script to extract notes with a particular tag from an obsidian vault, copying with those notes the supporting documents (linked notes or linked media). The notes that have the tag will be moved (deleted from the original vault), the linked notes and media will be copied over.

import os
from pathlib import Path
from pprint import pprint
from shutil import copy2, move
import subprocess
import re
import frontmatter  #pip install python-frontmatter

old_vault = input("Drop vault directory on the command prompt window: ")
# old_vault = r"C:\Users\YourName\Documents\ObsidianVault"
media_folder = input("Name of the media folder in your vault: ")
new_vault = input("Drop the directory to extract to on the command prompt window: ")
# new_vault = r"C:\Users\YourName\Test\ExtractTo"

md_files = {}
media_files = {}
files_to_move = {}
files_to_copy = {}
linked_media = {}

# Get a list of paths to every md file in the vault
for root, dir_names, file_names in os.walk(old_vault):
	if file_names:
		for file in file_names:
			base, ext = os.path.splitext(file)
			if ext in (".md", ".MD"):
				md_files[base] = os.path.join(root, file)
for root, dir_names, file_names in os.walk(os.path.join(old_vault, "Media")):
	for file in file_names:
		media_files[file] = os.path.join(os.path.join(old_vault, "Media"), file)
				

# find all notes that have a tag
tag_list = input("Comma separated list of tags to extract: ")
tag_list = tag_list.replace(", ", ",").split(',')
# tag_list = ["work", "project1"]
tags_pattern = r"\B#" + r"\b|\B#".join(tag_list) + r'\b' # The regex to match a single tag is \B#tag\b . This creates a string that joins all these regex with a '|' which is the 'OR' operator between regex patterns.



# Check in each file if it has the tags I want to move (either in the frontmatter or in the text)
for base_name, file_path in md_files.items():
	move_file = False
	# find tags in frontmatter
	with open(file_path, encoding="utf-8-sig") as f:
		try:
			metadata = frontmatter.load(f)
		except:
			print(f"Could not parse frontmatter for {file_path}, unsupported character. From experience it's often single or double quotes in the frontmatter")
	tags = metadata.get('tags') or ''
	if isinstance(tags, str):
		tags = tags.split(', ')
	
	for tag in tags:
		if tag in tag_list:
			move_file = True
	
	# find tags in the text
	if not move_file: 
		with open(file_path, encoding='utf-8') as f:
			match = re.findall(tags_pattern, f.read())
			if match:
				move_file = True
	if move_file:
		files_to_move[base_name] = file_path
			
# Check for each file that must be moved which files it links to, those will need to be copied
for base_name, file_path in files_to_move.items():
	with open(file_path, encoding='utf-8') as f:
	# Note check that this regex doesn't find media as well as links.
		matches = re.findall(r"(?<=\[{2})(.*?)(?=\]{2})", f.read())
		if matches:
			for match in matches:
				m = match.split('|')[0]
				if m in files_to_move:
					print(f"Linked file {m} already in files_to_move, won't add to files_to_copy")
					continue
				try:
					files_to_copy[m] = md_files[m]
				except KeyError:
					# Linked file not found in the list of all notes, probably a link to a note that hasn't been created yet. A dangling link.
					print(f"Found a link to note {m} but couldn't find note {m}. Assuming dangling link, check manually to be certain")
				
				

# Check for media. Media will be copied because it might be linked by other notes in the old vault. So we rather copy and then we will clean the old vault of media that is not linked to by any note using a plugin that does that.
media_pattern = r"(?<=!\[{2})(.*?)(?=\]{2})"
for base_name, file_path in files_to_move.items():
	with open(file_path, encoding='utf-8') as f:
		matches = re.findall(media_pattern, f.read())
		if matches:
			for match in matches:
				m = match.split('|')[0]
				if m in linked_media:
					print(f"Media {m} already in media to copy, skipping")
				try:
					linked_media[m] = media_files[m]
				except KeyError:
					print(f"Media {m} not found but linked to. Check manually")
for base_name, file_path in files_to_copy.items():
	with open(file_path, encoding='utf-8') as f:
		matches = re.findall(media_pattern, f.read())
		if matches:
			for match in matches:
				m = match.split('|')[0]
				if m in linked_media:
					print(f"Media {m} already in media to copy, skipping")
				try:
					linked_media[m] = media_files[m]
				except KeyError:
					print(f"Media {m} not found but linked to. Check manually")
				

				
print("\n=== Files to move ===")
for key, value in files_to_move.items():
	print(key, ': ', value)
print("\n=== Files to copy ===")
for key, value in files_to_copy.items():
	print(key, ': ', value)
print("\n=== Linked media ===")
for key, value in linked_media.items():
	print(key, ': ', value)

confirm_extract = input("Review the lists above and the errors before that. Continue extraction? (y/N)").lower() or 'n'

if confirm_extract == 'y':
	if not os.path.isdir(new_vault):
		print("New vault location did not exist, creating it...")
		Path(new_vault).mkdir(parents=True, exist_ok=True)

	for key, value in files_to_copy.items():
		relative_path = Path(value).relative_to(old_vault)
		destination = os.path.join(new_vault, relative_path)
		Path(os.path.dirname(destination)).mkdir(parents=True, exist_ok=True)
		copy2(value, destination)

	for key, value in linked_media.items():
		relative_path = Path(value).relative_to(old_vault)
		destination = os.path.join(new_vault, relative_path)
		Path(os.path.dirname(destination)).mkdir(parents=True, exist_ok=True)
		copy2(value, destination)

	for key, value in files_to_move.items():
		relative_path = Path(value).relative_to(old_vault)
		destination = os.path.join(new_vault, relative_path)
		Path(os.path.dirname(destination)).mkdir(parents=True, exist_ok=True)
		move(value, destination)

print("Finished.")
subprocess.Popen(rf'explorer "{new_vault}"') 