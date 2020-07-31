import os

def save_uploaded_file(uploaded_file, filename):
    # Make sure temporary directory exists
    if not os.path.exists(get_temp_directory_name()):
        os.makedirs(get_temp_directory_name())

    # Store uploaded file in temporary location
    uploaded_file.save(get_full_path(filename))

def delete(filename):
    path = get_full_path(filename)
    if os.path.exists(path):
        print('Deleting temporary file %s' % path)
        os.remove(path)

def get_temp_directory_name():
    return 'temp'

def get_full_path(filename):
    return get_temp_directory_name() + '/' + filename