from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask.ext.bootstrap import Bootstrap
from jinja2 import Template
from strogonanoff_sender import send_command
from WiringPin import WiringPin

# create our little application :)
app = Flask(__name__)
pin = WiringPin(0).export()
Bootstrap(app)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE='/home/server/flaskr.db',
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select switch_name, switch_channel, switch_button, switch_last_state from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/flickswitch/<channel>/<button>/<on>', methods = ['GET'])
def switch(channel,button,on):
	db = get_db()
        if on == 'on':
                state = True
		db.execute("update entries set switch_last_state = 'on' where switch_channel = ? and switch_button = ?",[channel,button])
        	db.commit()
	else:
                state = False
		db.execute("update entries set switch_last_state = 'off' where switch_channel = ? and switch_button = ?",[channel,button])
        	db.commit()
	for i in range(1,8):
                send_command(pin,int(channel),int(button),state)
        return 'ok'


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (switch_name, switch_channel, switch_button) values (?, ?, ?)',
                 [request.form['switch_name'], request.form['switch_channel'], request.form['switch_button']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/delete/<switch_name>', methods=['GET'])
def delete_entry(switch_name):
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from entries where switch_name = ?',[switch_name])
    db.commit()
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    #init_db() #Uncomment for a clean start
    app.run(host='0.0.0.0')

