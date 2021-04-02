from flask import Flask, render_template, request, sessions
app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/taker_or_creator', methods=['GET','POST'])
def taker_or_creator():
    return render_template('taker_or_creator.html')

@app.route('/create_or_open')
def create_or_open():
    return render_template('create_or_open.html')

@app.route('/survey_creation')
def survey_creation():
    return render_template('survey_creation.html')

@app.route('/survey_or_test')
def survey_or_test():
    return render_template('survey_or_test.html')

@app.route('/test_creation')
def test_creation():
    return render_template('test_creation.html')

@app.route('/upload_or_grade')
def upload_or_grade():
    return render_template('upload_or_grade.html')

if __name__ == "__main__":
    app.run(port=5029, debug=True)