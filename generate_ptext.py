#!/usr/bin/env python3
import os
from random import randint

students_dir = "static/dataset-medium";
lines = []

with open('levit.txt', 'r') as f:
	for line in f:
		lines.append(line)
for student in [x for x in os.listdir(students_dir) if not x.startswith('.')]:
	# if 'profile_text.txt' not in os.listdir(os.path.join(students_dir, student)):
	# 	with open(os.path.join(students_dir, student, 'profile_text.txt'), 'w') as f:
	# 		f.write(lines[randint(0, len(lines)-1)])
	with open(os.path.join(students_dir, student, 'profile_text.txt'), 'w') as f:
		f.write(lines[randint(0, len(lines)-1)].rstrip())