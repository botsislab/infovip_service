import db_util
import pandas
import numpy

### FOR API: ###
# @app.route(base_url + '/test_oracle_connection', methods = ['GET'])
# def test_oracle_connection():
#     print('about to connect')
#     import sys
#     from os.path import dirname
#     sys.path.append(dirname('/Users/jspiker3/Desktop/repositories/infovip/infovip_service/oracle/'))
#     print(sys.path)
#     import cx_Oracle
#     con = cx_Oracle.connect('sys/Oradoc_db1@localhost/orcl')
#     print(con.version)
#     con.close()


df = pandas.read_csv('./data/test_data_3.csv')

print(df.head())

connection = db_util.get_connection()
cursor = connection.cursor()

for index, row in df.iterrows():
  # print(row['case_id'],  row['all_concomitants'], row['all_outcomes'])
  # print(type(row['weight_kg']))
  # str(datetime_parts[0]) + '-'+ str(datetime_parts[1]) + '-' + str(datetime_parts[2])
  print(row['all_suspect_product_names'])
  if row['age_in_years'] > 100: continue
  date = None
  if type(row['initial_fda_received_date']) == int and len(str(row['initial_fda_received_date'])) == 8:
    year = str(row['initial_fda_received_date'])[:4]
    month = str(row['initial_fda_received_date'])[4:6]
    day = str(row['initial_fda_received_date'])[6:]
    date = year + '-' + month + '-' + day
  else: continue

  to_insert = {
    'case_id': row['case_id'],
    'faers_case_number': '123',
    'version_number': '1',
    'report_type': '',
    'manufacturer_control_number': '',
    'age_in_years': None if pandas.isna(row['age_in_years']) else row['age_in_years'],
    'sex': None if pandas.isna(row['sex']) else row['sex'],
    'weight_kg': None if pandas.isna(row['weight_kg']) else row['weight_kg'],
    'report_source': 'HP',
    'sender_mfr_organization': row['sender_mfr_organization'],
    # 'case_event_date': None if pandas.isna(row['case_event_date']) else row['case_event_date'],
    # 'latest_fda_received_date': row['latest_fda_received_date'],
    'initial_fda_received_date': date,
    'country_derived': row['country_derived'],
    'all_pts': row['all_pts'],
    'all_outcomes': None if pandas.isna(row['all_outcomes']) else row['all_outcomes'],
    'narrative': 'Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur? At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere',
    'all_suspect_product_names': row['all_suspect_product_names'],
    'all_concomitants': None if pandas.isna(row['all_concomitants']) else row['all_concomitants'],
    'product_1_product_name': row['all_suspect_product_names'].split(':')[0],
    'pt_term_event_1': row['all_pts'].split(':')[0],
  }
  columns = list(to_insert.keys())
  columns_string = ','.join(columns)
  placeholders = ','.join(['%s'] * len(columns))

  query = 'INSERT INTO faers_case_details (' + columns_string + ') VALUES (' + placeholders + ')'

  params = tuple(to_insert.values())

  print(columns)
  print(params)

  cursor.execute(query, params)
  connection.commit()
  print('inserted row')




# query = 'DESC faers_case_details'

# connection = db_util.get_connection()
# cursor = connection.cursor()
# cursor.execute(query)

# processed = [column[0] for column in cursor.fetchall()]

# print(processed)

# for i in range(100):

#   case_id = 
