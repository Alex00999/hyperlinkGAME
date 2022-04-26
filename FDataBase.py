import sqlite3
import math
import time

from bs4 import BeautifulSoup as BS
import re
import requests


class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def addUser(self, name, email, hpsw):
        pts = 0
        last_game = 'пользователь не сыграл ни одной игры'
        try:
            self.__cur.execute(f"SELECT COUNT() as `count` FROM users WHERE email LIKE '{email}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print("Пользователь с таким email уже существует")
                return False

            tm = math.floor(time.time())
            self.__cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, ?, ?, ?)",
                               (name, email, hpsw, last_game, pts, tm))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления пользователя в БД " + str(e))
            return False

        return True

    def getUser(self, user_id):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE id = {user_id} LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False

            return res
        except sqlite3.Error as e:
            print("Ошибка получения данных из БД " + str(e))

        return False

    def getArticles(self):
        try:
            self.__cur.execute(f"SELECT * FROM start_goal")
            res = self.__cur.fetchall()
            res = [[i[0], i[1]] for i in res]
            return res
        except sqlite3.Error as e:
            print("Ошибка получения данных из БД " + str(e))
        return False

    def getUserByEmail(self, email):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email = '{email}' LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False

            return res
        except sqlite3.Error as e:
            print("Ошибка получения данных из БД " + str(e))

    def changePts(self, id, add_pts):
        try:
            self.__cur.execute(f"SELECT pts FROM users WHERE id = '{id}'")
            old_pts = self.__cur.fetchone()
            new_pts = add_pts + old_pts[0]
            self.__cur.execute(f"UPDATE users SET pts = '{new_pts}' WHERE id = '{id}'")
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления данных в БД " + str(e))

        return False

    def changeLastGame(self, id, new_last_game):
        try:
            print('→'.join(new_last_game))
            self.__cur.execute(f"UPDATE users SET last_game = '{'→'.join(new_last_game)}' WHERE id = '{id}'")
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления данных в БД " + str(e))

        return False

    def getLeaders(self, amount):
        self.__cur.execute(f"SELECT name, pts, id FROM users ORDER BY pts DESC LIMIT {amount}")
        res = self.__cur.fetchall()
        res = [[i[0], i[1], i[2]] for i in res]
        res = [[x + 1] + res[x] for x in range(0, len(res))]
        return res

    def fillDb(self):
        self.__cur.execute(f"SELECT article FROM start_goal")
        res = self.__cur.fetchall()
        res = [i[0] for i in res]
        for article in res:
            r = requests.get('https://ru.wikipedia.org/wiki/' + article)
            html = BS(r.content, 'html.parser')
            summary = html.select("p")[0].get_text()
            summary = re.sub(r'\[[^\]]+\]', '', summary)
            self.__cur.execute(f"UPDATE start_goal SET summary = '{summary}' WHERE article = '{article}'")
            self.__db.commit()
