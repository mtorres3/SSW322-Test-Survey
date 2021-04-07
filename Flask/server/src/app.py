from flask import Flask, render_template, request, session, redirect, url_for, g, abort
import sqlite3

app = Flask(__name__)
app.secret_key = 'okay'

class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User: {self.username}>'

conn = sqlite3.connect('LOGINS.db', check_same_thread=False)
c = conn.cursor()

# Deletes all previous login information

# c.execute("DROP TABLE IF EXISTS INFORMATION")
# c.execute(''' CREATE TABLE INFORMATION (
#                 [ID] TEXT PRIMARY KEY,
#                 [username] TEXT,
#                 [password] TEXT
#         )''')
# users = [User(-1, 'Jon', '123'), User(-2, 'Joe', '123'), User(-3, 'Will', '123'), User(-4, 'Marky', '123')]

def redefine():
    #users = [User(-1, 'Jon', '123'), User(-2, 'Joe', '123'), User(-3, 'Will', '123'), User(-4, 'Marky', '123')]
    c.execute('SELECT ID, username, password FROM INFORMATION')
    s = len(c.fetchall())

    u = []
    c.execute('SELECT ID, username, password FROM INFORMATION')
    for row in c.fetchall():
        u = u + [User(row[0], row[1], row[2])]

    return u, s

users = redefine()[0]
size = redefine()[1]

@app.before_request
def before_request():
    redefine()
    g.user = None
    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        g.user = user

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':

        session.pop('user_id', None)

        username = request.form['username']
        password = request.form['password']

        try:
            user = [x for x in users if x.username == username][0]
        except IndexError:
            return redirect(url_for('login'))

        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('taker_or_creator'))

        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_id = size + 1
        username = request.form['username']
        password = request.form['password']

        sql = '''INSERT INTO INFORMATION (ID, username, password)
                VALUES(?,?,?)'''
        c.execute(sql, [new_id, username, password])
        conn.commit()
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

if __name__ == "__main__":
    app.run(port=5029, debug=True)