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

#########################################For Taker#################################################
@app.route('/take_survey_or_test')
def take_survey_or_test():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('take_survey_or_test.html')

@app.route('/taker_test_select',  methods=['GET','POST'])
def taker_test_select():
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
            return render_template('taker_test_select.html', testListings = testListings)
        else:
            return render_template('no_test_survey.html')
       
    elif request.method == "POST":
        the_test = request.form.get('test-lookup')
        #### PASS DATA TO TAKE TEST
        session['test_name_ID'] = the_test
        firstTake = 1
        session['firstTake'] = firstTake
        #print(the_survey)
        return redirect(url_for('take_test'))

@app.route('/take_test', methods = ['GET', 'POST'])
def take_test():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Display test info
    test_name_ID = session.get('test_name_ID') #receive test (type: str) search form data
    firstTake = session.get('firstTake') 
    testName = ' '
    testID = ' '
    t = test_name_ID.split("-")
    tests = ref.document(t[0]).collection('Tests').stream()
    info = {}

    for test in tests:
        if t[1] == test.to_dict()['ID']:
            testID = test.to_dict()['ID']
            print("testID: " + testID)
            info = test.to_dict()
            testName = test.to_dict()['Name']
            #print(info)
            #print(testName)

    #Build question array. Code gets all question names from question map from database
    Qmap= info['Questions'] #get questions map of the test
    length = len(Qmap) #amt of questions
    counter = 1
    questionArray = []
    for counter in range (1, length + 1):
        string = "question0" + str(counter)
        if(counter >= 10):
            string = "question" + str(counter)
        counter = counter + 1
        questionArray.append(Qmap[string]['question'])
    #end array build

    ##REFERENCE FOR POSTING DATA TO DB
    user_name = session['user_id']
    curr_ref = ref.document(t[0]).collection('Tests').document(testName).collection('Takers').document(user_name)


    #Default, on load, show first question
    if request.method == 'GET':
        print("GET ACTIVATED!")
        question = Qmap['question01']['question']
        answers = Qmap['question01']['answers']
        #correct = Qmap['question01']['correct_answer']
        answerLength = len(answers)
        name = info['Name']
        questionType = Qmap['question01']['question_type']
        
        return render_template(('take_test.html'), testName = name, testQuestion = question, 
            answers = answers, question_amount = length, answerLength = answerLength, 
            questionArray = questionArray,  questionType = questionType, Qstring = string,
            nextQuestionNumber= 2, testLength = int(length)) 

    #any posts, such as next question, code executes this 
    elif request.method == 'POST':
        print("POST ACTIVATED")
        #when user first opens test, the 'next question' should bring up the second question.
        if(len(str(request.form['submit'])) > 3 and firstTake == 1):

            #Acquire necessary data for Db to push question01
            questionFirst = 'question01'
            answersF = Qmap[questionFirst]['answers'] #return array of strings containing answers
            questionF = Qmap[questionFirst]['question']
            correctF = Qmap[questionFirst]['correct_answer']
            correctString = ' '

            #### multiple-choice form request and points calculation ####
            chosen = request.form['radio']

            #find the correct answer string
            if(correctF == 'A' ):
                correctString = answersF[0]
            elif(correctF == 'B' ):
                correctString = answersF[1]
            elif(correctF == 'C' ):
                correctString = answersF[2]
            elif(correctF == 'D' ):
                correctString = answersF[3]

            if(chosen == correctString):
                points = 1
            else:
                points = 0            
            #### end request and calculation ####

            #Push these to Db
            curr_ref.set({
                'Questions': {
                    questionFirst: {
                        'Question': questionF,
                        'answer': chosen,
                        'correct_answer': correctString,
                        'points': points,
                    }
                }
            }, merge = True)

            #Acquire necessary data for template and for next question to show
            print("Next Question was clicked for the first time. ")        
            Qstring = 'question02'
            question = Qmap[Qstring]['question']
            answers = Qmap[Qstring]['answers'] #return array of strings containing answers
            name = info['Name']
            answerLength = len(answers)
            questionType = Qmap[Qstring]['question_type'] 
            #correct = Qmap[Qstring]['correct_answer'] 
            session['firstTake'] = firstTake + 1 #increment so this isnt called again after first question



            return render_template('take_test.html', testName = name, testQuestion = question,
            answers = answers, question_amount = length, answerLength = answerLength,
            questionArray = questionArray,  questionType = questionType, Qstring = Qstring,
            nextQuestionNumber= 2, testLength = int(length))


        #check if 'submit' form is 'next-question' and if it is, then increment question # value and return all necessary values to template
        elif(len(str(request.form['submit'])) > 3):
            print("Next Question was clicked")

            stringSubmit = request.form['submit']
            substring = stringSubmit[8:] #remove 'question' from 'question##'
            number = int(substring) #current question number
            nextQuestion = number + 1

            #### multiple-choice form request and points calculation ####
            chosen = request.form['radio']
            currentQ = 'question0' + str(number) 
            if(number >= 10):
                    currentQ = 'question' + str(number)
            questionC = Qmap[currentQ]['question']
            correctC = Qmap[currentQ]['correct_answer']
            answersC = Qmap[currentQ]['answers']

            #find the correct answer string
            if(correctC == 'A' ):
                correctString = answersC[0]
            elif(correctC == 'B' ):
                correctString = answersC[1]
            elif(correctC == 'C' ):
                correctString = answersC[2]
            elif(correctC == 'D' ):
                correctString = answersC[3]
            elif(correctC == 'True' ):
                correctString = 'True'
            elif(correctC == 'False' ):
                correctString = 'False'

            if(chosen == correctString):
                points = 1
            else:
                points = 0            
            #### end request and calculation ####
            #Push these to Db
            curr_ref.set({
                'Questions': {
                    currentQ: {
                        'Question': questionC,
                        'answer': chosen,
                        'correct_answer': correctString,
                        'points': points,
                    }
                },
                'grade': 0,
                'username': session['user_id'],
            }, merge = True)

            curr_ref.get()

            #Get all necessary data for next question, while there is next question
            if (nextQuestion <= len(questionArray)):
                Qstring = 'question0' + str(nextQuestion)
                if(nextQuestion >= 10):
                    Qstring = 'question' + str(nextQuestion)
                question = Qmap[Qstring]['question']
                answers = Qmap[Qstring]['answers']
                #correct = Qmap[Qstring]['correct_answer']
                name = info['Name']
                answerLength = len(answers)
                questionType = Qmap[Qstring]['question_type'] 

                return render_template('take_test.html', testName = name, testQuestion = question,
                answers = answers, question_amount = length, answerLength = answerLength,
                questionArray = questionArray,  questionType = questionType, Qstring = Qstring,
                nextQuestionNumber= int(nextQuestion), testLength = int(length)) 
            else:
                print("COMPLETE")
                name = info['Name']
                return render_template('take_test.html', testName = name, ID = testID, 
                    userName = session['user_id'], questionArray = questionArray,
                    nextQuestionNumber= int(nextQuestion), testLength = int(length))

        #get question0# or question# from buttons on left
        elif isinstance(int(request.form['submit']),int): #is a digit, clicked on dark rectangle
            number = int(request.form.get('submit'))
            print(number)
            if (number <= 10): 
                Qstring = "question0" + str(number)
            if(number >= 10):
                Qstring = "question" + str(number)

            question = Qmap[Qstring]['question']
            answers = Qmap[Qstring]['answers']
            #correct = Qmap[Qstring]['correct_answer']
            name = info['Name']
            answerLength = len(answers)
            questionType = Qmap[Qstring]['question_type']  

            return render_template('take_test.html', testName = name, testQuestion = question,
            answers = answers, question_amount = length, answerLength = answerLength,
            questionArray = questionArray,  questionType = questionType, Qstring = Qstring,
            nextQuestionNumber = number, testLength = length)

    return render_template('take_test.html')

@app.route('/taker_survey_select',  methods=['GET','POST'])
def taker_survey_select():
    if not g.user:
        return redirect(url_for('login'))
   
    if request.method == 'GET':
        surveyListings = [] 
        surveys = ref.document(session['user_id']).collection('Surveys').stream()
        survey_counter = 0

        for survey in surveys:
            survey_counter = survey_counter + 1
            surveyListings.append(f'{survey.id}')

        if(survey_counter > 0): 
            return render_template('taker_survey_select.html', surveyListings = surveyListings)
        else:
            return render_template('no_test_survey.html')
       
    elif request.method == "POST":
        the_survey = request.form.get('survey-lookup')
        #### PASS DATA TO TAKE TEST
        session['survey_creator'] = the_survey.split('-')[0]
        session['survey_id'] = the_survey.split('-')[1]
        firstTake2 = 1
        session['firstTake2'] = firstTake2
        #print(the_survey)
        return redirect(url_for('take_survey'))

@app.route('/take_survey', methods = ['GET', 'POST'])
def take_survey():
    if not g.user:
        return redirect(url_for('login'))

    curr_ref = ref.document(session['survey_creator']).collection('Surveys')

    for stream in curr_ref.stream():
        if stream.to_dict()['ID'] == session['survey_id']:
            curr_ref = curr_ref.document(stream.to_dict()['Name'])
    
    if request.method == "GET":

        session['current_question'] = 'question01'

        try:
            curr_ref.collection('Answers').document('info').update({
                u'total_takers' : curr_ref.collection('Answers').document('info').get().to_dict()['total_takers'] + 1
            })
        except KeyError: 
            curr_ref.collection('Answers').document('info').update({
                u'total_takers' : 1
            })

    elif request.method == "POST":

        info = request.form
        answers = curr_ref.collection('Answers').document('info')

        if "question" in request.form.get('submit'):

            try:
                answers.update({
                    u'Questions.{}.{}.{}'.format(session['current_question'],'answers',info['answer']): answers.get().to_dict()['Questions'][session['current_question']]['answers'][info['answer']] + 1,
                    u'Questions.{}.{}'.format(session['current_question'],'question'): curr_ref.get().to_dict()['Questions'][session['current_question']]['question']
                    })

            except KeyError:
                answers.update({
                    u'Questions.{}.{}.{}'.format(session['current_question'],'answers',info['answer']): 1,
                    u'Questions.{}.{}'.format(session['current_question'],'question'): curr_ref.get().to_dict()['Questions'][session['current_question']]['question']
                    })

            new_q = int(session['current_question'].split('n')[1]) + 1
            if  new_q < 10:
                session['current_question'] = "question0" + str(new_q)
            else:
                session['current_question'] = "question" + str(new_q)

        else:

            if int(request.form.get('submit')) < 10:
                session['current_question'] = "question0" + request.form.get('submit')
            else:
                session['current_question'] = "question" + request.form.get('submit')

    if session['current_question'] not in curr_ref.get().to_dict()['Questions'].keys():
        return redirect(url_for('take_survey_or_test'))
    else:
        return render_template('take_survey.html', questionArray = curr_ref.get().to_dict(), survey_creator = session['survey_creator'], survey_id = session['survey_id'], current_question = session['current_question'])

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
@app.route('/grade_test_select', methods=['GET','POST'])
def grade_test_select():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Get Test ID to open
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

        return redirect(url_for('taker_selection_for_grading')) 

    return render_template('grade_test_select.html')

@app.route('/taker_selection_for_grading', methods=['GET','POST'])
def taker_selection_for_grading():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'GET':

        takerListings = [] 
        takers = ref.document(session['user_id']).collection('Tests').document(session['test-name']).collection('Takers').stream()
        taker_counter = 0

        for taker in takers:
            taker_counter += 1
            takerListings.append(taker.to_dict()['username']) 

        if(taker_counter > 0):
            return render_template('taker_selection_for_grading.html', takerListings = takerListings)
        else:
            return render_template('no_test_survey.html')

    elif request.method == "POST":

        session['taker-name'] = request.form.get('taker-list')
        return redirect(url_for('view_grade'))

    return render_template('taker_selection_for_grading.html')

@app.route('/view_grade', methods=['GET','POST'])
def view_grade():
    if not g.user:
        return redirect(url_for('login'))

    curr_ref = ref.document(session['user_id']).collection('Tests').document(session['test-name']).collection('Takers').document(session['taker-name'])
    gradedQuestions = curr_ref.get().to_dict()

    if request.method == "POST":

        info = request.form
        points = 0
        total = 0


        for num in range(1, len(gradedQuestions['Questions'])+1):

            points += int(info['p'+str(num)])
            total += 1

            if num < 10:
                string = "question0" + str(num)
            else:
                string = "question" + str(num)

            curr_ref.update({

                u'Questions.{}.points'.format(string) : info['p'+str(num)]

            })

        curr_ref.update({

            u'grade' : round((points / total) * 100, 2)

        })

    gradedQuestions = curr_ref.get().to_dict()
    return render_template('view_grade.html', test_name = session['test-name'], gradedQuestions = gradedQuestions, takerName = session['taker-name'])

@app.route('/tabulate_survey_select', methods=['GET','POST'])
def tabulate_survey_select():
    if not g.user:
        return redirect(url_for('login'))
    #TODO: Get Survey ID to open
    if request.method == 'GET':
    
        surveyListings = [] 
        surveys = ref.document(session['user_id']).collection('Surveys').stream()
        survey_counter = 0

        for survey in surveys:
            survey_counter = survey_counter + 1
            surveyListings.append(f'{survey.id}') 

        if(survey_counter > 0):
            return render_template('survey_list.html', surveyListings = surveyListings)
        else:
            return render_template('no_test_survey.html')

    elif request.method == "POST":

        session['survey-name'] = request.form.get('survey-list')
        #print("This is the get request " + request.form.get('survey-list').items())

        return redirect(url_for('survey_tabulation')) 

    return render_template('survey_tabulation.html')

@app.route('/survey_tabulation', methods=['GET','POST'])
def survey_tabulation():
    if not g.user:
        return redirect(url_for('login'))

    curr_ref = ref.document(session['user_id']).collection('Surveys').document(session['survey-name']).collection('Answers').document('info')
    surveyQuestions = curr_ref.get().to_dict()

    #TODO: Give data for top/avg answers for each question
    return render_template('survey_tabulation.html', survey_name = session['survey-name'], surveyQuestions = surveyQuestions)
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

        # return render_template('test_open.html', Name = testName, question = session['question'], 
        # answers = session['answers'], question_amount = length, answerLength = session['answerLength'], 
        # questionArray = questionArray, correct = session['correct'] )

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

            # return render_template('test_open.html', Name = testName, question = session['question'], 
            # answers = session['answers'], question_amount = length, answerLength = session['answerLength'], 
            # questionArray = questionArray, correct = session['correct'] )

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

            try:
                new_answer = num_to_let[info['correct-answer-display']]
                new_question = info['asked-question']
                print("printtttin")
            except KeyError:
                try:
                    print("bye")
                    new_answer = info['correct-answer-display']   
                except KeyError:
                    print("hello")
                    new_answer = ''
            new_question = info['asked-question']  

            ref.document(session['user_id']).collection('Tests').document(testName).update({
                        u'Questions.{}.answers'.format(session['question_num']) : answers,
                        u'Questions.{}.correct_answer'.format(session['question_num']) : new_answer,
                        u'Questions.{}.question'.format(session['question_num']) : new_question
            })

            session['answers'] = answers
            session['correct'] = new_answer
            session['question'] = new_question

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

        # question = curr_ref['question01']['question']
        # answers = curr_ref['question01']['answers']
        # answerLength = len(answers)

        # return render_template('survey_open.html', Name = surveyName, question = question, 
        # answers = answers, question_amount = length, answerLength = answerLength, 
        # questionArray = questionArray)

        session['question_num'] = 'question01'
        session['question'] = curr_ref['question01']['question']
        session['answers'] = curr_ref['question01']['answers']
        session['question_type'] = curr_ref[string]['question_type']
        session['answerLength'] = len(session['answers'])

    elif request.method == 'POST':

        info = request.form
        print(info)
        #get question0# or question# from button

        if 'question' in request.form['submit']:

            number = int(request.form['submit'].split('n')[1])
            
            if(number >= 10):
                string = "question" + str(number)
            else:
                string = "question0" +str(number)

            session['question_num'] = string
            session['question'] = curr_ref[string]['question']
            session['answers'] = curr_ref[string]['answers']
            session['question_type'] = curr_ref[string]['question_type']
            session['answerLength'] = len(session['answers'])

            # return render_template('survey_open.html', Name = surveyName, question = question,
            # answers = answers, question_amount = length, answerLength = answerLength,
            # questionArray = questionArray)
    
        elif request.form['submit'] == 'modify-submit':
        
            info = request.form
            print(info)
            
            answers = []
            for num in range(1, len(session['answers'])+1):
                if len(info) > 2:
                    answers.append(info['q' + str(num)])

            num_to_let = {'1' : 'A',
                        '2' : 'B',
                        '3' : 'C', 
                        '4' : 'D'}

            try:
                new_question = info['asked-question']
            except KeyError:
                try:
                    new_question = info['asked-question']
                except:
                    new_question = ''

            ref.document(session['user_id']).collection('Surveys').document(surveyName).update({
                    u'Questions.{}.answers'.format(session['question_num']) : answers,
                    u'Questions.{}.question'.format(session['question_num']) : new_question
            })

            session['answers'] = answers
            session['question'] = new_question

    return render_template('survey_open.html', Name = surveyName, question = session['question'], 
        answers = session['answers'], question_amount = length, answerLength = session['answerLength'], 
        questionArray = questionArray, question_type = session['question_type'])

# surveys = ref.document("test").collection("Surveys").stream()
# for survey in surveys:
#     if survey.to_dict()["ID"] == "1":
#         # print(survey.to_dict())

if __name__ == "__main__":
    app.run(port=5055, debug=True)
