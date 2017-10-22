#!/usr/bin/env python3
# !/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re, calendar
from datetime import date, datetime
from flask import Flask, render_template, session, request, make_response, redirect, url_for

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

def getDate(date):
    # 1 - year, 2 - month, 3 - day, 4 - time
    regex = re.match('([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}:[0-9]{2}).*', date)
    year = regex.group(1)
    month = calendar.month_name[int(regex.group(2))]
    day = regex.group(3)
    time = regex.group(4)
    return "{} {} {} at {}".format(day, month, year, time)
    # 13 October 2017 at 21:45

class Post:
    def __init__(self, file, post_id, zid=None, message=None, fmessage=None, comments=None, num_comments=0, time=None, dtime=None, related_to=None, hsh=None):
        self.file = file
        self.post_id = post_id
        self.num_comments = num_comments
        with open(self.file, 'r', encoding='utf8') as f:
            # 0. User name, 1. Time, 2. Message, 3. Post ID, 4. User Photo, 5. zID
            for line in f:
                line = line.rstrip()
                line = line.replace('\\n', '<br/>')
                if line.startswith('from'):
                    self.zid = line[len('from')+2: ]
                elif line.startswith('time'):
                    regex = '.*([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\+([0-9]{4})'
                    r = re.match(regex, line)
                    self.dtime = datetime(int(r.group(1)), int(r.group(2)), int(r.group(3)), int(r.group(4)), int(r.group(5)), int(r.group(6)))
                    self.time = getDate(line[len('time')+2: ])
                elif line.startswith('message'):
                    self.message = line[len('message')+2: ]
        self.fmessage = self.message
        if re.match('.*z[0-9]{7}.*', self.fmessage):
            for k, v in s.items():
                self.fmessage = self.fmessage.replace(k,'<a href="/user/'+k+'">'+v.full_name+'</a>')
        self.related_to = re.findall('z[0-9]{7}', self.message) + [self.zid]
        self.hsh = hash(file)
        self.getComments() 

    def getComments(self):
        comments = []
        comment_filenames = os.listdir(os.path.join(students_dir, self.zid))
        my_regex = self.post_id + r"-[0-9]+.txt"
        comment_filenames = [x for x in comment_filenames if re.match(my_regex, x)]
        comment_filenames.sort(key=self.sortComments, reverse=True)
        for comment_id in comment_filenames:
            file = os.path.join(students_dir, self.zid, comment_id) 
            comments.append(Comment(file, self.zid, comment_id[:-4]))
        self.comments = comments
        for comment in self.comments:
            self.num_comments += 1
            self.related_to += comment.related_to
        # Add in related to for comments to the main post.

    def sortComments(self, filename):
        match = re.match('.*-([0-9]+).txt', filename)
        return int(match.group(1))


class Comment:
    def __init__(self, file, parent_zid, post_id, comment_id=None, zid=None, message=None, fmessage=None, replies=None, num_replies=0, time=None, related_to=None, hsh=None):
        self.file = file
        self.post_id = post_id
        self.parent_zid = parent_zid
        self.message = ''
        self.num_replies = num_replies
        self.comment_id = self.file.split('-')[-1].replace('.txt','')
        with open(self.file, 'r', encoding='utf8') as f:
            # 0. User name, 1. Time, 2. Message, 3. Post ID, 4. User Photo, 5. zID
            for line in f:
                line = line.rstrip()
                line = line.replace('\\n', '<br/>')
                if line.startswith('from'):
                    self.zid = line[len('from')+2: ]
                elif line.startswith('time'):
                    self.time = getDate(line[len('time')+2: ])
                elif line.startswith('message'):
                    self.message = line[len('message')+2: ]
        self.fmessage = self.message
        if re.match('.*z[0-9]{7}.*', self.fmessage):
            for k, v in s.items():
                self.fmessage = self.fmessage.replace(k,'<a href="/user/'+k+'">'+v.full_name+'</a>')
        self.related_to = re.findall('z[0-9]{7}', self.message)
        self.hsh = hash(file)
        self.getReplies() 

    def getReplies(self):
        replies = []
        reply_filenames = os.listdir(os.path.join(students_dir, self.parent_zid))
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

class Reply:
    def __init__(self, file, parent_zid, post_id, reply_id=None, zid=None, message=None, fmessage=None, time=None, related_to=None, hsh=None):
        self.file = file
        self.post_id = post_id
        self.parent_zid = parent_zid
        self.message = ''
        self.reply_id = self.file.split('-')[-1].replace('.txt','')
        with open(self.file, 'r', encoding='utf8') as f:
            # 0. User name, 1. Time, 2. Message, 3. Post ID, 4. User Photo, 5. zID
            for line in f:
                line = line.rstrip()
                line = line.replace('\\n', '<br/>')
                if line.startswith('from'):
                    self.zid = line[len('from')+2: ]
                elif line.startswith('time'):
                    self.time = getDate(line[len('time')+2: ])
                elif line.startswith('message'):
                    self.message = line[len('message')+2: ]
        self.fmessage = self.message
        if re.match('.*z[0-9]{7}.*', self.fmessage):
            for k, v in s.items():
                self.fmessage = self.fmessage.replace(k,'<a href="/user/'+k+'">'+v.full_name+'</a>')
        self.related_to = re.findall('z[0-9]{7}', self.message) + [self.zid]
        self.hsh = hash(file)

class Student:
    def __init__(self, zid,
                 age=None, birthday=None, courses=None,
                 email=None, friends=None, full_name=None, 
                 home_latitude=None, home_longitude=None, 
                 home_suburb=None, password=None, picture=None,
                 posts=None, program=None):
        self.zid = zid
        self.refresh()

    def refresh(self):
        details = {}
        for field in fields:
            details[field] = ''
        details_filename = os.path.join(students_dir, self.zid, "student.txt")
        # USER DETAILS
        if os.path.exists(os.path.join(students_dir, self.zid, "img.jpg")):
            details['picture'] = os.path.join(students_dir, self.zid, "img.jpg") 
        else: details['picture'] = os.path.join("egg.gif")
        with open(details_filename) as f:
            for line in f:
                line = line.rstrip()
                for field in fields:
                    if line.startswith(field):
                        details[field] = line[len(field)+2:] 
                        break
        details['age'] = date.today() - date(int(details['birthday'][ :4]), int(details['birthday'][5:7]), int(details['birthday'][8:10]))  
        details['age'] = int(details['age'].days // 365.25)
        
        # FRIEND LIST
        details['friends'] = re.sub(r'[\(\)]','', details['friends'])
        details['friends'] = details['friends'].split(', ')

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
        post_filenames = sorted(os.listdir(os.path.join(students_dir, self.zid)), reverse=True)
        post_filenames = [x for x in post_filenames if re.match('[0-9]+.txt', x)]
        post_filenames.sort(key = lambda x: int(x.split('.')[0]))
        for post_id in post_filenames:
            file = os.path.join(students_dir, self.zid, post_id)
            posts.append(Post(file, post_id[:-4]))
        self.posts = posts

    def getPosts(self):
        my_related = []
        for key, student in s.items():
            for post in student.posts:
                if self.zid in post.related_to:
                    my_related.append(post)
        return my_related

def updateStudentList():
    for zid in [x for x in os.listdir(students_dir) if not x.startswith('.')]:
        if not zid in s:
            s[zid] = Student(zid)
        else:
            s[zid].refresh()

# Dictionary in which to store all out of our students
# store all of the students info as objects in our dictionary
s = {}
updateStudentList()
for k, v in s.items():
    v.refreshPosts()

@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
def start():
    #posts
    # post_id = 0
    student_to_show = request.cookies.get('user_id') 
    if not student_to_show:
        return render_template('start.html')
    related_posts = s[student_to_show].getPosts()
    related_posts.sort(key=lambda x: x.dtime, reverse=True)
    # for p in related_posts:
    # #     print(s[p.zid].full_name, p.time, p.message)
    #     for c in p.comments:
    # #         print('comment:', s[c.zid].full_name, c.time, c.message)
    #         for r in c.replies:
    #             if 'z' in r.message:
    #                 print('comment reply:', r.message)
    #                 print('              ', r.fmessage)


    # posts = []
    # post_filenames = sorted(os.listdir(os.path.join(students_dir, student_to_show)), reverse=True)
    # post_filenames = [x for x in post_filenames if re.match('[0-9]+.txt', x)]
    # post_filenames.sort(key = lambda x: int(x.split('.')[0]), reverse=True)
    # post_fields = ['time', 'from', 'msg']
    # for file in post_filenames:
    #     # print("FILE:",file)
    #     file = os.path.join(students_dir, student_to_show, file)
    #     with open(file, 'r', encoding='utf8') as f:
    #         # 0. User name, 1. Time, 2. Message, 3. Post ID, 4. User Photo, 5. zID
    #         posts.append(['','','', str(post_id), '', '', []])
    #         for line in f:
    #             line = line.rstrip()
    #             line = line.replace('\\n', '<br/>')
    #             if line.startswith('from'):
    #                 posts[-1][0] = getName(line[len('from')+2: ])
    #                 posts[-1][4] = getPicture(line[len('from')+2: ])
    #                 posts[-1][5] = line[len('from')+2: ]
    #             elif line.startswith('time'):
    #                 posts[-1][1] = getDate(line[len('time')+2: ])
    #             elif line.startswith('message'):
    #                 posts[-1][2] = line[len('message')+2: ]
    #     post_id += 1
    return render_template('start.html', posts=related_posts, s=s) 

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
    elif zid is None and request.cookies.get('user_id'):
        student_to_show = request.cookies.get('user_id') 
    else: 
        student_to_show = zid
    session['n'] = n + 1
    return render_template('profile.html', students_dir=students_dir, s=s, student=student_to_show) 

@app.route('/results', methods=['GET','POST'])
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
                if query in p.fmessage:
                    posts.append(p)
                for c in p.comments:
                    if query in c.fmessage:
                        comments.append(c)
                    for r in c.replies:
                        if query in r.fmessage:
                            replies.append(r)

        # for student_to_show in students:
        #     details_filename = os.path.join(students_dir, student_to_show, "student.txt")
        #     with open(details_filename) as f:
        #         for line in f:
        #             line = line.rstrip()
        #             if line.startswith('full_name'):
        #                 name = line[len('full_name')+2:] 
        #                 break
        #     if query.lower() in name.lower():
        #         if os.path.exists(os.path.join(students_dir, student_to_show, "img.jpg")):
        #             pic = os.path.join(students_dir, student_to_show, "img.jpg") 
        #         else: pic = os.path.join("egg.gif")
        #         result.append((student_to_show, name, pic))
        return render_template("results.html", s=s, people=people, posts=posts, comments=comments, replies=replies) 
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
                resp = make_response(render_template("success.html"))
                resp.set_cookie('user_id', user_id)
                resp.set_cookie('user_name', name)
                return resp 
        return 'Failed Login'

@app.route('/newpost', methods=['GET','POST'])
def newpost():
    if request.method == 'POST':
        student = request.cookies.get('user_id') 
        post_filenames = sorted(os.listdir(os.path.join(students_dir, student)), reverse=True)
        post_filenames = [int(x.replace('.txt','')) for x in post_filenames if re.match('[0-9]+.txt', x)]
        newpost_filename = str(max(post_filenames)+1)+'.txt'
        post = request.form['message']
        post = post.replace('\r', '')
        post = post.replace('\n', '<br/>')
        with open(os.path.join(students_dir, student, newpost_filename), 'w') as f:
            f.write('time: '+ datetime.now().strftime('%Y-%m-%dT%H:%M:%S+0000')+'\n')
            f.write('from: '+student+'\n')
            f.write('longitude: 150.3226\n')
            f.write('latitude: -33.7140\n')
            f.write('message: '+post)
        s[student].refreshPosts()
        return redirect(url_for('start'))

@app.route('/newcomment', methods=['GET','POST'])
def newcomment():
    if request.method == 'POST':
        student = request.cookies.get('user_id') 
        post_zid = request.form['post_zid']
        post_id = request.form['post_id']
        message = request.form['comment']
        num_comments = s[post_zid].posts[int(post_id)].num_comments
        newcomment_filename = post_id + '-' + str(num_comments) + '.txt'
        with open(os.path.join(students_dir, post_zid, newcomment_filename), 'w') as f:
            f.write('time: '+ datetime.now().strftime('%Y-%m-%dT%H:%M:%S+0000')+'\n')
            f.write('from: '+student+'\n')
            f.write('message: '+message)
        s[post_zid].refreshPosts()
        return redirect(url_for('start'))

@app.route('/newreply', methods=['GET','POST'])
def newreply():
    if request.method == 'POST':
        student = request.cookies.get('user_id') 
        post_zid = request.form['post_zid']
        post_id = request.form['post_id']
        comment_id = request.form['comment_id']
        message = request.form['comment']
        num_replies = s[post_zid].posts[int(post_id)].comments[int(comment_id)].num_replies
        newreply_filename = post_id + '-' + comment_id + '-' + str(num_replies) + '.txt'
        with open(os.path.join(students_dir, post_zid, newreply_filename), 'w') as f:
            f.write('time: '+ datetime.now().strftime('%Y-%m-%dT%H:%M:%S+0000')+'\n')
            f.write('from: '+student+'\n')
            f.write('message: '+message)
        s[post_zid].refreshPosts()
        return redirect(url_for('start'))

@app.route('/logout', methods=['GET','POST'])
def logout():
    resp = make_response(render_template("logout.html"))
    resp.set_cookie('user_id', '', expires=0)
    resp.set_cookie('user_name', '', expires=0)
    return resp

def getName(zid):
    details_filename = os.path.join(students_dir, zid, "student.txt")
    with open(details_filename) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith('full_name'):
                name = line[len('full_name')+2:] 
                return name

def getPicture(zid):
    if os.path.exists(os.path.join(students_dir, zid, "img.jpg")):
        picture = os.path.join(students_dir, zid, "img.jpg") 
    else:
        picture = os.path.join("egg.gif")
    return picture

if __name__ == '__main__':
    # app.secret_key = os.urandom(12)
    app.run(debug=True)
