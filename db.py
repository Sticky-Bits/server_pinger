import sqlite3
from config import SERVER_LIST, SLACK_URL

DB_FILENAME = 'pingping.db'


def run_sql(sql, values=[]):
    conn = get_connection()
    c = conn.cursor()
    # if sql is a list or tuple, assume we're passing a list of commands to run.
    if type(sql) in (list, tuple):
        for sql_m, values_m in sql:
            c.execute(sql_m, values_m)
    else:
        c.execute(sql, values)
    res = c.fetchall()
    conn.commit()
    conn.close()
    return res


def get_server_name(server):
    return server if type(server) == str else server['name']


def add_server(server):
    run_sql('insert into servers values(?,?,?)', list(server.values()))


def add_multiple_servers(servers):
    sql_list = []
    for server in servers:
        sql_list.append(
            ('insert into servers values(?,?,?)', list(server.values()))
        )
    run_sql(sql_list)


def remove_server(server):
    name = get_server_name(server)
    run_sql('delete from servers where name=?', [name])


def set_server_status(server, status):
    name = get_server_name(server)
    run_sql('update servers set previous_status=? where name=?', [status, name])


def change_server_url(server, url):
    name = get_server_name(server)
    run_sql('update servers set url=? where name=?', [url, name])


def get_slack_url():
    return run_sql('select slack_url from meta')[0][0]


def get_servers():
    return run_sql('select * from servers')


def change_slack_url(url):
    run_sql('update meta set slack_url=?', [url])


def new_connection(server_list, slack_url):
    # Create db and close connection immediately. We use our helper functions for the rest.
    return sqlite3.connect(f'{DB_FILENAME}')


def init_db():
    # Create tables
    run_sql('create table servers (name text, url text, previous_status text)')
    run_sql('create table meta (slack_url text)')

    # Insert into tables
    add_multiple_servers(SERVER_LIST)
    run_sql(f'insert into meta values (?)', [SLACK_URL])


def get_connection():
    # Connects to existing db, or creates new one with starting data
    try:
        return sqlite3.connect(f'file:{DB_FILENAME}?mode=rw', uri=True)
    except sqlite3.OperationalError:
        conn = new_connection(SERVER_LIST, SLACK_URL)
        init_db()
        return conn
