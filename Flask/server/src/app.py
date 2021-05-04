'''
Authors: Jon Cucci, Joe Letizia, Markell Torres, Will Baltus
Started on: March 28th 2021
'''

# Assorted imports
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()
SALT = os.getenv('SALT')

# Flask frameworking
from flask import Flask, render_template, request, session, redirect, url_for, g, abort, jsonify, flash

app = Flask(__name__)
app.secret_key = 'okay'

# Fire Store and databasing
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
ref = db.collection('Users')

# DB Query Documentation
'''
Small changes to the code below will get you everything you need

ref.document(session['user_id']).collection('Surveys').document(session['survey_name']).get().to_dict()
'''

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
        password = hashlib.sha256((password+SALT).encode()).hexdigest()

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
        hashed_password = hashlib.sha256((password+SALT).encode())

        if username in usernames:
            return redirect(url_for('register'))
        else:
            ref.document(username).set({
                'username': username,
                'password': hashed_password.hexdigest()
            })

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/taker_or_creator', methods=['GET','POST'])
def taker_or_creator():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('taker_or_creator.html')

#For Taker
@app.route('/take_survey_or_test')
def take_survey_or_test():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('take_survey_or_test.html')

############################## GOTTA GET DONE STILL #############################

@app.route('/taker_test_select',  methods=['GET','POST'])
def taker_test_select():

    if not g.user:
        return redirect(url_for('login'))

    #TODO: Display tests in dropdown 
    if request.method == 'GET':

        testListings = [] 
        tests = ref.document(session['user_id']).collection('Tests').stream()
        test_counter = 0

        for test in tests:
            test_counter = test_counter + 1
            testListings.append(f'{test.id}') 
        #print(testListings)

        if(test_counter > 0):
            return render_template('taker_test_select.html', testListings = testListings)
        else:
            return render_template('taker_no_test_survey.html')

    elif request.method == "POST":
        #print(request.form.get('test-list'))
        session['test-name'] = request.form.get('test-list')
        print("This is the get request " + request.form.get('test-list').items())
        return redirect(url_for('take_test')) 

    return render_template('taker_test_select.html')

@app.route('/take_test')
def take_test():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Display test info
    return render_template('take_test.html')

@app.route('/taker_survey_select', methods=['GET','POST'])
def taker_survey_select():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Display surveys in dropdown
    ##################################### USELESS BC NO DROP DOWN ANYMORE, But I feel bad to delete #######################
    if request.method == 'GET':

        surveyListings = [] 
        surveys = ref.document(session['user_id']).collection('Surveys').stream()
        test_counter = 0

        for survey in surveys:
            test_counter = test_counter + 1
            surveyListings.append(f'{survey.id}')

        if(test_counter > 0): 
            return render_template('taker_survey_select.html', surveyListings = surveyListings)
        else:
            return render_template('no_test_survey.html')
    ######################################################################################################      
    elif request.method == "POST":
        
        #TODO: Display survey info
        the_survey = request.form.get('survey-lookup')
        #### PASS DATA TO TAKE_SURVEY
        session['survey_name_ID'] = the_survey
        #print(the_survey)
        
        return redirect(url_for('take_survey'))

@app.route('/take_survey', methods=['GET', 'POST'])
def take_survey():
    if not g.user:
        return redirect(url_for('login'))

    survey_name_ID = session.get('survey_name_ID') #receive survey (type: str) search form data
    s = survey_name_ID.split("-")
    surveys = ref.document(s[0]).collection('Surveys').stream()
    info = {}
    #testing split method, separates string and deletes split token
    #print("0th " + s[0])
    #print("1st " + s[1])
    for survey in surveys:
        if s[1] == survey.to_dict()['ID']:
            info = survey.to_dict()
            print(info)
    else:
        print("Invalid ID: " + survey.to_dict()['ID'])

    Qmap= info['Questions'] #get questions of the survey
    length = len(Qmap) #amt of questions
    #print(length)
    counter = 1
    questionArray = []
    for counter in range (1, length + 1):
        string = "question0" + str(counter)
        if(counter >= 10):
            string = "question" + str(counter)
        counter = counter + 1
        questionArray.append(Qmap[string]['question'])

    #print(questionArray)
    if request.method == 'GET':
        question = Qmap['question01']['question']
        answers = Qmap['question01']['answers']
        correct = Qmap['question01']['correct_answer']
        answerLength = len(answers)
        name = info['Name']
        questionType = Qmap[string]['question_type']
        
        return render_template(('take_survey.html'), surveyName = name, surveyQuestion = question, 
            answers = answers, question_amount = length, answerLength = answerLength, 
            questionArray = questionArray, correct = correct, questionType = questionType) 

    elif request.method == 'POST':
        #get question0# or question# from buttons on left
        number = int(request.form.get('submit'))
        if (number <= 10): 
            string = "question0" + str(number)
        if(number >= 10):
            string = "question" + str(number)

        questionName = Qmap[string]['question']
        answers = Qmap[string]['answers']
        correct = Qmap[string]['correct_answer']
        name = info['Name']
        answerLength = len(answers)
        questionType = Qmap[string]['question_type']

        return render_template('test_open.html', surveyName = name, surveyQuestion = questionName,
        answers = answers, question_amount = length, answerLength = answerLength,
        questionArray = questionArray, correct = correct, questionType = questionType)

    return render_template('take_survey.html')

##################################################################################

#For Creator
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
        session['question_type'] = 'multiple-choice'
        return render_template('survey_creation.html', questionType="text", questionClass="multiple-choice", my_list=['A','B','C','D'], 
        qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True, amount_of_questions = amount_of_questions)
    
    elif request.method == 'POST':

        qType = request.form.get('question-type')

        if qType == 'multiple-choice':
            session['question_type'] = 'multiple-choice'
            return render_template('survey_creation.html', questionType="text", questionClass="multiple-choice", my_list=['A', 'B', 'C', 'D'], 
            qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True, amount_of_questions = amount_of_questions)
        
        elif qType == 'true-false':
            session['question_type'] = 'true-false'
            return render_template('survey_creation.html', questionType="radio", questionClass="true-false", my_list=['True', 'False'], 
            correctAnswer='correct-answer', qSubmit="question-submit-2", cSubmit='creation-submit-2', amount_of_questions = amount_of_questions)
        
        elif qType == 'short-answer':
            session['question_type'] = 'short-answer'
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
                            'question_type' : session['question_type'],
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
                'Name' : name,
                'ID' : str(len(ref.document(session['user_id']).collection('Tests').get()) + 1)
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
                'Name' : name,
                'ID' : str(len(ref.document(session['user_id']).collection('Surveys').get()) + 1)
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
        session['question_type'] = 'multiple-choice'
        return render_template('test_creation.html', questionType="text", questionClass="multiple-choice", my_list=['A', 'B', 'C', 'D'],
        qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True, amount_of_questions = amount_of_questions)

    elif request.method == 'POST':

        qType = request.form.get('question-type')

        if qType == 'multiple-choice':
            session['question_type'] = 'multiple-choice'
            return render_template('test_creation.html', questionType="text", questionClass="multiple-choice", my_list=['A', 'B', 'C', 'D'],
            qSubmit="question-submit-1", cSubmit='creation-submit-1', radioChoices=True, amount_of_questions = amount_of_questions)
        
        elif qType == 'true-false':
            session['question_type'] = 'true-false'
            return render_template('test_creation.html', questionType="radio", questionClass="true-false", my_list=['True', 'False'],
            correctAnswer='correct-answer', qSubmit="question-submit-2", cSubmit='creation-submit-2', amount_of_questions = amount_of_questions)
        
        elif qType == 'short-answer':
            session['question_type'] = 'short-answer'
            return render_template('test_creation.html', questionType="text", questionClass="short-answer", my_list=[],
            qSubmit="question-submit-3", cSubmit='creation-submit-3', amount_of_questions = amount_of_questions)

        # same things for essay, rank and match


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
                            'question_type' : session['question_type'],
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

@app.route('/grade_test_or_survey')
def grade_test_or_survey():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('grade_test_or_survey.html')

#################################### TODO STILL #########################################
@app.route('/grade_test_select')
def grade_test_select():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Get Test ID to open
    return render_template('grade_test_select.html')

@app.route('/taker_selection_for_grading')
def taker_selection_for_grading():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Get user ID for grading
    return render_template('taker_selection_for_grading.html')

@app.route('/view_grade')
def view_grade():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Give data for user's so creator can grade it
    return render_template('view_grade.html')

@app.route('/tabulate_survey_select')
def tabulate_survey_select():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Get Survey ID to open
    return render_template('tabulate_survey_select.html')

@app.route('/survey_tabulation')
def survey_tabulation():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Give data for top/avg answers for each question
    return render_template('survey_tabulation.html')
#########################################################################################

@app.route('/open_file')
def open_file():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('open_file.html')

#edge case route
@app.route('/no_test_survey')
def no_test_survey():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('no_test_survey.html')

@app.route('/test_list', methods=['GET', 'POST'])
def test_list():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'GET':

        testListings = [] 
        tests = ref.document(session['user_id']).collection('Tests').stream()
        test_counter = 0

        for test in tests:
            test_counter = test_counter + 1
            testListings.append(f'{test.id}') 

        if(test_counter > 0):
            return render_template('test_list.html', testListings = testListings)
        else:
            return render_template('no_test_survey.html')

    elif request.method == "POST":

        session['test-name'] = request.form.get('test-list')
        #print("This is the get request " + request.form.get('test-list').items())

        return redirect(url_for('test_open')) 

@app.route('/test_open', methods=['GET','POST'])
def test_open():

    if not g.user:
        return redirect(url_for('login'))

    testName = session.get('test-name') #receive test Name from Test_List
    curr_ref = ref.document(session['user_id']).collection('Tests').document(testName).get().to_dict()['Questions']
    length = len(curr_ref) #amt of questions
    
    counter = 1
    questionArray = []

    for counter in range (1, length + 1):

        string = "question0" + str(counter)

        if(counter >= 10):
            string = "question" + str(counter)

        counter = counter + 1
        questionArray.append(curr_ref[string]['question'])

    print(questionArray)


    if request.method == 'GET':

        session['question_num'] = 'question01'
        session['question'] = curr_ref['question01']['question']
        session['answers'] = curr_ref['question01']['answers']
        session['correct'] = curr_ref['question01']['correct_answer']
        session['answerLength'] = len(session['answers'])

        return render_template('test_open.html', Name = testName, question = session['question'], 
        answers = session['answers'], question_amount = length, answerLength = session['answerLength'], 
        questionArray = questionArray, correct = session['correct'] )

    elif request.method == 'POST':

        info = request.form
        print(info)

        if 'question' in request.form['submit']:

            number = int(request.form['submit'].split('n')[1])

            if(number >= 10):
                string = "question" + str(number)
            else:
                string = "question0" + str(number)

            session['question_num'] = string
            session['question'] = curr_ref[string]['question']
            session['answers'] = curr_ref[string]['answers']
            session['correct'] = curr_ref[string]['correct_answer']
            session['answerLength'] = len(session['answers'])

            return render_template('test_open.html', Name = testName, question = session['question'], 
            answers = session['answers'], question_amount = length, answerLength = session['answerLength'], 
            questionArray = questionArray, correct = session['correct'] )

        elif request.form['submit'] == 'modify-submit':

            info = request.form
            print(info)

            # Getting new answers
            answers = []
            for num in range(1, len(session['answers'])+1):
                answers.append(info['q' + str(num)])

            num_to_let = {'1' : 'A',
                        '2' : 'B',
                        '3' : 'C', 
                        '4' : 'D'}

            ref.document(session['user_id']).collection('Tests').document(testName).update({
                        u'Questions.{}.answers'.format(session['question_num']) : answers,
                        u'Questions.{}.correct_answer'.format(session['question_num']) : num_to_let[info['correct-answer-display']]
            })

            session['answers'] = answers
            session['correct'] = num_to_let[info['correct-answer-display']]

            return render_template('test_open.html', Name = testName, question = session['question'], 
            answers = session['answers'], question_amount = length, answerLength = session['answerLength'], 
            questionArray = questionArray, correct = session['correct'] )




@app.route('/survey_list', methods=['GET', 'POST'])
def survey_list():

    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'GET':

        surveyListings = [] 
        surveys = ref.document(session['user_id']).collection('Surveys').stream()
        test_counter = 0

        for survey in surveys:
            test_counter = test_counter + 1
            surveyListings.append(f'{survey.id}')

        if(test_counter > 0): 
            return render_template('survey_list.html', surveyListings = surveyListings)

        else:
            return render_template('no_test_survey.html')
        
    elif request.method == "POST":

        print(request.form.get('survey-list'))
        session['survey-name'] = request.form.get('survey-list')
        return redirect(url_for('survey_open')) 

    return render_template('survey_list.html')

@app.route('/survey_open', methods=['GET','POST'])
def survey_open():

    if not g.user:
        return redirect(url_for('login'))

    surveyName = session.get('survey-name') #receive survey Name from Survey_List
    curr_ref = ref.document(session['user_id']).collection('Surveys').document(surveyName).get().to_dict()['Questions']
    length = len(curr_ref) #amt of questions
    counter = 1
    questionArray = []

    for counter in range (1, length + 1):

        string = "question0" + str(counter)

        if(counter >= 10):
            string = "question" + str(counter)

        counter = counter + 1
        questionArray.append(curr_ref[string]['question'])

    if request.method == 'GET':

        question = curr_ref['question01']['question']
        answers = curr_ref['question01']['answers']
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
        question = curr_ref[string]['question']
        answers = curr_ref[string]['answers']
        answerLength = len(answers)

        return render_template('survey_open.html', Name = surveyName, question = question,
        answers = answers, question_amount = length, answerLength = answerLength,
        questionArray = questionArray)
    
    elif request.method == 'PUT':
        print(request.form.get('question'))
        
        # curr_ref.set({
        #              'Questions': {
        #                  'question' + question_num: {
        #                      'question_type' : session['question_type'],
        #                      'question' : info['question'],
        #                     'answers' : answers,
        #                      'correct_answer' : c_answer
        #                  }
        #              }
        #          })


        return render_template('survey_open.html', Name = surveyName, question = question,
        answers = answers, question_amount = length, answerLength = answerLength,
        questionArray = questionArray)






    return render_template('survey_open.html') # Name = surveyName

# surveys = ref.document("test").collection("Surveys").stream()
# for survey in surveys:
#     if survey.to_dict()["ID"] == "1":
#         # print(survey.to_dict())

if __name__ == "__main__":
    app.run(port=5033, debug=True)
