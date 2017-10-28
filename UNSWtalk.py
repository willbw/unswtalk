#!/usr/bin/env python3
# !/web/cs2041/bin/python3.6.3

import os
import re
import calendar
from datetime import date, datetime
from flask import Flask, render_template, session, request, make_response, redirect, url_for
from shutil import copy

students_dir = os.path.join("static", "dataset-medium")

app = Flask(__name__)
app.secret_key = os.urandom(12)
app.config['TEMPLATES_AUTO_RELOAD'] = True

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

# Re-formats dates from the supplied dataset in format '01 January 2017 at 18:45'

def getDate(date):
    regex = re.match(
        '([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}:[0-9]{2}).*',
        date)
    year = regex.group(1)
    month = calendar.month_name[int(regex.group(2))]
    day = regex.group(3)
    time = regex.group(4)
    return "{} {} {} at {}".format(day, month, year, time)

# Post data object
#
# Stores all information for each post, including its file location, author (zid), messsage,
# formatted message (fmessage), an array containing all comments, the number of comments,
# the time the post was written, a formatted date (dtime), an array of users that are
# 'related to' this post (if a user is an author or they are tagged in a post),
# and a unique hash value we use to identity the post in the news feed.

class Post:
    def __init__(
            self,
            file,
            post_id,
            zid=None,
            message=None,
            fmessage=None,
            comments=None,
            num_comments=0,
            time=None,
            dtime=None,
            related_to=None,
            hsh=None):
        self.file = file
        self.post_id = post_id
        self.num_comments = num_comments
        with open(self.file, 'r', encoding='utf8') as f:
            for line in f:
                line = line.rstrip()
                line = line.replace('\\n', '<br/>')
                if line.startswith('from'):
                    self.zid = line[len('from') + 2:]
                elif line.startswith('time'):
                    regex = '.*([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\+([0-9]{4})'
                    r = re.match(regex, line)
                    self.dtime = datetime(int(r.group(1)), int(r.group(2)), int(
                        r.group(3)), int(r.group(4)), int(r.group(5)), int(r.group(6)))
                    self.time = getDate(line[len('time') + 2:])
                elif line.startswith('message'):
                    self.message = line[len('message') + 2:]
        self.fmessage = self.message
        if re.match('.*z[0-9]{7}.*', self.fmessage):
            for k, v in s.items():
                self.fmessage = self.fmessage.replace(
                    k, '<a href="user/' + k + '">' + v.full_name + '</a>')
        self.related_to = re.findall('z[0-9]{7}', self.message) + [self.zid]
        self.hsh = hash(file)
        self.getComments()

    def getComments(self):
        comments = []
        comment_filenames = os.listdir(os.path.join(students_dir, self.zid))
        my_regex = self.post_id + r"-[0-9]+.txt"
        comment_filenames = [
            x for x in comment_filenames if re.match(
                my_regex, x)]
        comment_filenames.sort(key=self.sortComments, reverse=True)
        for comment_id in comment_filenames:
            file = os.path.join(students_dir, self.zid, comment_id)
            comments.append(Comment(file, self.zid, comment_id[:-4]))
        self.comments = comments
        for comment in self.comments:
            self.num_comments += 1
            self.related_to += comment.related_to

    def sortComments(self, filename):
        match = re.match('.*-([0-9]+).txt', filename)
        return int(match.group(1))

# Comment data object
#
# Similar structure to Post object, however we keep track of replies and also
# the parent post

class Comment:
    def __init__(
            self,
            file,
            parent_zid,
            post_id,
            comment_id=None,
            zid=None,
            message=None,
            fmessage=None,
            replies=None,
            num_replies=0,
            time=None,
            related_to=None,
            hsh=None):
        self.file = file
        self.post_id = post_id
        self.parent_zid = parent_zid
        self.message = ''
        self.num_replies = num_replies
        self.comment_id = self.file.split('-')[-1].replace('.txt', '')
        with open(self.file, 'r', encoding='utf8') as f:
            # 0. User name, 1. Time, 2. Message, 3. Post ID, 4. User Photo, 5.
            # zID
            for line in f:
                line = line.rstrip()
                line = line.replace('\\n', '<br/>')
                if line.startswith('from'):
                    self.zid = line[len('from') + 2:]
                elif line.startswith('time'):
                    self.time = getDate(line[len('time') + 2:])
                elif line.startswith('message'):
                    self.message = line[len('message') + 2:]
        self.fmessage = self.message
        if re.match('.*z[0-9]{7}.*', self.fmessage):
            for k, v in s.items():
                self.fmessage = self.fmessage.replace(
                    k, '<a href="user/' + k + '">' + v.full_name + '</a>')
        self.related_to = re.findall('z[0-9]{7}', self.message)
        self.hsh = hash(file)
        self.getReplies()

    def getReplies(self):
        replies = []
        reply_filenames = os.listdir(
            os.path.join(
                students_dir,
                self.parent_zid))
        my_regex = self.post_id + r"-[0-9]+.txt"
        reply_filenames = [x for x in reply_filenames if re.match(my_regex, x)]
        reply_filenames.sort(key=self.sortReplies, reverse=True)
        for reply_id in reply_filenames:
            file = os.path.join(students_dir, self.parent_zid, reply_id)
            replies.append(Reply(file, self.parent_zid, reply_id[:-4]))
        self.replies = replies
        for reply in replies:
            self.num_replies += 1
            self.related_to += reply.related_to + [self.zid]
        # Add in related to for comments to the main post.

    def sortReplies(self, filename):
        match = re.match('.*-.*-([0-9]+).txt', filename)
        return int(match.group(1))

# Reply data object
#
# Similar to Comment data object, however you are unable to reply to replies so this 
# is the lowest level possible in a post/comment chain

class Reply:
    def __init__(
            self,
            file,
            parent_zid,
            post_id,
            reply_id=None,
            zid=None,
            message=None,
            fmessage=None,
            time=None,
            related_to=None,
            hsh=None):
        self.file = file
        self.post_id = post_id
        self.parent_zid = parent_zid
        self.message = ''
        self.reply_id = self.file.split('-')[-1].replace('.txt', '')
        with open(self.file, 'r', encoding='utf8') as f:
            # 0. User name, 1. Time, 2. Message, 3. Post ID, 4. User Photo, 5.
            # zID
            for line in f:
                line = line.rstrip()
                line = line.replace('\\n', '<br/>')
                if line.startswith('from'):
                    self.zid = line[len('from') + 2:]
                elif line.startswith('time'):
                    self.time = getDate(line[len('time') + 2:])
                elif line.startswith('message'):
                    self.message = line[len('message') + 2:]
        self.fmessage = self.message
        if re.match('.*z[0-9]{7}.*', self.fmessage):
            for k, v in s.items():
                self.fmessage = self.fmessage.replace(
                    k, '<a href="user/' + k + '">' + v.full_name + '</a>')
        self.related_to = re.findall('z[0-9]{7}', self.message) + [self.zid]
        self.hsh = hash(file)

# Student data type
#
# Stores all the information from student.txt in one data object, and keeps track
# of all posts by the student.
# Able to be refreshed entirely, or just for the student's posts to be refreshed
# (if we have had a new post made).
# getPosts() function will get all related posts for the student, for
# publishing on the news feed.

class Student:
    def __init__(
            self,
            zid,
            age=None,
            birthday=None,
            courses=None,
            email=None,
            friends=None,
            full_name=None,
            home_latitude=None,
            home_longitude=None,
            home_suburb=None,
            password=None,
            picture=None,
            posts=None,
            program=None,
            ptext=None):
        self.zid = zid
        self.refresh()

    def refresh(self):
        details = {}
        for field in fields:
            details[field] = ''
        details_filename = os.path.join(students_dir, self.zid, "student.txt")
        ptext_filename = os.path.join(
            students_dir, self.zid, "profile_text.txt")
        # USER DETAILS
        if os.path.exists(os.path.join(students_dir, self.zid, "img.jpg")):
            details['picture'] = os.path.join(
                students_dir, self.zid, "img.jpg")
            details['picture'] = details['picture'].replace('static/', '')
        else:
            details['picture'] = os.path.join("egg.gif")
        with open(details_filename) as f:
            for line in f:
                line = line.rstrip()
                for field in fields:
                    if line.startswith(field):
                        details[field] = line[len(field) + 2:]
                        break
        details['age'] = date.today() - date(int(details['birthday'][:4]),
                                             int(details['birthday'][5:7]), int(details['birthday'][8:10]))
        details['age'] = int(details['age'].days // 365.25)
        if os.path.exists(ptext_filename):
            with open(ptext_filename) as f:
                self.profile_text = f.read()
        else:
            self.profile_text = 'Put some profile text here!'

        # FRIEND LIST
        details['friends'] = re.sub(r'[\(\)]', '', details['friends'])
        details['friends'] = details['friends'].split(', ')
        # COURSE LIST
        details['courses'] = re.sub(r'[\(\)]', '', details['courses'])
        if details['courses'] == '':
            details['courses'] = []
        else:
            details['courses'] = details['courses'].split(', ')
        self.age = details['age']
        self.birthday = details['birthday']
        self.courses = details['courses']
        self.email = details['email']
        self.friends = details['friends']
        self.full_name = details['full_name']
        self.home_latitude = details['home_latitude']
        self.home_longitude = details['home_longitude']
        self.home_suburb = details['home_suburb']
        self.password = details['password']
        self.picture = details['picture']
        self.program = details['program']

    def refreshPosts(self):
        # Posts
        posts = []
        post_filenames = sorted(
            os.listdir(
                os.path.join(
                    students_dir,
                    self.zid)),
            reverse=True)
        post_filenames = [
            x for x in post_filenames if re.match(
                '[0-9]+.txt', x)]
        post_filenames.sort(key=lambda x: int(x.split('.')[0]))
        for post_id in post_filenames:
            file = os.path.join(students_dir, self.zid, post_id)
            posts.append(Post(file, post_id[:-4]))
        self.posts = posts

    def getPosts(self):
        my_related = []
        for key, student in s.items():
            if student.posts:
                for post in student.posts:
                    if self.zid in post.related_to:
                        my_related.append(post)
        return my_related

# updateStudentList initalises all of our students in the s dictionary

def updateStudentList():
    for zid in [x for x in os.listdir(students_dir) if not x.startswith('.')]:
        if zid not in s:
            s[zid] = Student(zid)
        else:
            s[zid].refresh()


# 's' is a dictionary in which to store all out of our students as objects
# where zid is the key to the dictionary
s = {}
updateStudentList()
for k, v in s.items():
    v.refreshPosts()

# This functionality disabled temporarily

# @app.after_request
# def add_header(r):
#     # Code taken from StackOverflow
#     """
#     Add headers to both force latest IE rendering engine or Chrome Frame,
#     and also to cache the rendered page for 10 minutes.
#     """
#     r.headers["Pragma"] = "no-cache"
#     r.headers["Expires"] = "0"
#     r.headers['Cache-Control'] = 'public, max-age=0'
#     return r


# If no cookie for user, render registration page
# otherwise, render news feed

@app.route('/', methods=['GET', 'POST'])
@app.route('/start', methods=['GET', 'POST'])
def start(err=None):
    student_to_show = request.cookies.get('user_id')
    if not student_to_show:
        return render_template('register.html')
    related_posts = s[student_to_show].getPosts()
    related_posts.sort(key=lambda x: x.dtime, reverse=True)
    return render_template('feed.html', posts=related_posts, s=s)

# Profile page
# Optional to specify zid - if not specified,
# return user's profile who is logged in

@app.route('/user/<zid>', methods=['GET', 'POST'])
def user(zid=None):
    n = session.get('n', 0)
    if zid is None and request.cookies.get('user_id') is None:
        students = sorted(os.listdir(students_dir))
        students = [x for x in students if not x.startswith('.')]
        student_to_show = students[n % len(students)]
    elif zid is None and request.cookies.get('user_id'):
        student_to_show = request.cookies.get('user_id')
    else:
        student_to_show = zid
    session['n'] = n + 1
    return render_template(
        'profile.html',
        students_dir=students_dir,
        s=s,
        student=student_to_show)

# Search results
# Case insensitive search of all people and posts
# if part of query matches any of the text in the person's
# full name or their message

@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        query = request.form['query']
        people = []
        posts = []
        comments = []
        replies = []

        for k, v in s.items():
            if query.lower() in v.full_name.lower():
                people.append(k)
            for p in v.posts:
                if query.lower() in p.fmessage.lower():
                    posts.append(p)
                # for c in p.comments:
                #     if query.lower() in c.fmessage.lower():
                #         comments.append(c)
                #     for r in c.replies:
                #         if query.lower() in r.fmessage.lower():
                #             replies.append(r)
        return render_template(
            "results.html",
            s=s,
            people=people,
            posts=posts,
            comments=comments,
            replies=replies)

# Login
# Look up password associated with the user's zid and see if it matches
# what was provided at login. If so, log user in and set cookies

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        details_filename = os.path.join(students_dir, user_id, "student.txt")
        try:
            with open(details_filename) as f:
                this_zid = ''
                this_password = ''
                for line in f:
                    line = line.rstrip()
                    if line.startswith('zid'):
                        this_zid = line[len('zid') + 2:]
                    elif line.startswith('password'):
                        this_password = line[len('password') + 2:]
                    elif line.startswith('full_name'):
                        name = line[len('full_name') + 2:]
                if user_id == this_zid and password == this_password:
                    resp = make_response(render_template("success.html"))
                    resp.set_cookie('user_id', user_id)
                    resp.set_cookie('user_name', name)
                    return resp
        except OSError:
            return render_template(
                "register.html",
                err='zID is not registered.')
        return render_template("register.html", err='Password incorrect.')

# New Post
# When making a new post, format the post correctly (replace newlines with breaks)
# and write the post with the correct filename into the user's directory
# and then refresh that user's posts so that their news feed will render
# correctly

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    if request.method == 'POST':
        student = request.cookies.get('user_id')
        post_filenames = sorted(
            os.listdir(
                os.path.join(
                    students_dir,
                    student)),
            reverse=True)
        post_filenames = [int(x.replace('.txt', ''))
                          for x in post_filenames if re.match('[0-9]+.txt', x)]
        if post_filenames:
            newpost_filename = str(max(post_filenames) + 1) + '.txt'
        else:
            newpost_filename = '0.txt'
        post = request.form['message']
        post = post.replace('\r', '')
        post = post.replace('\n', '<br/>')
        with open(os.path.join(students_dir, student, newpost_filename), 'w') as f:
            f.write(
                'time: ' +
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S+0000') +
                '\n')
            f.write('from: ' + student + '\n')
            f.write('longitude: 150.3226\n')
            f.write('latitude: -33.7140\n')
            f.write('message: ' + post)
        s[student].refreshPosts()
        return redirect(url_for('start'))

# New Comment
# Based off new post

@app.route('/newcomment', methods=['GET', 'POST'])
def newcomment():
    if request.method == 'POST':
        student = request.cookies.get('user_id')
        post_zid = request.form['post_zid']
        post_id = request.form['post_id']
        message = request.form['comment']
        num_comments = s[post_zid].posts[int(post_id)].num_comments
        newcomment_filename = post_id + '-' + str(num_comments) + '.txt'
        with open(os.path.join(students_dir, post_zid, newcomment_filename), 'w') as f:
            f.write(
                'time: ' +
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S+0000') +
                '\n')
            f.write('from: ' + student + '\n')
            f.write('message: ' + message)
        s[post_zid].refreshPosts()
        return redirect(url_for('start'))

# New reply
# Based off new post

@app.route('/newreply', methods=['GET', 'POST'])
def newreply():
    if request.method == 'POST':
        student = request.cookies.get('user_id')
        post_zid = request.form['post_zid']
        post_id = request.form['post_id']
        comment_id = request.form['comment_id']
        message = request.form['comment']
        num_replies = s[post_zid].posts[int(
            post_id)].comments[int(comment_id)].num_replies
        newreply_filename = post_id + '-' + \
            comment_id + '-' + str(num_replies) + '.txt'
        with open(os.path.join(students_dir, post_zid, newreply_filename), 'w') as f:
            f.write(
                'time: ' +
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S+0000') +
                '\n')
            f.write('from: ' + student + '\n')
            f.write('message: ' + message)
        s[post_zid].refreshPosts()
        return redirect(url_for('start'))

# Delete Post
# This can be used for comments, replies or posts.
# I have decided not to erase the original file, but instead just replace
# the message with [Deleted]. This way the original comment structure around
# can remain.

@app.route('/deletepost', methods=['GET', 'POST'])
def deletepost():
    if request.method == 'POST':
        post_zid = request.form['post_zid']
        fname = request.form['fname']
        with open(fname, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.startswith('message:'):
                    lines[i] = 'message: [Deleted]\n'
        with open(fname, 'w') as f:
            f.writelines(lines)
        s[post_zid].refreshPosts()
    return redirect(url_for('start'))

# New Account
# Retrieves the information from the registration form, checks to see that
# the zid is not already registered, and then creates a new directory for the
# new user and writes to student.txt. The user is then logged in

@app.route('/newaccount', methods=['GET', 'POST'])
def newaccount():
    if request.method == 'POST':
        zid = request.form['inputzID']
        if os.path.exists(os.path.join(students_dir, zid)):
            return render_template(
                "register.html",
                err2='zID is already registered.')
        else:
            os.mkdir(os.path.join(students_dir, zid))
            # os.mkdir(os.path.join('static',students_dir, zid))
            full_name = request.form['inputName']
            full_name = ' '.join([x.capitalize() for x in full_name.split()])
            password = request.form['inputPassword']
            email = request.form['inputEmail']
            birthday = request.form['inputBday']
            program = request.form['inputProgram']
            home_suburb = request.form['inputSuburb']
            with open(os.path.join(students_dir, zid, 'student.txt'), 'w') as f:
                f.write('zid: ' + zid + '\n')
                f.write('full_name: ' + full_name + '\n')
                f.write('birthday: ' + birthday + '\n')
                f.write('password: ' + password + '\n')
                f.write('email: ' + email + '\n')
                f.write('program: ' + program + '\n')
                f.write('home_suburb: ' + home_suburb + '\n')
                f.write('home_longitude: 151.2005\n')
                f.write('home_latitude: -33.6672\n')
                f.write('friends: (z5195995)\n')
                f.write('courses: ()\n')
            picture = request.form.get(
                'inputPicture', None)  # remember this is optional
            resp = make_response(render_template("success.html"))
            resp.set_cookie('user_id', zid)
            resp.set_cookie('user_name', full_name)
            updateStudentList()
            for k, v in s.items():
                v.refreshPosts()
            return resp
    return redirect(url_for('start'))

# Logout
# Removes cookies and logs user out

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    resp = make_response(render_template("logout.html"))
    resp.set_cookie('user_id', '', expires=0)
    resp.set_cookie('user_name', '', expires=0)
    return resp

# Edit profile
# Simply a redirect for the user to the edit profile page

@app.route('/editprofile', methods=['GET', 'POST'])
def editprofile():
    student = request.cookies.get('user_id')
    student = s[student]
    return render_template("editprofile.html", student=student)

# Submit Edit
# This function commits the edits to file. We will write over student.txt
# and any amendments to the existing profile will be present in the new profile

@app.route('/submitedit', methods=['GET', 'POST'])
def submitedit():
    if request.method == 'POST':
        student = request.cookies.get('user_id')
        full_name = request.form['inputName']
        full_name = ' '.join([x.capitalize() for x in full_name.split()])
        password = request.form['inputPassword']
        email = request.form['inputEmail']
        birthday = request.form['inputBday']
        program = request.form['inputProgram']
        home_suburb = request.form['inputSuburb']
        profile_text = request.form['inputPText']
        courses = request.form['inputCourses']
        if not courses:
            courses = ''
        with open(os.path.join(students_dir, student, 'student.txt'), 'w') as f:
            f.write('zid: ' + student + '\n')
            f.write('full_name: ' + full_name + '\n')
            f.write('birthday: ' + birthday + '\n')
            f.write('password: ' + password + '\n')
            f.write('email: ' + email + '\n')
            f.write('program: ' + program + '\n')
            f.write('home_suburb: ' + home_suburb + '\n')
            f.write('home_longitude: 151.2005\n')
            f.write('home_latitude: -33.6672\n')
            f.write('friends: ' +
                    '(' + ', '.join([x for x in s[student].friends]) + ')\n')
            f.write('courses: (' + courses + ')\n')
        with open(os.path.join(students_dir, student, 'profile_text.txt'), 'w') as f:
            f.write(profile_text)
        picture = request.form.get(
            'inputPicture',
            None)  # remember this is optional
        if 'file' in request.files:
            pic = request.files['file']
            if pic.filename != '':
                # pic.save(os.path.join('static', students_dir, student, 'img.jpg'))
                pic.save(os.path.join(students_dir, student, 'img.jpg'))
        s[student].refresh()
        return redirect(url_for('user', zid=student))
    return redirect(url_for('start'))

# Add Friend
# Friend requests are yet to be implemented, so if you add a friend - they are
# your friend. First we get the current list of friends, then we append the new 
# friend to it, reassemble the list of friends and write it to our student.txt file.

@app.route('/addfriend/<friend>', methods=['GET', 'POST'])
def addfriend(friend):
    student = request.cookies.get('user_id')
    details_filename = os.path.join(students_dir, student, "student.txt")
    with open(details_filename) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith('friends'):
                friends = line[len('friends') + 2:]
                break
    friends = re.sub(r'[\(\)]', '', friends)
    friends = friends.split(', ')
    if '' in friends:
        friends.remove('')
    friends.append(friend)
    friends = 'friends: (' + ', '.join(friends) + ')\n'
    st = s[student]  # Current Student
    with open(os.path.join(students_dir, student, 'student.txt'), 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith('friends'):
                lines[i] = friends
    with open(os.path.join(students_dir, student, 'student.txt'), 'w') as f:
        f.writelines(lines)
    st.refresh()
    return redirect(url_for('user', zid=student))

# Remove Friend
# The opposite process to add friend.

@app.route('/removefriend/<friend>', methods=['GET', 'POST'])
def removefriend(friend):
    student = request.cookies.get('user_id')
    details_filename = os.path.join(students_dir, student, "student.txt")
    with open(details_filename) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith('friends'):
                friends = line[len('friends') + 2:]
                break
    friends = re.sub(r'[\(\)]', '', friends)
    friends = friends.split(', ')
    friends.remove(friend)
    if not friends:
        friends = 'friends: ()\n'
    else:
        friends = 'friends: (' + ', '.join(friends) + ')\n'
    st = s[student]  # Current Student
    with open(os.path.join(students_dir, student, 'student.txt'), 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith('friends'):
                lines[i] = friends
    with open(os.path.join(students_dir, student, 'student.txt'), 'w') as f:
        f.writelines(lines)
    st.refresh()
    return redirect(url_for('user', zid=student))

# Friend Suggestions
# FriendScore = ( 2 * Common Friends ) + ( Common Classes )
# comparing two students, 'a' and 'b', and giving them a score approximating how
# likely it is they will be friends. I have weighted more heaviliy common friends,
# as I think if you have taken some common classes you may not know the person,
# but if you have a few common friends - it is more likely you will socialise with
# this person.

@app.route('/friendsuggestions/<n>', methods=['GET', 'POST'])
def friendsuggestions(n=None):
    a = request.cookies.get('user_id')
    d = {}
    if not n:
        n = 0
    else:
        n = max(0, int(n))
    for b in [x for x in s if x != a and x not in s[a].friends]:
        d[s[b].zid] = 2 * len(set(s[a].friends) & set(s[b].friends)) + \
            len(set(s[a].courses) & set(s[b].courses))
    recs = sorted(d.items(), key=lambda x: x[1], reverse=True)
    max_n = min(len(recs), n + 10)
    ten_recs = recs[n: max_n]
    return render_template(
        'friendsuggestions.html',
        recs=ten_recs,
        n=n,
        s=s,
        max_n=max_n)

if __name__ == '__main__':
    # app.secret_key = os.urandom(12)
    app.run(debug=True)