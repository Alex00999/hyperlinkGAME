from flask import Flask, render_template, url_for, session, redirect, request, abort, g, flash
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from forms import LoginForm, RegisterForm

from FDataBase import FDataBase
from UserLogin import UserLogin
from random import sample

import sqlite3
import os

from werkzeug.security import generate_password_hash, check_password_hash

from bs4 import BeautifulSoup as BS
import requests

# конфиг
DATABASE = '/tmp/site.db'
DEBUG = True
SECRET_KEY = 'e}jy84lNlGhWStLRjyr3Wl3h6ipUlpasSoKv1}tdFSMm}#YH10Kops0ne5h7r4Wo'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'site.db')))

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def update_summary():
    dbase.fillDb()


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


def get_menu(session):
    if 'userLogged' in session:
        menu = {
            "menu": [
                {
                    "title": "Выйти",
                    "link": "/logout",
                },
                {
                    "title": session['userLogged'],
                    "link": "/profile",
                }
            ]
        }
    else:
        menu = {
            "menu": [
                {
                    "title": "Регистрация",
                    "link": "/registration",
                    "type": "active"
                },
                {
                    "title": "Вход",
                    "link": "/login"
                },
            ]
        }
    return menu


dbase = None


@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, dbase)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route('/')
@app.route('/home')
def index():
    leader_data = dbase.getLeaders(5)
    return render_template("index.html", menu=get_menu(session)['menu'], leader_data=leader_data)


@app.route('/info')
def info():
    return render_template("info.html", menu=get_menu(session)['menu'])


@app.route('/favicon.ico')
def favicon():
    return


@app.route("/profile")
def redirect_to_user_profile():
    return redirect('profile/' + str(session['userId']))


@app.route("/profile/<id>")
def profile(id):
    try:
        user = dbase.getUser(id)
        userdata = [user['name'], user['pts'], user['last_game']]
        return render_template('profile.html', menu=get_menu(session)['menu'], userdata=userdata)
    except TypeError:
        abort(404)


@app.route('/start')
@login_required
def start():
    articles = dbase.getArticles()
    start_goal_data = sample(articles, 2)
    start_goal = start_goal_data[0][0], start_goal_data[1][0]
    summary = start_goal_data[0][1], start_goal_data[1][1]
    start_link = '-'.join(start_goal)
    session['wikiQueue'] = []
    return render_template('start.html', menu=get_menu(session)['menu'], articles=start_goal, link=start_link,
                           summary=summary)


@app.route('/starting/<data>')
@login_required
def starting(data):
    start_goal = data.split('-')
    session['goal'] = start_goal[1]
    session['start'] = start_goal[0]
    session['isPlaying'] = True
    return redirect('/wiki/' + start_goal[0])


@app.route('/wiki/<path:req>')
@login_required
def wiki(req):
    if request.method == "GET":
        if session['isPlaying']:
            won_flag = False
            pts_earned = 0
            if req == session['goal']:
                won_flag = True
                pts_earned = (15 - len(session['wikiQueue']) + 1) * 100
                if pts_earned < 0:
                    pts_earned = 0
                dbase.changePts(session['userId'], pts_earned)
                dbase.changeLastGame(session['userId'], session['wikiQueue'] + [req])
                session['isPlaying'] = False
            if len(session['wikiQueue']) == 0:
                session['wikiQueue'].append(req.replace('_', ' '))
            if session['wikiQueue'][len(session['wikiQueue']) - 1] != req.replace('_', ' '):
                session['wikiQueue'].append(req.replace('_', ' '))
            session.modified = True
            r = requests.get('https://ru.wikipedia.org/wiki/' + req)
            html = BS(r.content, 'html.parser')
            page = str(*html.select(".mw-body"))
            page = page.replace('http', '')
            return render_template('wiki.html', pagedata=page, order=session['wikiQueue'],
                                   length=len(session['wikiQueue']) - 1, won=won_flag, pts=pts_earned)
        else:
            return redirect('/start')


@app.route('/w/<path:subpath>')
def w(subpath):
    return '<script>document.location.href = document.referrer</script>'


@app.route('/registration', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash = generate_password_hash(request.form['psw'])
        res = dbase.addUser(form.name.data, form.email.data, hash)
        if res:
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login'))
        else:
            flash("Неверно введены данные", "error")

    return render_template("registration.html", menu=get_menu(session)['menu'], form=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.getUserByEmail(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            user_login = UserLogin().create(user)
            session['userId'] = user['id']
            session['userLogged'] = str(user['name'])
            rm = form.remember.data
            login_user(user_login, remember=rm)
            return redirect("profile/" + str(user['id']))

        flash("Неверный логин или пароль", "error")

    return render_template('login.html', menu=get_menu(session)['menu'], form=form)


@app.route('/logout')
@login_required
def logout():
    session.pop('userLogged')
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.errorhandler(404)
def pageNotFound(error):
    return render_template('error.html', title="Страница не найдена", error_message='Страница не найдена',
                           menu=get_menu(session)['menu'])


@app.errorhandler(401)
def pageNotFound(error):
    return render_template('error.html', title="Ошибка авторизации", error_message='Вы не авторизованы',
                           menu=get_menu(session)['menu'])


if __name__ == '__main__':
    app.run(port=8000, host='127.0.0.1', debug=True)
