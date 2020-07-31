from flask import Flask, request, Response, abort, session, jsonify
from werkzeug.exceptions import HTTPException
from services.case_lists import case_lists_api
from services.faers import faers_api
from managers import mock_faers_manager
from managers import meddra_manager
from managers import case_list_manager
from pubmed import pubmed_manager
import tempfile
import json
import decimal
import datetime
import auth_manager
import traceback

app = Flask(__name__)
app.secret_key = b'_i#y28"64Q8zsp9c]/'
base_url = '/api'

app.register_blueprint(case_lists_api, url_prefix = base_url)
app.register_blueprint(faers_api, url_prefix = base_url)

@app.errorhandler(Exception)
def handle_error(error):
    message = str(error)
    code = 500

    if isinstance(error, HTTPException):
        print(error)
        code = error.code
    elif isinstance(error, KeyError):
        print('Encountered error while processing request', traceback.format_exc())
        message = 'An unexpected error occurred'
    elif isinstance(error, TypeError):
        print('Encountered error while processing request', traceback.format_exc())
        message = 'An unexpected error occurred'
    else:
        print(error)

    return jsonify(message = message), code

@app.route(base_url + '/')
def root():
    return '''Root page'''

# https://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object
class DecimalEncoder(json.JSONEncoder):
    def default(self, o): # pylint: disable=E0202
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return super(DecimalEncoder, self).default(o)

app.json_encoder = DecimalEncoder

@app.route(base_url + '/meddra_pts', methods = ['GET'])
def get_meddra_pts():
    require_login()
    meddra_pts = meddra_manager.get_meddra_pts()
    return jsonify(meddra_pts)

@app.route(base_url + '/meddra_hlts', methods = ['GET'])
def get_meddra_hlts():
    require_login()
    meddra_hlts = meddra_manager.get_meddra_hlts()
    return jsonify(meddra_hlts)

@app.route(base_url + '/hlt_autocomplete_search')
def hlt_autocomplete_search():
  query = request.args.get('query')
  if query:
    hlts = meddra_manager.get_meddra_hlts()
    filtered_hlts = list(filter(lambda hlt: query.lower() in hlt['name'].lower(), hlts))
    results = [{
      'text': hlt['name'],
      'value': hlt['id']
    } for hlt in filtered_hlts]
    return jsonify(results)
  else:
    return jsonify({
      'message': 'The parameter \'query\' must be provided'
    }), 400

@app.route(base_url + '/pt_autocomplete_search')
def pt_autocomplete_search():
  query = request.args.get('query')
  if query:
    pts = meddra_manager.get_meddra_pts()
    filtered_pts = list(filter(lambda pt: query.lower() in pt['name'].lower(), pts))
    results = [{
      'text': pt['name'],
      'value': pt['id']
    } for pt in filtered_pts]
    return jsonify(results)
  else:
    return jsonify({
      'message': 'The parameter \'query\' must be provided'
    }), 400

@app.route(base_url + '/case/<case_id>', methods = ['GET'])
def get_case(case_id):
    require_login()
    case = case_list_manager.get_case(case_id)
    return jsonify(case)

@app.route(base_url + '/cases', methods = ['GET'])
def get_all_cases():
    require_login()
    all_cases = case_list_manager.get_all_cases()
    return jsonify(all_cases)

@app.route(base_url + '/articles/<query>', methods = ['GET'])
def get_articles(query):
    require_login()
    # TODO
    # email = request.args.get('email')
    # if not email:
    #     abort(403)
    email = 'jspiker3@jhmi.edu'
    return jsonify(pubmed_manager.get_articles(query, email))

# TODO Change to use FDA authenticated user, this service might be defunct at that point
@app.route(base_url + '/login', methods = ['POST'])
def do_login():
    credentials = request.get_json()

    if 'username' not in credentials or 'password' not in credentials:
        return jsonify({
            'message': 'username and password are required to login'
        }), 403

    username = credentials['username']
    password = credentials['password']

    if username and password and auth_manager.authenticate(username, password):
        session['username'] = username
        return jsonify({
            'message': username + ' was successfully logged in'
        })
    else:
        return jsonify({
            'message': 'invalid username/password combination for ' + username
        }), 403

@app.route(base_url + '/logout', methods = ['POST'])
def do_logout():
    username = session.pop('username', None)
    if username is not None:
        return jsonify({
            'message': username + ' was successfully logged out'
        })
    else:
        return jsonify({
            'message': 'no user was logged in'
        }), 400

def require_login():
    if 'username' not in session:
        abort(401)

if __name__ == '__main__':
    app.run()
