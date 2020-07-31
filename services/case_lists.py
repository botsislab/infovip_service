from flask import Blueprint, jsonify, request, Response, session, abort, make_response
from werkzeug.wsgi import FileWrapper
from managers import case_list_manager
from managers import mock_faers_manager
from managers import temporary_file_manager
from managers import label_manager
from managers import dedup_manager
from managers import qq_file_manager
from multiprocessing import Process
import json
import re
import time
import requests
import os

# What are the services I need for paging?

# POST /case_lists/
# Creates a new case series from a query or file with "processed" fields set to 0

# GET /case_lists/<int:case_list_id>
# Returns metadata for case series including "processed" status

# GET /case_lists/<int:case_list_id>/groups/?filter=<str:filter>
# Returns groups for case series, optionally filtered

# POST /case_lists/<int:case_list_id>/groups/
# Update groups for case series

# POST /case_lists/<int:case_list_id>
# If query_updated = true, queries database and sets "processed" fields to 0

case_lists_api = Blueprint('case_lists_api', __name__)

def require_login():
    if 'username' not in session:
        abort(401)

def get_username():
    return 'infovip' # Change to use FDA authenticated user
    # if 'username' not in session:
    #     abort(401)
    # else:
    #     return session['username']

ALLOWED_EXTENSIONS = ['xlsx']

def allowed_filename(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@case_lists_api.route('/case_lists', methods = ['POST'])
def upload_file():
    # username = session['username']
    username = 'infovip' # TODO Change to use whatever authentication FDA uses
    filename = username + '_' + str(int(round(time.time() * 1000)))

    # Save temporary file
    save_temporary_file(request, filename)

    try:
        # Add entry to database
        qq_file_manager.create_case_list_to_process(filename)
    except Exception as e:
        # If entry fails for any reason, delete file and abort
        message = 'Unable to create case list to process for file: %s' % filename
        print(message, e)

        temporary_file_manager.delete(filename)

        error_response(message, 500)

    try:
        # Spin up process to do the actual parsing and storing of the file contents
        process = Process(target = qq_file_manager.process_case_list_file, args = (filename, username))
        # process = Process(target = test_job)
        process.start()
    except Exception as e:
        # If creation of process fails for any reason, remove case list to process, delete file, and abort
        message = 'Unable to process case list for file: %s' % filename
        print(message, e)

        print('Removing case list to process entry from database')
        qq_file_manager.delete_case_list_to_process(filename)

        temporary_file_manager.delete(filename)

        error_response(message, 500)

    # Return a success response
    return jsonify(filename = filename)

@case_lists_api.route('/case_lists_to_process', methods = ['GET'])
def get_case_lists_to_process():
    case_lists_to_process = qq_file_manager.get_case_lists_to_process()
    return jsonify(case_lists_to_process)

@case_lists_api.route('/case_lists_to_process/<case_list_to_process_filename>', methods = ['GET'])
def get_case_list_to_process(case_list_to_process_filename):
    case_list_to_process = qq_file_manager.get_case_list_to_process(case_list_to_process_filename)
    return jsonify(case_list_to_process)

def save_temporary_file(request, filename):
    # Make sure the file we expect was given
    if 'file' not in request.files or request.files['file'] is None:
        error_response('No file was submitted', 400)

    uploaded_file = request.files['file']

    # Check for filename
    if uploaded_file.filename == '':
        error_response('No file was submitted', 400)
    
    # Check for a valid filename (extension)
    if not allowed_filename(uploaded_file.filename):
        error_response('The file extension must one of: ' + ', '.join(ALLOWED_EXTENSIONS), 400)

    temporary_file_manager.save_uploaded_file(uploaded_file, filename)

def error_response(message, status):
    abort(make_response(jsonify({
        'message': message
    }), status))

@case_lists_api.route('/case_lists/<int:case_list_id>', methods = ['POST'])
def update_case_list(case_list_id):
    require_login()
    case_list_object = request.get_json()
    case_list_manager.update_case_list(case_list_id, case_list_object)
    return jsonify(case_list_object)

@case_lists_api.route('/case_lists', methods = ['GET'])
def get_case_lists():
    # require_login() TODO Use FDA auth
    # username = session['username']
    username = 'infovip'
    return jsonify(case_list_manager.get_case_lists(username))

@case_lists_api.route('/case_lists/<int:case_list_id>', methods = ['DELETE'])
def delete_case_list(case_list_id):
    # require_login()
    case_list = case_list_manager.get_case_list(case_list_id)

    if case_list['username'] != get_username():
        error_response('Logged in user isn\'t allowed to delete this working case series', 401)
    elif not is_clean_field(case_list_id):
        error_response('Invalid character found in case list id (only alphanumeric or dashes allowed)', 400)
    else:
        case_list_manager.delete_case_list(case_list_id)

        return jsonify({
            'message': 'Successfully deleted case list with id: %s' % case_list_id
        })

@case_lists_api.route('/case_lists/<int:case_list_id>/cases', methods = ['GET'])
def get_case_list_cases(case_list_id):
    # require_login()

    # Get case ids for this case list
    case_ids = case_list_manager.get_case_list_case_ids(case_list_id)

    # Get cases using case ids
    cases = mock_faers_manager.get_cases_by_ids(case_ids)

    return jsonify(cases)

# Doing this as a separate service because it's more data processing intensive
@case_lists_api.route('/case_lists/<int:case_list_id>/temporal_features', methods = ['GET'])
def get_case_list_features(case_list_id):
    require_login()

    param = request.args.get('query')
    search_query = param if param is not None and param != '' else None
    if search_query is not None and not re.match('^[a-zA-Z0-9 ]+$', search_query):
        return jsonify({
            'message': 'The search query included invalid characters. Only alphanumeric characters and spaces are permitted'
        }), 400

    case_list_features = case_list_manager.get_case_list_temporal_features(case_list_id, search_query)

    return jsonify(case_list_features)

def get_case_features(case_id):
    features = case_list_manager.get_case_features(case_id)

    return features

@case_lists_api.route('/case/<case_id>/labels', methods = ['GET'])
def get_case_labels(case_id):
    require_login()

    # Validate inputs
    if not is_clean_field(case_id):
        return jsonify({
            'message': 'Invalid character found in case_id (only alphanumeric or dashes allowed)'
        }), 400

    return jsonify(label_manager.get_case_labels(case_id))

@case_lists_api.route('/exclude_case', methods = ['POST'])
def exclude_case():
    require_login()
    payload = request.get_json()
    case_list_id = payload['case_list_id']
    case_id = payload['case_id']
    exclusion_category = payload['exclusion_category']

    # Validate inputs
    if not is_clean_field(case_list_id) or not is_clean_field(case_id) or not is_clean_field(exclusion_category):
        return jsonify({
            'message': 'Invalid character found in payload (only alphanumeric or dashes allowed)'
        }), 400
    
    case_list_manager.exclude_case(case_id, case_list_id, exclusion_category)

    return jsonify({'message': 'Case %s excluded from case list %s as %s' % (case_id, case_list_id, exclusion_category)})

@case_lists_api.route('/include_case', methods = ['POST'])
def include_case():
    require_login()
    payload = request.get_json()
    case_list_id = payload['case_list_id']
    case_id = payload['case_id']

    # Validate inputs
    if not is_clean_field(case_list_id) or not is_clean_field(case_id):
        return jsonify({
            'message': 'Invalid character found in payload (only alphanumeric or dashes allowed)'
        }), 400
    
    case_list_manager.include_case(case_id, case_list_id)

    return jsonify({'message': 'Case %s included in case list %s' % (case_id, case_list_id)})

def is_clean_field(field):
    return re.match('^[a-zA-Z0-9-]+$', str(field))

@case_lists_api.route('/case_lists/<int:case_list_id>/export', methods = ['GET'])
def case_list_export(case_list_id):
    deduped_file_bytes = dedup_manager.get_deduped_file_bytes(case_list_id)
    wrapped = FileWrapper(deduped_file_bytes)
    response = Response(wrapped, mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', direct_passthrough = True)
    response.headers.set('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response.headers.set('Content-Disposition', 'attachment', filename = 'export.xlsx')
    response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate, public, max-age=0')
    response.headers.set('Expires', '0')
    response.headers.set('Pragma', 'no-cache')
    return response
