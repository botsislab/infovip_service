import mysql.connector
# from datetime import datetime
import os

def get_connection():
    return mysql.connector.connect(
        user = 'root',
        password = os.getenv('DATABASE_PASS', 'password'),
        host = os.getenv('DATABASE_HOST', 'localhost'),
        database = 'infovip',
        ssl_disabled = True,
        option_files = './mysql.cnf',
        use_pure = True # https://stackoverflow.com/questions/52759667/properly-getting-blobs-from-mysql-database-with-mysql-connector-in-python
    )

def query_one(query, params):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, params)
    result = cursor.fetchone()
    connection.close()
    return result

def get_all(table_name):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM ' + table_name)
    results = cursor.fetchall()
    connection.close()
    return results

def get_one(table_name, where_columns, where_values):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    where_clause = get_where_clause(where_columns)
    query = 'SELECT * FROM ' + table_name + ' ' + where_clause
    cursor.execute(query, where_values)
    result = cursor.fetchone()
    connection.close()
    return result

def get_rows_where(table_name, where_columns, where_values):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    where_clause = get_where_clause(where_columns)
    query = 'SELECT * FROM ' + table_name + ' ' + where_clause
    cursor.execute(query, where_values)
    result = cursor.fetchall()
    connection.close()
    return result

def get_all_as_dicts(query, params = ()):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    return results

def update(table_name, update_map, where_map):
    set_clause = get_set_pairs_string(update_map.keys())
    where_clause = get_where_clause(where_map.keys())
    query = 'UPDATE %s SET %s %s' % (table_name, set_clause, where_clause)
    params = tuple(update_map.values()) + tuple(where_map.values())
    do_update(query, params)

def get_where_clause(where_columns):
    where_clause = ''

    for index, column in enumerate(where_columns):
        where_clause += 'WHERE ' if index == 0 else 'AND '
        where_clause += column + ' = %s '

    return where_clause

def get_set_pairs_string(update_columns):
    set_pairs_strings = []

    for column in update_columns:
        set_pairs_strings.append(column + ' = %s')

    return ', '.join(set_pairs_strings)

def do_update(query, params):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    connection.commit()
    connection.close()

def do_update_many(query, params_list):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.executemany(query, params_list)
    connection.commit()
    connection.close()

def get_one_as_dict(query, params = ()):
    connection = get_connection()
    cursor = connection.cursor(dictionary = True)
    cursor.execute(query, params)
    result = cursor.fetchone()
    connection.close()
    return result

# def exists(query, params):
#     connection = get_connection()
#     cursor = connection.cursor()
#     cursor.execute(query, params)
#     return cursor.fetchone() != None

# def get_years_ago_date_string(years_ago):
#     today = datetime.today().strftime('%Y-%m-%d')
#     parts = today.split('-')
#     # Decrement year
#     parts[0] = str(int(parts[0]) - years_ago)
#     return '-'.join(parts)

# def get_today_date_string():
#     return datetime.today().strftime('%Y-%m-%d')