import db_util
import random
from time import sleep

MAX_SLEEP_SECONDS = 3

def mock_delay():
  sleep(random.random() * (MAX_SLEEP_SECONDS - 0.5) + 0.5)

def get_cases_by_ids(case_ids):
  mock_delay()

  query = '''SELECT
          case_id,
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
          narrative
      FROM faers_case_details
      WHERE case_id IN (\'%s\')''' % '\', \''.join(case_ids)

  cases = db_util.get_all_as_dicts(query)
  return cases

def get_products():
  # TODO The real result should be cached so no delay here
  query = 'SELECT DISTINCT product_1_product_name AS name FROM faers_case_details ORDER BY name'
  products = db_util.get_all_as_dicts(query)
  return [product['name'] for product in products]

def faers_report_query(products = [], hlts = [], pts = []):
  mock_delay()

  query = '''
    SELECT 
      case_id,
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
      narrative
    FROM faers_case_details
  '''

  if products:
    product_query = ' OR '.join(['all_suspect_product_names LIKE concat(\'%\', %s, \'%\')\n']*len(products))
    query += ' WHERE (' + product_query + ')\n'

  if hlts:
    hlt_query = ' OR '.join(['all_hlts LIKE concat(\'%\', %s, \'%\')\n']*len(hlts))

    if products:
      query += ' AND (' + hlt_query + ')\n'
    else:
      query += ' WHERE (' + hlt_query + ')\n'

  if pts:
    pt_query = ' OR '.join(['all_pts LIKE concat(\'%\', %s, \'%\')\n']*len(pts))

    if products or hlts:
      query += ' AND (' + pt_query + ')\n'
    else:
      query += ' WHERE (' + pt_query + ')\n'

  params = tuple(products) + tuple(hlts) + tuple(pts)

  reports = db_util.get_all_as_dicts(query, params)

  return reports

def get_duplicate_groups(reports):

  case_ids = [report['case_id'] for report in reports]

  query = '''
    SELECT
      GROUP_CONCAT(case_id SEPARATOR '|') as case_id,
      GROUP_CONCAT(age_in_years),
      sex,
      pt_term_event_1,
      product_1_product_name
    FROM faers_case_details
    WHERE case_id IN (\'%s\')
    GROUP BY sex, product_1_product_name, pt_term_event_1
  ''' % '\', \''.join(case_ids)

  grouped = db_util.get_all_as_dicts(query)

  only_duplicate_groups = list(filter(lambda group: '|' in group['case_id'], grouped))
  print(only_duplicate_groups)

  duplicates = [{
    'case_ids': duplicate_group['case_id'].split('|')
  } for duplicate_group in only_duplicate_groups]

  return duplicates