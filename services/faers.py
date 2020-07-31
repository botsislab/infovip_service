from flask import Blueprint, jsonify, request, session
from managers import mock_faers_manager
import json

faers_api = Blueprint('faers_api', __name__)

def require_login():
    if 'username' not in session:
        abort(401)

@faers_api.route('/products')
def get_products():
    require_login()
    products = mock_faers_manager.get_products()
    return jsonify(products)

@faers_api.route('/product_autocomplete_search')
def product_autocomplete_search():
  query = request.args.get('query')
  if query:
    products = mock_faers_manager.get_products()
    filtered_products = list(filter(lambda product_name: query.lower() in product_name.lower(), products))
    results = [{
      'text': product,
      'value': product
    } for product in filtered_products]
    return jsonify(results)
  else:
    return jsonify({
      'message': 'The parameter \'query\' must be provided'
    }), 400

@faers_api.route('/faers_report_query', methods = ['POST'])
def faers_report_query():
  query_data = request.get_json()

  print(query_data)

  products = query_data['products'] if 'products' in query_data else ()
  hlts = query_data['hlts'] if 'hlts' in query_data else ()
  pts = query_data['pts'] if 'pts' in query_data else ()

  if len(products) == 0:
    return jsonify({
      'message': 'The query must include at least one Product'
    }), 400

  reports = mock_faers_manager.faers_report_query(products, hlts, pts)

  response = {
    'reports': reports,
    'duplicates': mock_faers_manager.get_duplicate_groups(reports)
  }

  return jsonify(response)