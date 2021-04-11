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

@app.route('/survey_creation', methods=['GET','POST'])
def survey_creation():
    if not g.user:
        return redirect(url_for('login')) 

    if request.method == "GET":
        return render_template('survey_creation.html', qSubmit="question-submit-0", cSubmit='creation-submit-0')

    elif request.method == 'POST':
        qType = request.form.get('question-type')
        if qType == 'multiple-choice':
            return render_template('survey_creation.html', questionType="text", questionClass="multiple-choice", my_list=[1,2,3,4], 
            qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True)
        elif qType == 'true-false':
            return render_template('survey_creation.html', questionType="radio", questionClass="true-false", my_list=[1,2], 
            correctAnswer='correct-answer', qSubmit="question-submit-2", cSubmit='creation-submit-2')
        elif qType == 'short-answer':
            return render_template('survey_creation.html', questionType="text", questionClass="short-answer", my_list=[1], 
            qSubmit="question-submit-3", cSubmit='creation-submit-3')

@app.route('/survey_or_test')
def survey_or_test():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('survey_or_test.html')

@app.route('/test_creation', methods=['GET','POST'])
def test_creation():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == "GET":
        return render_template('test_creation.html', qSubmit="question-submit-0", cSubmit='creation-submit-0')

    elif request.method == 'POST':
        qType = request.form.get('question-type')
        if qType == 'multiple-choice':
            return render_template('test_creation.html', questionType="text", questionClass="multiple-choice", my_list=[1,2,3,4], 
            qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True)
        elif qType == 'true-false':
            return render_template('test_creation.html', questionType="radio", questionClass="true-false", my_list=[1,2], 
            correctAnswer='correct-answer', qSubmit="question-submit-2", cSubmit='creation-submit-2')
        elif qType == 'short-answer':
            return render_template('test_creation.html', questionType="text", questionClass="short-answer", my_list=[1], 
            qSubmit="question-submit-3", cSubmit='creation-submit-3')
         

#Still being Developed
#Trying to save question and answer choices to database
# def question_saved():
#     Firebase.firestore().collection("Tests/".get())
    
# #Needs: User Reference, allowing for placing | Unique ID for 
#     if not g.user:
#         return redirect(url_for('login'))
#     else request.method == 'POST':
#         q_type = request.form['question-type-form']
#         q = request.form['question']
#         a = request.form['choice-a']
#         b = request.form['choice-b']
#         c = request.form['choice-c']
#         d = request.form['choice-d']

#         ref.document(question).set({
#             'type': q_type,
#             'question': q,
#             'choice-a': a,
#             'choice-b': b,
#             'choice-c': c,
#             'choice-d': d
#         })
#         return render_template('test_creation.html')

def submit_test_creation():
    text = request.form['choice-a']
    processed_text = text.upper()
    return processed_text

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
    app.run(port=5047, debug=True)
