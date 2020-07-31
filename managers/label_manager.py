from managers import meddra_manager
import db_util

def get_case_labels(case_id):

    labels_markup = []

    # Get labels for case_id
    labels = get_labels(case_id)

    # For each label
    for label in labels:

        # Get label sections
        label_sections = get_label_sections(label['label_id'])

        # Get label section features
        label_features = get_label_features(label['label_id'])

        # Construct markup
        label_markup = get_label_markup(label, label_sections, label_features)

        # Add PTs related by HLT
        unique_pts = meddra_manager.get_unique_pts(label_features)
        label_markup['related_pts'] = meddra_manager.get_related_pts(unique_pts)

        # Add to array of labels
        labels_markup.append(label_markup)

    return labels_markup

def get_labels(case_id):

    query = '''
        SELECT faers_case_products.case_id, faers_case_products.product_name, label_id_lookup.package_title, label_id_lookup.set_id, label_id_lookup.version_number, label_id_lookup.label_id FROM faers_case_products
        # SELECT label_id_lookup.label_id FROM faers_case_products
        # https://stackoverflow.com/questions/5657446/mysql-query-max-group-by
        LEFT JOIN (
            SELECT dailymed_labels.label_id, dailymed_labels.version_number, dailymed_labels.set_id, dailymed_labels.package_title
            FROM dailymed_labels
            INNER JOIN (
                SELECT set_id, max(version_number) as version
                FROM dailymed_labels
                GROUP BY set_id
            ) max_versions
            ON (dailymed_labels.set_id = max_versions.set_id and dailymed_labels.version_number = max_versions.version)
        ) as label_id_lookup ON faers_case_products.best_set_id = label_id_lookup.set_id
        WHERE faers_case_products.best_set_id IS NOT NULL
        AND case_id = %s'''

    return db_util.get_all_as_dicts(query, (case_id,))

def get_label_sections(label_id):

    return db_util.get_all_as_dicts('''
        SELECT * FROM dailymed_label_sections
        WHERE label_id = %s
    ''', (label_id,))

def get_label_features(label_id):

    return db_util.get_all_as_dicts('''
        SELECT section_id, subsection_id, start_position, end_position, preferred_term
        FROM ether_dailymed_label_features
        WHERE label_id = %s
        ORDER BY section_id, subsection_id, start_position
    ''', (label_id,))

def get_label_markup(label, label_sections, label_features):

    label_markup = []

    # For each label section
    for label_section in label_sections:
        
        # Get features for section
        section_id = label_section['section_id']
        subsection_id = label_section['subsection_id']
        section_features = get_section_features(section_id, subsection_id, label_features)

        # If first subsection, use section title/text
        if subsection_id == 0:

            label_markup.append({
                'title': label_section['section_title'],
                'section_id': label_section['section_id'],
                'subsection_id': label_section['subsection_id'],
                'markup': get_section_markup(label_section['section_text'], section_features)
            })

        # Otherwise, use subsection title/text
        else:

            label_markup.append({
                'title': label_section['subsection_title'],
                'section_id': label_section['section_id'],
                'subsection_id': label_section['subsection_id'],
                'markup': get_section_markup(label_section['subsection_text'], section_features)
            })

    return {
        'label_id': label['label_id'],
        'set_id': label['set_id'],
        'product_name': label['product_name'],
        'package_title': label['package_title'],
        'sections': label_markup
    }

def get_section_features(section_id, subsection_id, label_features):
    return [label_feature for label_feature in label_features if label_feature['section_id'] == section_id and label_feature['subsection_id'] == subsection_id]

def get_section_markup(section_text, section_features):

    section_markup = []

    # Return single item if no features TODO Include these but ignore them in the UI?
    if not section_features:
        section_markup.append({
            'type': 'none',
            'text': section_text
        })
    else:

        next_position = 0
        
        # For each feature
        for feature in section_features:

            # Ignore any duplicate features (can happen when there are multiple times referenced for a single bit of text)
            if feature['start_position'] < next_position:
                continue

            # Add psuedo feature before this one if necessary
            if feature['start_position'] != next_position:
                section_markup.append({
                    'type': 'none',
                    'text': section_text[next_position:feature['start_position']],
                    'pt': None
                })

            section_markup.append({
                'type': feature['feature_type'] if 'feature_type' in feature else 'other_term',
                'feature_temp_start': feature['feature_temp_start'] if 'feature_temp_start' in feature else None,
                'feature_id': feature['feature_id'] if 'feature_id' in feature else None,
                'text': section_text[feature['start_position']:feature['end_position']],
                'start_position': feature['start_position'],
                'pt': feature['preferred_term']
            })

            next_position = feature['end_position'] + 1

        # Add any remaining text
        if len(section_text) >= next_position:
            section_markup.append({
                'type': 'none',
                'text': section_text[next_position:],
                'pt': None
            })

    return section_markup