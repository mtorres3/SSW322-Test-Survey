import os
from flask import Flask, render_template, request, session, redirect, url_for, g, abort, jsonify, flash

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
#print(ref.document('test').collection('Tests').document('fuck this').get().to_dict()['Name'])
#print(ref.document('test').collection('Tests').document('fuck this').get().to_dict()['Questions']['question01'])
#print(ref.document('test').collection('Tests').document('fuck this').get().to_dict()['question1']['answers'])
#print(ref.document('test').collection('Tests').document('fuck this').get().to_dict()['Questions']['question01']['question'])
#length = (len(ref.document('test').collection('Tests').document('fuck this').get().to_dict()['Questions']))
#get all of the questions values from from Question array
#counter = 1
#questionArray = []
#for n in range (1, length + 1):
 #   string = "question0" + str(counter)
  #  if(counter >= 10):
   #     string = "question" + str(counter)
    #print(ref.document('test').collection('Tests').document('fuck this').get().to_dict()['Questions'][string])
    #print(ref.document('test').collection('Tests').document('fuck this').get().to_dict()['Questions'][string]['answers'])
    #print(string)
    #print(ref.document('test').collection('Tests').document('fuck this').get().to_dict()['Questions'][string]['question'])
    #counter = counter + 1
    #questionArray.append(ref.document('test').collection('Tests').document('fuck this').get().to_dict()['Questions'][string]['question'])
    
#print(questionArray)

@app.before_request
def before_request():

    redefine()
    g.user = None

    if 'user_id' in session:
        user = [x for x in users if x.username == session['user_id']]
        g.user = user


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

    curr = ref.document(session['user_id']).collection('Surveys').document(session['survey_name'])
    try:
        amount_of_questions = curr.get().to_dict()['Questions']
    except KeyError:
        amount_of_questions = []

    if request.method == "GET":
        return render_template('survey_creation.html', questionType="text", questionClass="multiple-choice", my_list=['A','B','C','D'], 
            qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True, amount_of_questions = amount_of_questions)
    elif request.method == 'POST':
        qType = request.form.get('question-type')
        if qType == 'multiple-choice':
            return render_template('survey_creation.html', questionType="text", questionClass="multiple-choice", my_list=['A', 'B', 'C', 'D'], 
            qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True, amount_of_questions = amount_of_questions)
        
        elif qType == 'true-false':
            return render_template('survey_creation.html', questionType="radio", questionClass="true-false", my_list=['True', 'False'], 
            correctAnswer='correct-answer', qSubmit="question-submit-2", cSubmit='creation-submit-2', amount_of_questions = amount_of_questions)
        
        elif qType == 'short-answer':
            return render_template('survey_creation.html', questionType="text", questionClass="short-answer", my_list=[], 
            qSubmit="question-submit-3", cSubmit='creation-submit-3', amount_of_questions = amount_of_questions)
        
        if request.form['submit'] == 'next-question':

            info = request.form
            answers = []

            for i in ['A', 'B', 'C', 'D']:
                try:
                    if len(info[i]) > 0:
                        answers = answers + [info[i]]
                except KeyError:
                    break
            ''' 
            try:
                if info['answers'] in ['True', 'False']:
                    answers = info['answers']
            except KeyError:
                pass
            '''
            try:
                question_num = str(len(amount_of_questions) + 1)
                if len(question_num) == 1:
                    question_num = '0' + question_num

                curr.set({
                    'Questions': {
                        'question' + question_num: {
                            'question' : info['question'],
                            'answers' : answers,
                        }
                    }
                }, merge = True)

            except KeyError:
                pass
            return redirect(url_for('survey_creation'))

        if request.form['submit'] == 'save-survey':
            return redirect(url_for('create_or_open'))


@app.route('/survey_or_test')
def survey_or_test():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('survey_or_test.html')

@app.route('/new_test', methods=['GET','POST'])
def new_test():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        session['test_name'] = name
        ref.document(session['user_id']).collection('Tests').document(session['test_name']).set(
            {
                'Name' : name
            })
        return(redirect(url_for('test_creation')))

    return render_template('new_test.html')

@app.route('/new_survey', methods = ['GET', 'POST'])
def new_survey():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        session['survey_name'] = name
        ref.document(session['user_id']).collection('Surveys').document(session['survey_name']).set(
            {
                'Name' : name
            })
        return(redirect(url_for('survey_creation')))

    return render_template('new_survey.html')

@app.route('/test_creation', methods=['GET','POST'])
def test_creation():
    if not g.user:
        return redirect(url_for('login'))

    curr = ref.document(session['user_id']).collection('Tests').document(session['test_name'])
    try:
        amount_of_questions = curr.get().to_dict()['Questions']
    except KeyError:
        amount_of_questions = []
    
    if request.method == "GET":
        return render_template('test_creation.html', questionType="text", questionClass="multiple-choice", my_list=['A', 'B', 'C', 'D'], 
        qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True, amount_of_questions = amount_of_questions)

    elif request.method == 'POST':  
        qType = request.form.get('question-type')
        if qType == 'multiple-choice':
            return render_template('test_creation.html', questionType="text", questionClass="multiple-choice", my_list=['A', 'B', 'C', 'D'], 
            qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True, amount_of_questions = amount_of_questions)
        elif qType == 'true-false':
            return render_template('test_creation.html', questionType="radio", questionClass="true-false", my_list=['True', 'False'], 
            correctAnswer='correct-answer', qSubmit="question-submit-2", cSubmit='creation-submit-2', amount_of_questions = amount_of_questions)
        elif qType == 'short-answer':
            return render_template('test_creation.html', questionType="text", questionClass="short-answer", my_list=[], 
            qSubmit="question-submit-3", cSubmit='creation-submit-3', amount_of_questions = amount_of_questions)

        if request.form['submit'] == 'next-question':

            info = request.form
            answers = []

            for i in ['A', 'B', 'C', 'D']:
                try:
                    if len(info[i]) > 0:
                        answers = answers + [info[i]]
                except KeyError:
                    break
            
            try:
                question_num = str(len(amount_of_questions) + 1)
                if len(question_num) == 1:
                    question_num = '0' + question_num

                try:
                    c_answer = info['correct-answer']
                except KeyError:
                    c_answer = []

                curr.set({
                    'Questions': {
                        'question' + question_num: {
                            'question' : info['question'],
                            'answers' : answers,
                            'correct_answer' : c_answer
                        }
                    }
                }, merge = True)

            except KeyError:
                pass
            return redirect(url_for('test_creation'))

        if request.form['submit'] == 'save-test':
            return redirect(url_for('create_or_open'))

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

@app.route('/test_list', methods=['GET', 'POST'])
def test_list():
    if not g.user:
        return redirect(url_for('login'))
    if request.method == 'GET':
        testListings = [] 
        tests = ref.document(session['user_id']).collection('Tests').stream()
        for test in tests:
            testListings.append(f'{test.id}')
        print(testListings)
        return render_template('test_list.html', testListings = testListings)
    elif request.method == "POST":
        print(request.form.get('test-list'))
        session['test-name'] = request.form.get('test-list')
        return redirect(url_for('test_open')) 

@app.route('/survey_list', methods=['GET', 'POST'])
def survey_list():
    if not g.user:
        return redirect(url_for('login'))
    if request.method == 'GET':
        surveyListings = [] 
        surveys = ref.document(session['user_id']).collection('Surveys').stream()
        for survey in surveys:
            surveyListings.append(f'{survey.id}')
        print(surveyListings)
        return render_template('survey_list.html', surveyListings = surveyListings)
    elif request.method == "POST":
        print(request.form.get('survey-list'))
        session['survey-name'] = request.form.get('survey-list')
        return redirect(url_for('survey_open')) 
    return render_template('survey_list.html')


@app.route('/test_open', methods=['GET','POST'])
def test_open():
    if not g.user:
        return redirect(url_for('login'))
    
    testName = session.get('test-name') #receive test Name from Test_List
    print(testName)
    print(type(testName))
    #testName = ref.document(session['user_id']).collection('Tests').document('fuck this').get().to_dict()['Name']#Test Name
    length = (len(ref.document(session['user_id']).collection('Tests').document(testName).get().to_dict()['Questions'])) #amt of questions
    counter = 1
    questionArray = []
    for counter in range (1, length + 1):
        string = "question0" + str(counter)
        if(counter >= 10):
            string = "question" + str(counter)
        counter = counter + 1
        questionArray.append(ref.document(session['user_id']).collection('Tests').document(testName).get().to_dict()['Questions'][string]['question'])
    print(questionArray)


    if request.method == 'GET':
        question = ref.document(session['user_id']).collection('Tests').document(testName).get().to_dict()['Questions']['question01']['question']
        answers = ref.document(session['user_id']).collection('Tests').document(testName).get().to_dict()['Questions']['question01']['answers']
        correct = ref.document(session['user_id']).collection('Tests').document(testName).get().to_dict()['Questions']['question01']['correct_answer']
        answerLength = len(answers)
        return render_template('test_open.html', Name = testName, question = question, 
        answers = answers, question_amount = length, answerLength = answerLength, 
        questionArray = questionArray, correct = correct)

    elif request.method == 'POST':
        #get question0# or question# from button
        number = int(request.form.get('submit')) 
        if(number >= 10):
            string = "question" + str(number)
        string = "question0" + str(number)
        #print(question)
        #print(answers) 
        question = ref.document(session['user_id']).collection('Tests').document(testName).get().to_dict()['Questions'][string]['question']
        answers = ref.document(session['user_id']).collection('Tests').document(testName).get().to_dict()['Questions'][string]['answers']
        correct = ref.document(session['user_id']).collection('Tests').document(testName).get().to_dict()['Questions'][string]['correct_answer']
        answerLength = len(answers)
        #print(request.form.get('submit-test'))
        #print(request.form.get('submit'))
        return render_template('test_open.html', Name = testName, question = question,
        answers = answers, question_amount = length, answerLength = answerLength,
        questionArray = questionArray, correct = correct)



@app.route('/survey_open', methods=['GET','POST'])
def survey_open():
    if not g.user:
        return redirect(url_for('login'))

    surveyName = session.get('survey-name') #receive survey Name from Survey_List
    #print(surveyName)
    #print(type(surveyName))
    length = (len(ref.document(session['user_id']).collection('Surveys').document(surveyName).get().to_dict()['Questions'])) #amt of questions
    counter = 1
    questionArray = []
    for counter in range (1, length + 1):
        string = "question0" + str(counter)
        if(counter >= 10):
            string = "question" + str(counter)
        counter = counter + 1
        questionArray.append(ref.document(session['user_id']).collection('Surveys').document(surveyName).get().to_dict()['Questions'][string]['question'])
    #print(questionArray)


    if request.method == 'GET':
        question = ref.document(session['user_id']).collection('Surveys').document(surveyName).get().to_dict()['Questions']['question01']['question']
        answers = ref.document(session['user_id']).collection('Surveys').document(surveyName).get().to_dict()['Questions']['question01']['answers']
        answerLength = len(answers)
        return render_template('survey_open.html', Name = surveyName, question = question, 
        answers = answers, question_amount = length, answerLength = answerLength, 
        questionArray = questionArray)

    elif request.method == 'POST':
        #get question0# or question# from button
        number = int(request.form.get('submit')) 
        if(number >= 10):
            string = "question" + str(number)
        string = "question0" + str(number)
        #print(question)
        #print(answers) 
        question = ref.document(session['user_id']).collection('Surveys').document(surveyName).get().to_dict()['Questions'][string]['question']
        answers = ref.document(session['user_id']).collection('Surveys').document(surveyName).get().to_dict()['Questions'][string]['answers']
        answerLength = len(answers)
        #print(request.form.get('submit-survey'))
        #print(request.form.get('submit'))
        return render_template('survey_open.html', Name = surveyName, question = question,
        answers = answers, question_amount = length, answerLength = answerLength,
        questionArray = questionArray)
    #surveyName = ref.document(session['user_id']).collection('Surveys').document('NameOfDocumentGoesHere').get().to_dict()['Name']#collection of Tests
    #surveyQuestions = ref.document('test').collection('Surveys').document('NameOfDocumentGoesHere').get().to_dict()['Questions']['question01']['question']
    return render_template('survey_open.html') # Name = surveyName


if __name__ == "__main__":
    app.run(port=5017, debug=True)
