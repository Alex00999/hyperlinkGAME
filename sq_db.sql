CREATE TABLE IF NOT EXISTS users (
id integer PRIMARY KEY AUTOINCREMENT,
name text NOT NULL,
email text NOT NULL,
psw text NOT NULL,
last_game text NOT NULL,
pts integer NOT NULL,
time integer NOT NULL
);

CREATE TABLE IF NOT EXISTS start_goal (
article text NOT NULL,
summary text NOT NULL
);