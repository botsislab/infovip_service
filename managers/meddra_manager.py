import db_util

def get_meddra_pts():
  query = 'SELECT * FROM meddra_pt'
  return db_util.get_all_as_dicts(query)

def get_meddra_hlts():
  query = 'SELECT * FROM meddra_hlt'
  return db_util.get_all_as_dicts(query)

def get_related_pts(unique_pts):
    related_pts = dict()

    if len(unique_pts) == 0:
        return related_pts

    query = 'SELECT hlt, pts FROM meddra_related_pts WHERE pts LIKE \'%' + '%\'\n OR pts LIKE \'%'.join(unique_pts) + '%\''

    print(query)
    
    related_pts_rows = db_util.get_all_as_dicts(query)

    for row in related_pts_rows:
        related_pts[row['hlt']] = row['pts'].split(';')
    
    return related_pts

def get_unique_pts(features):
    unique_pts = set()
    for feature in features:
        if feature['preferred_term'] == '': continue
        for pt in feature['preferred_term'].split(';'):
            unique_pts.add(pt.lower())
    
    return tuple(unique_pts)