#!/usr/bin/env python3
# !/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re
from flask import Flask, render_template, session

students_dir = "dataset-medium";

app = Flask(__name__)
app.secret_key = os.urandom(12)

# Show unformatted details for student "n"
# Increment n and store it in the session cookie

fields = ['birthday',
          'courses',
          'email',
          'friends',
          'full_name',
          'home_latitude',
          'home_longitude',
          'home_suburb',
          'password',
          'program',
          'zid']

@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
def start():
    n = session.get('n', 0)
    print(n)
    students = sorted(os.listdir(students_dir))
    students = [x for x in students if not x.startswith('.')]
    student_to_show = students[n % len(students)]
    details = {}
    details_filename = os.path.join(students_dir, student_to_show, "student.txt")
    if os.path.exists(os.path.join(students_dir, student_to_show, "img.jpg")):
        details['picture'] = os.path.join(students_dir, student_to_show, "img.jpg") 
    else: details['picture'] = os.path.join("egg.gif")
    with open(details_filename) as f:
        for line in f:
            line = line.rstrip()
            for field in fields:
                if line.startswith(field):
                    details[field] = line[len(field)+2:] 
                    break

    session['n'] = n + 1
    return render_template('start.html', **details) 

if __name__ == '__main__':
    # app.secret_key = os.urandom(12)
    app.run(debug=True)
