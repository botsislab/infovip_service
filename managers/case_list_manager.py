from managers import meddra_manager
import mysql.connector
from mysql.connector import errorcode
import json
import re
import datetime
import time
import case_list
import os
import db_util
import traceback

def populate_case_list(case_list_id, case_list):

    # Get ids
    case_ids = case_list.get_case_ids()

    # Add case list id
    to_insert = [(case_list_id, case_id) for case_id in case_ids]

    connection = db_util.get_connection()
    cursor = connection.cursor()

    columns = ['case_list_id', case_list.get_id_column_name()]
    columns_string = ','.join(columns)
    placeholders = ','.join(['%s'] * len(columns))

    query = 'INSERT INTO case_list_case_details (' + columns_string + ') VALUES (' + placeholders + ')'
    
    cursor.executemany(query, to_insert)

    connection.commit()
    connection.close()

def update_case_detail_store(case_list, force_update):

    updated_case_ids = []

    connection = db_util.get_connection()
    cursor = connection.cursor()

    all_tuples = case_list.get_tuples()
    columns = case_list.case_detail_headers
    case_id_index = columns.index('case_id')

    # INSERT INTO faers_case_details (case_id, faers_case_number, version_number...) VALUES (%s, %s, %s...)
    columns_string = ','.join(columns)
    placeholders = ','.join(['%s'] * len(columns))

    query = 'INSERT INTO faers_case_details (' + columns_string + ') VALUES (' + placeholders + ')'

    for params in all_tuples:

        try:
            cursor.execute(query, params)
            updated_case_ids.append(params[case_id_index])
    
        except mysql.connector.Error as error:

            # Do update if the key already exists
            if error.errno == errorcode.ER_DUP_ENTRY:

                if force_update:
                    # TODO Is there a cleaner way to build this?
                    assignment_pair_strings = [column + ' = %s' for column in columns if column != 'faers_case_number' and column != 'version_number']
                    assignment_string = ','.join(assignment_pair_strings)

                    update_query = 'UPDATE faers_case_details SET ' + assignment_string + ' WHERE faers_case_number = %s and version_number = %s'
                    update_params = tuple(params[index] for index, column in enumerate(columns) if column != 'faers_case_number' and column != 'version_number')
                    update_params_with_where = update_params + (params[columns.index('faers_case_number')],) + (params[columns.index('version_number')],)

                    cursor.execute(update_query, update_params_with_where)
                    updated_case_ids.append(params[case_id_index])
            else:
                print('failed to insert the following row of data (error follows): ' + str(params))
                print(traceback.format_exc())

    connection.commit()
    connection.close()

    return updated_case_ids

def create_case_list(username, case_list, filename):
    
    connection = db_util.get_connection()
    cursor = connection.cursor()

    case_list_id = get_next_case_list_id(cursor)

    with open(filename, 'rb') as case_list_file:
        case_list_file_contents = case_list_file.read()
        cursor.execute('INSERT INTO case_lists (id, username, selection_criteria, number_of_cases, file) VALUES (%s, %s, %s, %s, %s)',
            (str(case_list_id), username, json.dumps(case_list.selection_criteria), case_list.get_number_of_cases(), case_list_file_contents)
        )

    connection.commit()
    connection.close()

    return case_list_id

def update_case_list(case_list_id, case_list_object):
    table_name = 'case_lists'
    # Only allow updating of name
    update_map = {
        'name': case_list_object['name']
    }
    where_map = {
        'id': case_list_id
    }

    db_util.update(table_name, update_map, where_map)

def delete_case_list(case_list_id):

    connection = db_util.get_connection()
    cursor = connection.cursor()

    cursor.execute('DELETE FROM case_lists WHERE id = %s', (case_list_id,))

    connection.commit()
    connection.close()

    return case_list_id

def get_case_list(case_list_id):

    query = 'SELECT id, username, selection_criteria, name, number_of_cases, created_at FROM case_lists WHERE id = %s'
    case_list = db_util.get_one_as_dict(query, (case_list_id,))

    case_list['selection_criteria'] = json.loads(case_list['selection_criteria'])

    return case_list

def get_next_case_list_id(cursor):

    cursor.execute('SELECT MAX(id) FROM case_lists')

    result = cursor.fetchone()
    max_id = result[0] if result[0] is not None else 0

    return max_id + 1

def get_case_lists(username):

    query = '''
        SELECT
            case_lists.id,
            username,
            selection_criteria,
            name,
            number_of_cases,
            created_at,
            ether_processed,
            dedup_pairs_processed,
            dedup_groups_processed,
            GROUP_CONCAT(case_list_case_details.case_id SEPARATOR "','") as case_ids
        FROM case_lists
        LEFT JOIN case_list_case_details ON case_lists.id = case_list_case_details.case_list_id
        WHERE username = %s
        GROUP BY case_lists.id
        '''
    case_lists = db_util.get_all_as_dicts(query, (username,))

    for case_list in case_lists:

        case_list['selection_criteria'] = json.loads(case_list['selection_criteria'])

        # Add status object
        case_list['processing_status'] = get_processing_status(case_list)

    return case_lists

def get_processing_status(case_list):
    status = {}
    # status['ether_progress'] = get_ether_progress(case_list)
    # status['dedup_pairs_progress'] = get_dedup_pairs_progress(case_list)
    # status['dedup_groups_progress'] = get_dedup_groups_progress(case_list)

    if case_list['ether_processed'] == 0:
        status['name'] = 'nlp'
    elif case_list['dedup_pairs_processed'] == 0 or case_list['dedup_groups_processed'] == 0:
        status['name'] = 'dedup'
    else:
        status['name'] = 'ready'

    del case_list['ether_processed']
    del case_list['dedup_pairs_processed']
    del case_list['dedup_groups_processed']

    return status

def get_ether_progress(case_list):
    query = '''
        SELECT COUNT(*) as processed
        FROM (
            SELECT ether_case_features.case_id FROM case_list_case_details
            INNER JOIN ether_case_features ON (case_list_case_details.case_id = ether_case_features.case_id)
            WHERE case_list_case_details.case_list_id = %s
            GROUP BY case_list_case_details.case_id
        ) as processed_cases
    '''
    print(query)

    result = db_util.get_one_as_dict(query, (case_list['id'],))
    print(result)

    return result['processed']

def get_dedup_pairs_progress(case_list):
    query = '''
        SELECT * FROM (
            SELECT duplicate_results.case_id_1, duplicate_results.case_id_2 FROM case_list_case_details
            INNER JOIN duplicate_results ON (case_list_case_details.case_id = duplicate_results.case_id_1 OR case_list_case_details.case_id = duplicate_results.case_id_2)
            WHERE case_list_case_details.case_list_id = %s
            GROUP BY case_list_case_details.case_id
        ) as processed_cases
    '''

    result = db_util.get_all_as_dicts(query, (case_list['id'],))
    print(result)

    return -1

def get_dedup_groups_progress(case_list):
    cases_to_check = case_list['case_ids']

    query = '''
        SELECT count(DISTINCT case_id) as processed FROM case_list_suggested_duplicate_groups
        WHERE case_id IN ('%s')
    ''' % cases_to_check

    result = db_util.get_one_as_dict(query)

    return result['processed']

def get_case_list_cases(case_list_id, search_query):

    query = '''SELECT
            case_list_case_details.case_id,
            case_list_case_details.exclusion_category,
            faers_case_number,
            version_number,
            report_type,
            manufacturer_control_number,
            age_in_years,
            sex,
            weight_kg,
            report_source,
            sender_mfr_organization,
            case_event_date,
            latest_fda_received_date,
            initial_fda_received_date,
            country_derived,
            all_pts,
            all_outcomes,
            MAX(CASE WHEN classification_feature_results.feature_name = 'DrugInducedTermEvaluator' THEN classification_feature_results.feature_value ELSE NULL END) class_drug_induced,
            MAX(CASE WHEN classification_feature_results.feature_name = 'ExpertReporterEvaluator' THEN classification_feature_results.feature_value ELSE NULL END) class_expert_reporter,
            MAX(CASE WHEN classification_feature_results.feature_name = 'NarrativeLengthEvaluator' THEN classification_feature_results.feature_value ELSE NULL END) class_narrative_length,
            MAX(CASE WHEN classification_feature_results.feature_name = 'PreCuratedTermEvaluator' THEN classification_feature_results.feature_value ELSE NULL END) class_causal_term,
            MAX(CASE WHEN classification_feature_results.feature_name = 'ReasonableTimeFrameEvaluator' THEN classification_feature_results.feature_value ELSE NULL END) class_reasonable_timeframe,
            MAX(CASE WHEN classification_feature_results.feature_name = 'SymptomsBeforeEvaluator' THEN classification_feature_results.feature_value ELSE NULL END) class_symptoms_before,
            classifications.classification class_overall
        FROM case_list_case_details
        LEFT JOIN faers_case_details ON case_list_case_details.case_id = faers_case_details.case_id
        LEFT JOIN classification_feature_results ON case_list_case_details.case_id = classification_feature_results.case_id
        LEFT JOIN classifications ON classifications.case_id = faers_case_details.case_id
        WHERE case_list_case_details.case_list_id = %s'''

    if search_query is not None:
        text_search = get_boolean_text_search_clause(search_query)
        query += ' AND ' + text_search
    
    query += ' GROUP BY case_list_case_details.case_id'

    cases = db_util.get_all_as_dicts(query, (case_list_id,))

    return cases

def get_case_list_case_ids(case_list_id):

    query = '''SELECT
            case_id
        FROM case_list_case_details
        WHERE case_list_case_details.case_list_id = %s'''

    case_ids = [case['case_id'] for case in db_util.get_all_as_dicts(query, (case_list_id,))]

    return case_ids

def get_case_list_temporal_features(case_list_id, search_query):

    cases = get_case_list_cases(case_list_id, search_query)
    case_ids = [case['case_id'] for case in cases]

    query = '''SELECT
            ether_case_features.case_id,
            ether_case_extracted.time_exposure,
            IF(
                ether_case_extracted.time_exposure > '1900-01-01' AND ether_case_extracted.time_exposure <= CURDATE(),
                DATEDIFF(feature_temp_start, ether_case_extracted.time_exposure),
                NULL
            ) as relative_days,
            feature_id,
            feature_type,
            clean_text,
            preferred_term,
            feature_temp_start
            # feature_temp_end
        FROM ether_case_features
        LEFT JOIN ether_case_extracted
        ON ether_case_features.case_id = ether_case_extracted.case_id
        WHERE feature_temp_start IS NOT NULL
        AND time_exposure IS NOT NULL
        AND ether_case_features.case_id IN (\'%s\')''' % '\', \''.join(case_ids)

    case_features = db_util.get_all_as_dicts(query)

    return clean_features(case_features)

def get_boolean_text_search_clause(search_query):
    text_search = ''
    terms = search_query.split()
    text_fields = case_list.get_text_fields()

    for term_index, term in enumerate(terms):
        term_search = ''
        for field_index, text_field in enumerate(text_fields):
            if field_index != 0: term_search += ' OR '
            term_search += text_field + ' REGEXP "^' + term + '| ' + term + '"'
        
        if term_index != 0: text_search += ' AND '
        text_search += '(' + term_search + ')'

    return text_search

def exclude_case(case_id, case_list_id, exclusion_category):
    table_name = 'case_list_case_details'
    update_map = {
        'exclusion_category': exclusion_category
    }
    where_map = {
        'case_id': case_id,
        'case_list_id': case_list_id
    }

    db_util.update(table_name, update_map, where_map)

def include_case(case_id, case_list_id):
    table_name = 'case_list_case_details'
    update_map = {
        'exclusion_category': 'none'
    }
    where_map = {
        'case_id': case_id,
        'case_list_id': case_list_id
    }

    db_util.update(table_name, update_map, where_map)

def get_case(case_id):
    case = db_util.get_one('faers_case_details', ('case_id',), (case_id,))
    case['features'] = get_case_features(case_id)
    case['narrative_markup'] = get_section_markup(case['narrative'], case['features'])
    unique_pts = meddra_manager.get_unique_pts(case['features'])
    case['related_pts'] = meddra_manager.get_related_pts(unique_pts)
    case['classification'] =  get_case_classification(case_id)
    case['classification']['features'] = get_case_classification_features(case_id)
    return case

def get_all_cases():
    return db_util.get_all('faers_case_details')

def get_case_features(case_id):
    features = db_util.get_rows_where('ether_case_features', ('case_id',), (case_id,))
    return clean_features(features)

def clean_features(features):
    # Clean up the feature type names
    for feature in features:
        if feature['feature_type'] == 'SECOND_LEVEL_DIAGNOSIS':
            feature['feature_type'] = 'other_term'
        elif feature['feature_type'] == 'SYMPTOM':
            feature['feature_type'] = 'other_term'
        else:
            feature['feature_type'] = feature['feature_type'].lower()
    return features

def get_case_classification(case_id):
    query = 'SELECT total_weight, classification FROM classifications WHERE case_id = %s'
    return db_util.get_one_as_dict(query, (case_id,)) or {}

def get_case_classification_features(case_id):
    query = '''
        SELECT features.feature_name, feature_value, feature_weight, display_name, description
        FROM classification_feature_results as results
        LEFT JOIN classification_features as features ON results.feature_name = features.feature_name
        WHERE results.case_id = %s
    '''
    return db_util.get_all_as_dicts(query, (case_id,)) or []