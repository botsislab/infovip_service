import xlrd
import re

id_column = 'case_id'

class CaseList:

    selection_criteria = {} # Map from criteria key to value
    case_detail_headers = []
    case_detail_rows = []

    def __init__(self, selection_criteria, case_detail_headers, case_detail_rows):
        self.selection_criteria = selection_criteria
        self.case_detail_headers = case_detail_headers
        self.case_detail_rows = case_detail_rows

    def get_tuples(self):
        return [tuple(row) for row in self.case_detail_rows]

    def get_case_ids(self):
        return [row[self.case_detail_headers.index(id_column)] for row in self.case_detail_rows]

    def get_id_column_name(self):
        return id_column
    
    def get_number_of_cases(self):
        return len(self.case_detail_rows)

def get_text_fields():

    return [
        'faers_case_number',
        'manufacturer_control_number',
        'isr_number',
        'report_type',
        'form_type',
        'sex',
        'race_ethnicity',
        'medical_history',
        'sender_mfr_organization',
        'reporter_organization',
        'reporter_city',
        'reporter_state',
        'country_derived',
        'reporter_qualifications',
        'health_professional',
        'report_source',
        'narrative',
        'all_llts',
        'all_pts',
        'all_hlts',
        'all_hlgts',
        'all_socs',
        'medication_errors_hlgt_pts',
        'all_outcomes',
        'all_suspect_product_names',
        'all_suspect_product_active_ingredients',
        'all_suspect_active_ingredients',
        'all_suspect_verbatim_products',
        'all_concomitants',
    ]

def from_xls(path):

    # Get reference to book
    book = xlrd.open_workbook(path)

    # Get selection criteria from book
    selection_criteria = parse_selection_criteria(book)

    # Get case details from book
    case_detail_rows = parse_case_details(book)

    # Get column names (including case_id we added during parsing)
    column_names = ['case_id'] + list(header_to_column_name.values())

    # Construct and return case list object
    return CaseList(selection_criteria, column_names, case_detail_rows)

def parse_selection_criteria(book):

    selection_criteria = {
        'product': {},
        'event': {},
        'other': {}
    }

    # Get cover page
    cover_page = get_sheet_by_name(book, 'Cover Page', 'selection criteria', 0)

    # For each row in the sheet, populate our map using columns B and C, ignoring empty and certain fields
    to_ignore = ['Selection Criteria', 'Total Number of Cases:', 'Event List', 'Product List', 'Sender Mfr Org List', 'Case Count']

    for row in cover_page.get_rows():
        key_cell = row[1]
        value_cell = row[2]

        if value_cell.value is not '' and key_cell.value is not '' and key_cell.value not in to_ignore:
            if 'Product' in key_cell.value:
                key = re.sub(r':$', '', str(key_cell.value))
                selection_criteria['product'][key] = str(value_cell.value)
            if 'Event' in key_cell.value:
                key = re.sub(r':$', '', str(key_cell.value))
                selection_criteria['event'][key] = str(value_cell.value)
            else:
                key = re.sub(r':$', '', str(key_cell.value))
                selection_criteria['other'][key] = str(value_cell.value)
          
    return selection_criteria

def get_sheet_by_name(book, sheet_name, looking_for, default_page_index):
    sheet = None

    # Get Cover Page Sheet
    if sheet_name in book.sheet_names():
        sheet = book.sheet_by_name(sheet_name)
    else:
        print('Couldn\'t find sheet: ' + sheet_name + ' assuming ' + looking_for + ' is in sheet ' + str(default_page_index+1))
        sheet = book.sheet_by_index(default_page_index)

    return sheet

def parse_case_details(book):

    rows = []

    # Get case details sheet
    case_details_sheet = get_sheet_by_name(book, 'Case Details', 'case details', 3)

    # Check to see which row the header is in, default to the third row
    header_row_index = 2
    if case_details_sheet.cell(0, 0).value == 'FAERS Case #':
        header_row_index = 0

    # Get headers
    parsed_headers = tuple(case_details_sheet.row_values(header_row_index))

    # Get case_id component ids based on the column name list
    column_names = list(header_to_column_name.values())
    case_number_index = column_names.index('faers_case_number')
    version_number_index = column_names.index('version_number')

    for row_index in range(header_row_index + 1, case_details_sheet.nrows):

        parsed_row = []
        
        # For each column in the database table we care about
        for header, column in header_to_column_name.items():

            # Add None if we didn't parse it out of the file's headers
            if header not in parsed_headers:
                parsed_row.append(None)
            else:

                # Get cell info for current header
                cell_index = parsed_headers.index(header)
                cell = case_details_sheet.cell(row_index, cell_index)

                # Insert value into the row using it's associated format
                field_format = column_name_to_format[column]
                parsed_row.append(format_cell_value(book, cell, field_format))

        # Create case_id
        case_number = parsed_row[case_number_index]
        version_number = parsed_row[version_number_index]
        case_id = '%s-%s' % (case_number, version_number)

        rows.append([case_id] + parsed_row)

    return rows

def headers_to_column_names(headers):
    field_names = []

    for header in headers:
        if header in header_to_column_name:
            field_names.append(header_to_column_name[header])
        else:
            field_names.append(header)

    return field_names

def format_cell_value(book, cell, field_format):

    if cell.value == '':
        return None

    if cell.ctype == xlrd.XL_CELL_DATE:
        datetime_parts = xlrd.xldate_as_tuple(cell.value, book.datemode)
        return str(datetime_parts[0]) + '-'+ str(datetime_parts[1]) + '-' + str(datetime_parts[2])

    if field_format == 'string':
        return str(cell.value)
    
    if field_format == 'int':
        return int(cell.value)
    
    if field_format == 'float':
        return float(cell.value)
    
    # If a date is stored as a string in the excel file
    if field_format == 'date':

        # The date format we'll see is MM/DD/YYYY with no padding
        parts = cell.value.split('/')
        return str(parts[2]) + '-' + str(parts[0]) + '-' + str(parts[1])

    # Default to original value and pray
    return cell.value

header_to_column_name = {
   "FAERS Case #": "faers_case_number",
   "Version Number": "version_number",
   "Image Info/Link": "image_link",
   "Attachments Info/Link": "attachments_link",
   "Manufacturer Control #": "manufacturer_control_number",
   "ISR Number(s)": "isr_number",
   "Report Type": "report_type",
   "Form Type": "form_type",
   "Initial FDA received Date": "initial_fda_received_date",
   "Latest FDA Received date": "latest_fda_received_date",
   "Latest MFR Received Date": "latest_mfr_received_date",
   "Data Entry Completion Date": "data_entry_completion_date",
   "Completness Score": "completeness_score",
   "Patient Id": "patient_id",
   "Age in Years": "age_in_years",
   "DOB": "dob",
   "Sex": "sex",
   "Weight (kg)": "weight_kg",
   "Race/Ethnicity": "race_ethnicity",
   "Medical History/Medical History Comments": "medical_history",
   "Sender Mfr. Organization ": "sender_mfr_organization",
   "Reporter Organization": "reporter_organization",
   "Reporter Last Name": "reporter_last_name",
   "Reporter First Name": "reporter_first_name",
   "Reporter City": "reporter_city",
   "Reporter State": "reporter_state",
   "Country Derived": "country_derived",
   "Reporter Qualifications": "reporter_qualifications",
   "Health Professional": "health_professional",
   "Report Source": "report_source",
   "Narrative": "narrative",
   "Case Event Date": "case_event_date",
   "All LLts": "all_llts",
   "All PTs": "all_pts",
   "All HLTs": "all_hlts",
   "All HLGTs": "all_hlgts",
   "All SOCs": "all_socs",
   "Medication Errors HLGT (PTs)": "medication_errors_hlgt_pts",
   "PT Term Event 1": "pt_term_event_1",
   "Start Date Event 1": "start_date_event_1",
   "PT Term Event 2": "pt_term_event_2",
   "Start Date Event 2": "start_date_event_2",
   "PT Term Event 3": "pt_term_event_3",
   "Start Date Event 3": "start_date_event_3",
   "PT Term Event 4": "pt_term_event_4",
   "Start Date Event 4": "start_date_event_4",
   "PT Term Event 5": "pt_term_event_5",
   "Start Date Event 5": "start_date_event_5",
   "PT Term Event 6": "pt_term_event_6",
   "PT Term Event 7": "pt_term_event_7",
   "PT Term Event 8": "pt_term_event_8",
   "PT Term Event 9": "pt_term_event_9",
   "PT Term Event 10": "pt_term_event_10",
   "PT Term Event 11": "pt_term_event_11",
   "PT Term Event 12": "pt_term_event_12",
   "Serious Outcome ?": "serious_outcome",
   "All Outcomes": "all_outcomes",
   "ALL Suspect Product Names": "all_suspect_product_names",
   "ALL Suspect Product Active Ingredients": "all_suspect_product_active_ingredients",
   "ALL Suspect Active Ingredients": "all_suspect_active_ingredients",
   "ALL Suspect Verbatim Products": "all_suspect_verbatim_products",
   "ALL Concomitants": "all_concomitants",
   "Product 1 Product Name": "product_1_product_name",
   "Product 1 Product Active Ingredient": "product_1_product_active_ingredient",
   "Product 1 Reported Verbatim": "product_1_reported_verbatim",
   "Product 1 Compounded Product": "product_1_compounded_product",
   "Product 1 Combination Product": "product_1_combination_product",
   "Product 1 Role": "product_1_role",
   "Product 1 Reason for Use": "product_1_reason_for_use",
   "Product 1 Strength": "product_1_strength",
   "Product 1 Strength (Unit)": "product_1_strength_unit",
   "Product 1 Dose (Amount)": "product_1_dose_amount",
   "Product 1 Dose (Unit)": "product_1_dose_unit",
   "Product 1 Dosage Text": "product_1_dosage_text",
   "Product 1 Dosage Form": "product_1_dosage_form",
   "Product 1 Route": "product_1_route",
   "Product 1 Frequency": "product_1_frequency",
   "Product 1 Dechallenge": "product_1_dechallenge",
   "Product 1 Rechallenge": "product_1_rechallenge",
   "Product 1 Start Date": "product_1_start_date",
   "Product 1 Stop Date": "product_1_stop_date",
   "Product 1 Therapy Duration (Days)": "product_1_therapy_duration_days",
   "Product 1 Therapy Duration (Verbatim)": "product_1_therapy_duration_verbatim",
   "Product 1 Time To Onset (Days)": "product_1_time_to_onset_days",
   "Product 1 Manufacturer": "product_1_manufacturer",
   "Product 1 Application Type": "product_1_application_type",
   "Product 1 Application #": "product_1_application_number",
   "Product 1 NDC #": "product_1_ndc_number",
   "Product 1 Lot #": "product_1_lot_number",
   "Product 2 Product Name": "product_2_product_name",
   "Product 2 Product Active Ingredient": "product_2_product_active_ingredient",
   "Product 2 Reported Verbatim": "product_2_reported_verbatim",
   "Product 2 Compounded Product": "product_2_compounded_product",
   "Product 2 Combination Product": "product_2_combination_product",
   "Product 2 Role": "product_2_role",
   "Product 2 Reason for Use": "product_2_reason_for_use",
   "Product 2 Strength": "product_2_strength",
   "Product 2 Strength (Unit)": "product_2_strength_unit",
   "Product 2 Dose (Amount)": "product_2_dose_amount",
   "Product 2 Dose (Unit)": "product_2_dose_unit",
   "Product 2 Dosage Text": "product_2_dosage_text",
   "Product 2 Dosage Form": "product_2_dosage_form",
   "Product 2 Route": "product_2_route",
   "Product 2 Frequency": "product_2_frequency",
   "Product 2 Dechallenge": "product_2_dechallenge",
   "Product 2 Rechallenge": "product_2_rechallenge",
   "Product 2 Start Date": "product_2_start_date",
   "Product 2 Stop Date": "product_2_stop_date",
   "Product 2 Therapy Duration (Days)": "product_2_therapy_duration_days",
   "Product 2 Therapy Duration (Verbatim)": "product_2_therapy_duration_verbatim",
   "Product 2 Time To Onset (Days)": "product_2_time_to_onset_days",
   "Product 2 Manufacturer": "product_2_manufacturer",
   "Product 2 Application Type": "product_2_application_type",
   "Product 2 Application #": "product_2_application_number",
   "Product 2 NDC #": "product_2_ndc_number",
   "Product 2 LOT #": "product_2_lot_number",
   "Product 3 Product Name": "product_3_product_name",
   "Product 3 Product Active Ingredient": "product_3_product_active_ingredient",
   "Product 3 Reported Verbatim": "product_3_reported_verbatim",
   "Product 3 Compounded Product": "product_3_compounded_product",
   "Product 3 Combination Product": "product_3_combination_product",
   "Product 3 Role": "product_3_role",
   "Product 3 Reason for Use": "product_3_reason_for_use",
   "Product 3 Strength": "product_3_strength",
   "Product 3 Strength (Unit)": "product_3_strength_unit",
   "Product 3 Dose (Amount)": "product_3_dose_amount",
   "Product 3 Dose (Unit)": "product_3_dose_unit",
   "Product 3 Dosage Text": "product_3_dosage_text",
   "Product 3 Dosage Form": "product_3_dosage_form",
   "Product 3 Route": "product_3_route",
   "Product 3 Frequency": "product_3_frequency",
   "Product 3 Dechallenge": "product_3_dechallenge",
   "Product 3 Rechallenge": "product_3_rechallenge",
   "Product 3 Start Date": "product_3_start_date",
   "Product 3 Stop Date": "product_3_stop_date",
   "Product 3 Therapy Duration (Days)": "product_3_therapy_duration_days",
   "Product 3 Therapy Duration (Verbatim)": "product_3_therapy_duration_verbatim",
   "Product 3 Time To Onset (Days)": "product_3_time_to_onset_days",
   "Product 3 Manufacturer": "product_3_manufacturer",
   "Product 3 Application Type": "product_3_application_type",
   "Product 3 Application #": "product_3_application_number",
   "Product 3 NDC #": "product_3_ndc_number",
   "Product 3 LOT #": "product_3_lot_number",
   "Product 4 Product Name": "product_4_product_name",
   "Product 4 Product Active Ingredient": "product_4_product_active_ingredient",
   "Product 4 Reported Verbatim": "product_4_reported_verbatim",
   "Product 4 Compounded Product": "product_4_compounded_product",
   "Product 4 Combination Product": "product_4_combination_product",
   "Product 4 Role": "product_4_role",
   "Product 4 Reason for Use": "product_4_reason_for_use",
   "Product 4 Strength": "product_4_strength",
   "Product 4 Strength (Unit)": "product_4_strength_unit",
   "Product 4 Dose (Amount)": "product_4_dose_amount",
   "Product 4 Dose (Unit)": "product_4_dose_unit",
   "Product 4 Dosage Text": "product_4_dosage_text",
   "Product 4 Dosage Form": "product_4_dosage_form",
   "Product 4 Route": "product_4_route",
   "Product 4 Frequency": "product_4_frequency",
   "Product 4 Dechallenge": "product_4_dechallenge",
   "Product 4 Rechallenge": "product_4_rechallenge",
   "Product 4 Start Date": "product_4_start_date",
   "Product 4 Stop Date": "product_4_stop_date",
   "Product 4 Therapy Duration (Days)": "product_4_therapy_duration_days",
   "Product 4 Therapy Duration (Verbatim)": "product_4_therapy_duration_verbatim",
   "Product 4 Time To Onset (Days)": "product_4_time_to_onset_days",
   "Product 4 Manufacturer": "product_4_manufacturer",
   "Product 4 Application Type": "product_4_application_type",
   "Product 4 Application #": "product_4_application_number",
   "Product 4 NDC #": "product_4_ndc_number",
   "Product 4 LOT #": "product_4_lot_number",
   "Product 5 Product Name": "product_5_product_name",
   "Product 5 Product Active Ingredient": "product_5_product_active_ingredient",
   "Product 5 Reported Verbatim": "product_5_reported_verbatim",
   "Product 5 Compounded Product": "product_5_compounded_product",
   "Product 5 Combination Product": "product_5_combination_product",
   "Product 5 Role": "product_5_role",
   "Product 5 Reason for Use": "product_5_reason_for_use",
   "Product 5 Strength": "product_5_strength",
   "Product 5 Strength (Unit)": "product_5_strength_unit",
   "Product 5 Dose (Amount)": "product_5_dose_amount",
   "Product 5 Dose (Unit)": "product_5_dose_unit",
   "Product 5 Dosage Text": "product_5_dosage_text",
   "Product 5 Dosage Form": "product_5_dosage_form",
   "Product 5 Route": "product_5_route",
   "Product 5 Frequency": "product_5_frequency",
   "Product 5 Dechallenge": "product_5_dechallenge",
   "Product 5 Rechallenge": "product_5_rechallenge",
   "Product 5 Start Date": "product_5_start_date",
   "Product 5 Stop Date": "product_5_stop_date",
   "Product 5 Therapy Duration (Days)": "product_5_therapy_duration_days",
   "Product 5 Therapy Duration (Verbatim)": "product_5_therapy_duration_verbatim",
   "Product 5 Time To Onset (Days)": "product_5_time_to_onset_days",
   "Product 5 Manufacturer": "product_5_manufacturer",
   "Product 5 Application Type": "product_5_application_type",
   "Product 5 Application #": "product_5_application_number",
   "Product 5 NDC #": "product_5_ndc_number",
   "Product 5 LOT #": "product_5_lot_number",
   "Product 6 Product Name": "product_6_product_name",
   "Product 6 Product Active Ingredient": "product_6_product_active_ingredient",
   "Product 7 Product Name": "product_7_product_name",
   "Product 7 Product Active Ingredient": "product_7_product_active_ingredient",
   "Product 8 Product Name": "product_8_product_name",
   "Product 8 Product Active Ingredient": "product_8_product_active_ingredient",
   "Product 9 Product Name": "product_9_product_name",
   "Product 9 Product Active Ingredient": "product_9_product_active_ingredient",
   "Product 10 Product Name": "product_10_product_name",
   "Product 10 Product Active Ingredient": "product_10_product_active_ingredient"
}

column_name_to_format = {
    "faers_case_number" : "int",
    "version_number" : "int",
    "image_link" : "string",
    "attachments_link" : "string",
    "manufacturer_control_number" : "string",
    "isr_number" : "string",
    "report_type" : "string",
    "form_type" : "string",
    "initial_fda_received_date" : "date",
    "latest_fda_received_date" : "date",
    "latest_mfr_received_date" : "date",
    "data_entry_completion_date" : "date",
    "completeness_score": "float",
    "patient_id" : "string",
    "age_in_years" : "float",
    "dob" : "string",
    "sex" : "string",
    "weight_kg" : "string",
    "race_ethnicity" : "string",
    "medical_history" : "string",
    "sender_mfr_organization" : "string",
    "reporter_organization" : "string",
    "reporter_last_name" : "string",
    "reporter_first_name" : "string",
    "reporter_city" : "string",
    "reporter_state" : "string",
    "country_derived" : "string",
    "reporter_qualifications" : "string",
    "health_professional" : "string",
    "report_source" : "string",
    "narrative" : "string",
    "case_event_date" : "string",
    "all_llts" : "string",
    "all_pts" : "string",
    "all_hlts" : "string",
    "all_hlgts" : "string",
    "all_socs" : "string",
    "medication_errors_hlgt_pts" : "string",
    "pt_term_event_1" : "string",
    "start_date_event_1" : "string",
    "pt_term_event_2" : "string",
    "start_date_event_2" : "string",
    "pt_term_event_3" : "string",
    "start_date_event_3" : "string",
    "pt_term_event_4" : "string",
    "start_date_event_4" : "string",
    "pt_term_event_5" : "string",
    "start_date_event_5" : "string",
    "pt_term_event_6" : "string",
    "pt_term_event_7" : "string",
    "pt_term_event_8" : "string",
    "pt_term_event_9" : "string",
    "pt_term_event_10" : "string",
    "pt_term_event_11" : "string",
    "pt_term_event_12" : "string",
    "serious_outcome" : "string",
    "all_outcomes" : "string",
    "all_suspect_product_names" : "string",
    "all_suspect_product_active_ingredients" : "string",
    "all_suspect_active_ingredients" : "string",
    "all_suspect_verbatim_products" : "string",
    "all_concomitants" : "string",
    "product_1_product_name" : "string",
    "product_1_product_active_ingredient" : "string",
    "product_1_reported_verbatim" : "string",
    "product_1_compounded_product" : "string",
    "product_1_combination_product" : "string",
    "product_1_role" : "string",
    "product_1_reason_for_use" : "string",
    "product_1_strength" : "string",
    "product_1_strength_unit" : "string",
    "product_1_dose_amount" : "string",
    "product_1_dose_unit" : "string",
    "product_1_dosage_text" : "string",
    "product_1_dosage_form" : "string",
    "product_1_route" : "string",
    "product_1_frequency" : "string",
    "product_1_dechallenge" : "string",
    "product_1_rechallenge" : "string",
    "product_1_start_date" : "string",
    "product_1_stop_date" : "string",
    "product_1_therapy_duration_days" : "int",
    "product_1_therapy_duration_verbatim" : "string",
    "product_1_time_to_onset_days" : "int",
    "product_1_manufacturer" : "string",
    "product_1_application_type" : "string",
    "product_1_application_number" : "string",
    "product_1_ndc_number" : "string",
    "product_1_lot_number" : "string",
    "product_2_product_name" : "string",
    "product_2_product_active_ingredient" : "string",
    "product_2_reported_verbatim" : "string",
    "product_2_compounded_product" : "string",
    "product_2_combination_product" : "string",
    "product_2_role" : "string",
    "product_2_reason_for_use" : "string",
    "product_2_strength" : "string",
    "product_2_strength_unit" : "string",
    "product_2_dose_amount" : "string",
    "product_2_dose_unit" : "string",
    "product_2_dosage_text" : "string",
    "product_2_dosage_form" : "string",
    "product_2_route" : "string",
    "product_2_frequency" : "string",
    "product_2_dechallenge" : "string",
    "product_2_rechallenge" : "string",
    "product_2_start_date" : "string",
    "product_2_stop_date" : "string",
    "product_2_therapy_duration_days" : "int",
    "product_2_therapy_duration_verbatim" : "string",
    "product_2_time_to_onset_days" : "int",
    "product_2_manufacturer" : "string",
    "product_2_application_type" : "string",
    "product_2_application_number" : "string",
    "product_2_ndc_number" : "string",
    "product_2_lot_number" : "string",
    "product_3_product_name" : "string",
    "product_3_product_active_ingredient" : "string",
    "product_3_reported_verbatim" : "string",
    "product_3_compounded_product" : "string",
    "product_3_combination_product" : "string",
    "product_3_role" : "string",
    "product_3_reason_for_use" : "string",
    "product_3_strength" : "string",
    "product_3_strength_unit" : "string",
    "product_3_dose_amount" : "string",
    "product_3_dose_unit" : "string",
    "product_3_dosage_text" : "string",
    "product_3_dosage_form" : "string",
    "product_3_route" : "string",
    "product_3_frequency" : "string",
    "product_3_dechallenge" : "string",
    "product_3_rechallenge" : "string",
    "product_3_start_date" : "string",
    "product_3_stop_date" : "string",
    "product_3_therapy_duration_days" : "int",
    "product_3_therapy_duration_verbatim" : "string",
    "product_3_time_to_onset_days" : "int",
    "product_3_manufacturer" : "string",
    "product_3_application_type" : "string",
    "product_3_application_number" : "string",
    "product_3_ndc_number" : "string",
    "product_3_lot_number" : "string",
    "product_4_product_name" : "string",
    "product_4_product_active_ingredient" : "string",
    "product_4_reported_verbatim" : "string",
    "product_4_compounded_product" : "string",
    "product_4_combination_product" : "string",
    "product_4_role" : "string",
    "product_4_reason_for_use" : "string",
    "product_4_strength" : "string",
    "product_4_strength_unit" : "string",
    "product_4_dose_amount" : "string",
    "product_4_dose_unit" : "string",
    "product_4_dosage_text" : "string",
    "product_4_dosage_form" : "string",
    "product_4_route" : "string",
    "product_4_frequency" : "string",
    "product_4_dechallenge" : "string",
    "product_4_rechallenge" : "string",
    "product_4_start_date" : "string",
    "product_4_stop_date" : "string",
    "product_4_therapy_duration_days" : "int",
    "product_4_therapy_duration_verbatim" : "string",
    "product_4_time_to_onset_days" : "int",
    "product_4_manufacturer" : "string",
    "product_4_application_type" : "string",
    "product_4_application_number" : "string",
    "product_4_ndc_number" : "string",
    "product_4_lot_number" : "string",
    "product_5_product_name" : "string",
    "product_5_product_active_ingredient" : "string",
    "product_5_reported_verbatim" : "string",
    "product_5_compounded_product" : "string",
    "product_5_combination_product" : "string",
    "product_5_role" : "string",
    "product_5_reason_for_use" : "string",
    "product_5_strength" : "string",
    "product_5_strength_unit" : "string",
    "product_5_dose_amount" : "string",
    "product_5_dose_unit" : "string",
    "product_5_dosage_text" : "string",
    "product_5_dosage_form" : "string",
    "product_5_route" : "string",
    "product_5_frequency" : "string",
    "product_5_dechallenge" : "string",
    "product_5_rechallenge" : "string",
    "product_5_start_date" : "string",
    "product_5_stop_date" : "string",
    "product_5_therapy_duration_days" : "int",
    "product_5_therapy_duration_verbatim" : "string",
    "product_5_time_to_onset_days" : "int",
    "product_5_manufacturer" : "string",
    "product_5_application_type" : "string",
    "product_5_application_number" : "string",
    "product_5_ndc_number" : "string",
    "product_5_lot_number" : "string",
    "product_6_product_name" : "string",
    "product_6_product_active_ingredient" : "string",
    "product_7_product_name" : "string",
    "product_7_product_active_ingredient" : "string",
    "product_8_product_name" : "string",
    "product_8_product_active_ingredient" : "string",
    "product_9_product_name" : "string",
    "product_9_product_active_ingredient" : "string",
    "product_10_product_name" : "string",
    "product_10_product_active_ingredient" : "string",
}