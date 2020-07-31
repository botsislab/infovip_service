import xlrd

def get_case_list(path):
    """
    Get case ids from excel file
    """
    book = xlrd.open_workbook(path)

    case_details_sheet_name = 'Case Details'
    sheet = None

    # Get Case Details sheet
    if case_details_sheet_name in book.sheet_names():
        sheet = book.sheet_by_name('Case Details')
    else:
        print('Couldn\'t find sheet: ' + case_details_sheet_name + ' assuming case details are in the first sheet...')
        sheet = book.sheet_by_index(0)

    case_ids = []

    # Print out the first column, ignoring the header cell
    for cell in sheet.col(0)[1:]:
        if isinstance(cell.value, float):
            case_ids.append(str(int(cell.value)))
        else:
            case_ids.append(cell.value)
    
    return case_ids

def parse(path):
    """
    Get headers and list of tuples from excel file
    """

    book = xlrd.open_workbook(path)

    case_details_sheet_name = 'Case Details'
    sheet = None

    # Get Case Details Sheet
    if case_details_sheet_name in book.sheet_names():
        sheet = book.sheet_by_name('Case Details')
    else:
        print('Couldn\'t find sheet: ' + case_details_sheet_name + ' assuming case details are in the first sheet...')
        sheet = book.sheet_by_index(0)

    # Assume first row is the header
    # headers = 
    case_ids = []

    # Print out the first column, ignoring the header cell
    for cell in sheet.col(0)[1:]:
        if isinstance(cell.value, float):
            case_ids.append(str(int(cell.value)))
        else:
            case_ids.append(cell.value)
    
    return case_ids