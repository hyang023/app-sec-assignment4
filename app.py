import os
import random
from datetime import datetime
import subprocess
from subprocess import check_output
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

uname = ''
pword = ''

logincount = 0
loginaddon = random.randrange(1,100)
querycount = 0
queryaddon = random.randrange(1,100)
loggedin = ''

#def create_app(config=None):
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(80))
    twofactr = db.Column(db.String(20))
    queries  = db.relationship('Query', backref=db.backref('user', lazy='joined'), lazy='select')
    logins   = db.relationship('Login', backref=db.backref('user', lazy='joined'), lazy='select')
    def __repr__(self):
        return '<User %r>' % self.username

class Query(db.Model):
    query_id = db.Column(db.Integer(), primary_key=True)
    querytxt = db.Column(db.Text())
    misspell = db.Column(db.Text())
    queryusr = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    def __repr__(self):
        return '<Query %r>' % self.username
    
class Login(db.Model):
    login_id = db.Column(db.Integer(), primary_key=True)
    logitime = db.Column(db.String(30))
    logotime = db.Column(db.String(30))
    loginusr = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    def __repr__(self):
        return '<Login %r>' % self.username

db.drop_all() 
db.create_all()    

admin = User(username='admin', password='Administrator@1', twofactr='12345678901')
db.session.add(admin)
db.session.commit()
    
    #return app

@app.route('/')
def hello_world():
    alllogins = Login.query.all()
    countlogins = len(alllogins)
    output = "num logins is "+str(countlogins)
    for login in alllogins:
        output = output+" query: "+str(login.login_id)
    global logincount
    global loginaddon
    output = output+" and current loginid is "+str(logincount+loginaddon)
    return output

@app.route('/register', methods=['post', 'get'])
def register():
    value=random.randrange(1,100)
    message = ''
    if request.method == 'POST':
        uname = request.form.get('uname')
        pword = request.form.get('pword')
        twofa = request.form.get('2fa')
        if uname  and pword :
            checkuser = User.query.filter_by(username=uname).first()
            if checkuser is not None:
                message="Failure: username already exists"
            else:
                if twofa:
                    if not twofa.isdigit():
                        twofa = 'no'
                adduser = User(username=uname, password=pword, twofactr=twofa)
                db.session.add(adduser)
                db.session.commit()
                message = "Success. Your username is "+uname
    return render_template('registration.html', message=message, value=value)

@app.route('/login',  methods=['post', 'get'])
def login():
    value=random.randrange(1,100)
    message = ''
    if request.method == 'POST':
        uname = request.form.get('uname')
        pword = request.form.get('pword')
        twofa = request.form.get('2fa')
        if uname  and pword :
            checkuser = User.query.filter_by(username=uname).first()
            if checkuser is not None and str(checkuser.password) == pword:
                if str(checkuser.twofactr) == 'no' or str(checkuser.twofactr) == twofa:
                    now = datetime.now()
                    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    global logincount
                    global loginaddon
                    logincount = logincount + 1
                    loginnum = logincount+loginaddon
                    addlogin = Login(login_id=loginnum,logitime=current_time,logotime='N/A',loginusr=uname)
                    db.session.add(addlogin)
                    db.session.commit()
                    global loggedin
                    loggedin = uname
                    message = "Success "+uname+" is logged in at "+current_time
                else:
                    message = "Two-factor authentication failure"
            else:
                message = "Invalid login for "+uname
    return render_template('login.html', message=message, value=value)

@app.route('/login_success', methods=['POST'])
def login_success():
    return render_template('login_success.html')

@app.route('/logout')
def logout():
    message = ''
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    global loggedin
    if loggedin:
        global logincount
        loginnum = logincount+loginaddon
        checklogin = Login.query.filter_by(login_id=loginnum).first()
        checklogin.logotime = current_time
        db.session.commit()
        message = 'logged out'
        loggedin = ''
    else:
       message = 'you must be logged in to log out'
    return message

@app.route('/spell_check', methods=['post', 'get'])
def spell_check():
    value=random.randrange(1,100)
    message = ''
    message2 = ''
    if request.method == 'POST':
        inputtext = request.form.get('inputtext')
        if inputtext:
            global loggedin
            if not loggedin:
                message = "Please login and try again"
            else:
                message = "Supplied Text: "+inputtext
                f= open("test1.txt","w+")
                f.write(inputtext)
                f.close() 
                stdout = check_output(['chmod','755','a.out'])
                stdout = check_output(['./a.out','test1.txt','wordlist.txt']).decode('utf-8')
                os.remove("test1.txt")
                message2 = "Misspelled words: "+stdout
                global querycount
                global queryaddon
                querycount = querycount+1
                querynum = querycount+queryaddon
                addquery = Query(query_id=querynum,querytxt=inputtext,misspell=stdout,queryusr=loggedin)
                db.session.add(addquery)
                db.session.commit()
    return render_template('spellcheck.html', message=message, message2=message2, value=value)

@app.route('/history', methods=['post', 'get'])
def history():
    value=random.randrange(1,100)
    message1 = ''
    message2 = []
    global loggedin  
    if request.method == 'POST':
        inputtext = request.form.get('inputtext')
        if loggedin == 'admin' and inputtext:
            checkquery = Query.query.filter_by(queryusr=str(inputtext)).all()
            for eachquery in checkquery:
                message2.append(str(eachquery.query_id))
            message1 = "you have made "+str(len(checkquery))+" queries"
        elif loggedin:
            checkquery = Query.query.filter_by(queryusr=loggedin).all()
            for eachquery in checkquery:
                message2.append(str(eachquery.query_id))
            message1 = "you have made "+str(len(checkquery))+" queries"
    return render_template('history.html', message1=message1, message2=message2, user=loggedin, value=value)

@app.route('/history/query<int:query_id>')
def query_history(query_id):
    message1 = ''
    message2 = ''
    message3 = ''
    message4 = ''
    global loggedin
    checkquery = Query.query.filter_by(query_id=query_id).first()
    if checkquery.queryusr == loggedin or loggedin == 'admin':
        message1 = str(query_id)
        message2 = str(checkquery.queryusr)
        message3 = str(checkquery.querytxt)
        message4 = str(checkquery.misspell)
    return render_template('queryhistory.html', message1=message1, message2=message2, message3=message3, message4=message4)

@app.route('/login_history',  methods=['post', 'get'])
def login_history():
    value=random.randrange(1,100)
    message1 = []
    message2 = []
    message3 = []
    global loggedin
    if request.method == 'POST':
        inputtext = request.form.get('inputtext')
        if loggedin == 'admin' and inputtext:
            checklogin = Login.query.filter_by(loginusr=str(inputtext)).all()
            for eachlogin in checklogin:
                message1.append(str(eachlogin.login_id))
                message2.append(str(eachlogin.logitime))
                message3.append(str(eachlogin.logotime))
    zipped = zip(message1, message2, message3)
    return render_template('loginhistory.html', message1=zipped, value= value, user=loggedin)
