import os
from flask import Flask, render_template, request, session, redirect, url_for, g, abort, jsonify

app = Flask(__name__)
app.secret_key = 'okay'

import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
ref = db.collection('Users')

global users, usernames

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User: {self.username}>'

# Redefines list of users
def redefine():

    global users, usernames
    ref = db.collection('Users')
    stream = ref.stream()
    users = []
    usernames = []

    for i in stream:
        users = users + [User(i.to_dict()['username'], i.to_dict()['password'])]
        usernames = usernames + [i.to_dict()['username']]

redefine()
print(usernames)

@app.before_request
def before_request():

    redefine()
    g.user = None

    if 'user_id' in session:
        user = [x for x in users if x.username == session['user_id']]
        g.user = user
        print(g.user)


@app.route('/list_all_user_data/<user>', methods = ['GET', 'POST'])
def list(user) :

    ref = db.collection('Users')
    ref = ref.where(u'username', u'==', user)

    try:
        # Check if ID was passed to URL query
        todo_id = request.args.get('ID')

        if todo_id:
            todo = ref.document(todo_id).get()
            return jsonify(todo.to_dict()), 200
        else:
            all_todos = [doc.to_dict() for doc in ref.stream()]
            return jsonify(all_todos), 200

    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/', methods = ['GET', 'POST'])
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':

        redefine()
        session.pop('user_id', None)
        username = request.form['username']
        password = request.form['password']

        try:
            user = [x for x in users if x.username == username][0]
        except IndexError:
            return redirect(url_for('login'))

        if user and user.password == password:
            session['user_id'] = user.username
            return redirect(url_for('taker_or_creator'))

        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        redefine()
        username = request.form['username']
        password = request.form['password']

        if username in usernames:
            return redirect(url_for('register'))
        else:
            ref.document(username).set({
                'username': username,
                'password': password
            })

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/taker_or_creator', methods=['GET','POST'])
def taker_or_creator():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('taker_or_creator.html')

@app.route('/create_or_open')
def create_or_open():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('create_or_open.html')

@app.route('/survey_creation')
def survey_creation():
    if not g.user:
        return redirect(url_for('login'))    
    return render_template('survey_creation.html')

@app.route('/survey_or_test')
def survey_or_test():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('survey_or_test.html')

@app.route('/test_creation')
def test_creation():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('test_creation.html')

@app.route('/upload_or_grade')
def upload_or_grade():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('upload_or_grade.html')

@app.route('/open_file')
def open_file():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('open_file.html')

@app.route('/test_open')
def test_open():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('test_open.html')

@app.route('/survey-open')
def survey_open():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('survey-open.html')



if __name__ == "__main__":
    app.run(port=5029, debug=True)
