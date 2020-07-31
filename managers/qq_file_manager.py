from managers import temporary_file_manager
from managers import case_list_manager
import case_list
import db_util
import traceback
from io import BytesIO

def create_case_list_to_process(filename):
    query = "INSERT INTO case_lists_to_process (filename, status) VALUES (%s, 'new')"
    db_util.do_update(query, (filename,))
    return filename

def delete_case_list_to_process(filename):
    query = 'DELETE FROM case_lists_to_process WHERE filename = %s'
    db_util.do_update(query, (filename,))

def get_case_lists_to_process():
    return db_util.get_all_as_dicts("SELECT * FROM case_lists_to_process")

def get_case_list_to_process(filename):
    return db_util.get_one_as_dict("SELECT * FROM case_lists_to_process WHERE filename = %s", (filename,))

def process_case_list_file(filename, username):
    try:
        # Update status to 'parsing' TODO
        db_util.update(
            'case_lists_to_process',
            {
                'status': 'parsing'
            },
            {
                'filename': filename
            }
        )

        # Parse case list
        case_list = parse_case_list(temporary_file_manager.get_full_path(filename))

        # Store case list
        store_case_list(username, case_list, temporary_file_manager.get_full_path(filename))

        # Remove from case_list_to_process
        # Update status to 'parsing' TODO
        db_util.update(
            'case_lists_to_process',
            {
                'status': 'done'
            },
            {
                'filename': filename
            }
        )
    
    except Exception:
        print('Unable to process uploaded file %s' % filename)
        print(traceback.format_exc())
        db_util.update(
            'case_lists_to_process',
            {
                'status': 'error'
            },
            {
                'filename': filename
            }
        )

    # Delete temporary file
    temporary_file_manager.delete(filename)

def parse_case_list(path):
    return case_list.from_xls(path)

def store_case_list(username, case_list, filename):

    # Update case detail store
    updated_case_ids = case_list_manager.update_case_detail_store(case_list, False)

    # Create case list
    case_list_id = case_list_manager.create_case_list(username, case_list, filename)

    # Add case ids to new case list
    case_list_manager.populate_case_list(case_list_id, case_list)

    # TODO Only commit on no errors?
    return {
        'case_list_id': case_list_id,
        'case_ids': case_list.get_case_ids(),
        'updated_case_ids': updated_case_ids
    }

def get_case_list_file_bytes(case_list_id):
    query = 'SELECT file FROM case_lists WHERE id = %s'
    result = db_util.query_one(query, (case_list_id,))

    if result['file'] is None:
        # TODO Create excel file from scratch
        raise Exception('Original quick query file not found to modify')
    else:
        return BytesIO(result['file'])