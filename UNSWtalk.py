#!/usr/bin/env python3
# !/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re
from flask import Flask, render_template, session, request, make_response

students_dir = "dataset-medium";

app = Flask(__name__)
app.secret_key = os.urandom(12)
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
# def start(zid = None):
#     n = session.get('n', 0)
#     students = sorted(os.listdir(students_dir))
#     students = [x for x in students if not x.startswith('.')]
#     student_to_show = students[n % len(students)]

#     user(student_to_show)

#     # details = {}
#     # details_filename = os.path.join(students_dir, student_to_show, "student.txt")
#     # if os.path.exists(os.path.join(students_dir, student_to_show, "img.jpg")):
#     #     details['picture'] = os.path.join(students_dir, student_to_show, "img.jpg") 
#     # else: details['picture'] = os.path.join("egg.gif")
#     # with open(details_filename) as f:
#     #     for line in f:
#     #         line = line.rstrip()
#     #         for field in fields:
#     #             if line.startswith(field):
#     #                 details[field] = line[len(field)+2:] 
#     #                 break
#     # details['friends'] = re.sub(r'[\(\)]','', details['friends'])
#     # details['friends'] = details['friends'].split(', ')
#     # session['n'] = n + 1
#     # return render_template('start.html', **details, students_dir=students_dir) 

@app.route('/user/<zid>', methods=['GET','POST'])
def user(zid=None):
    n = session.get('n', 0)
    if zid is None and request.cookies.get('user_id') is None:
        students = sorted(os.listdir(students_dir))
        students = [x for x in students if not x.startswith('.')]
        student_to_show = students[n % len(students)]
    elif request.cookies.get('user_id'):
        student_to_show = request.cookies.get('user_id') 
    else: 
        student_to_show = zid
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
    details['friends'] = re.sub(r'[\(\)]','', details['friends'])
    details['friends'] = details['friends'].split(', ')
    for i, friend in enumerate(details['friends']):
        details_filename = os.path.join(students_dir, friend, "student.txt")
        if os.path.exists(os.path.join(students_dir, friend, "img.jpg")):
            friendpic = os.path.join(students_dir, friend, "img.jpg") 
        else: friendpic = os.path.join("egg.gif")
        with open(details_filename) as f:
            for line in f:
                line = line.rstrip()
                if line.startswith('full_name'):
                    friend_name = line[len('full_name')+2:] 
                    break
        details['friends'][i] = [friend, friend_name, friendpic] 
    session['n'] = n + 1
    return render_template('start.html', **details, students_dir=students_dir) 

@app.route('/results', methods=['GET','POST'])
def results():
    if request.method == 'POST':
        query = request.form['query']
        print(type(query))
        students = sorted(os.listdir(students_dir))
        students = [x for x in students if not x.startswith('.')]
        result = []
        for student_to_show in students:
            details_filename = os.path.join(students_dir, student_to_show, "student.txt")
            with open(details_filename) as f:
                for line in f:
                    line = line.rstrip()
                    if line.startswith('full_name'):
                        name = line[len('full_name')+2:] 
                        break
            if query.lower() in name.lower():
                if os.path.exists(os.path.join(students_dir, student_to_show, "img.jpg")):
                    pic = os.path.join(students_dir, student_to_show, "img.jpg") 
                else: pic = os.path.join("egg.gif")
                result.append((student_to_show, name, pic))
        return render_template("results.html", result = result)
    # students = sorted(os.listdir(students_dir))
    # students = [x for x in students if not x.startswith('.')]
    # student_to_show = students[n % len(students)]

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        details_filename = os.path.join(students_dir, user_id, "student.txt")
        with open(details_filename) as f:
            this_zid = ''
            this_password = ''
            for line in f:
                line = line.rstrip()
                if line.startswith('zid'):
                    this_zid = line[len('zid')+2: ] 
                elif line.startswith('password'):
                    this_password = line[len('password')+2:] 
                elif line.startswith('full_name'):
                    name = line[len('full_name')+2: ] 
            if user_id == this_zid and password == this_password:
                print("yay i made it")
                resp = make_response(render_template("success.html"))
                resp.set_cookie('user_id', user_id)
                resp.set_cookie('user_name', name)
                return resp 
        return 'Failed Login'

@app.route('/logout', methods=['GET','POST'])
def logout():
    resp = make_response(render_template("logout.html"))
    resp.set_cookie('user_id', '', expires=0)
    resp.set_cookie('user_name', '', expires=0)
    return resp

if __name__ == '__main__':
    # app.secret_key = os.urandom(12)
    app.run(debug=True)
