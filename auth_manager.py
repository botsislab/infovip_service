from passlib.hash import sha256_crypt
import db_util

def authenticate(username, password):
    user = db_util.get_one_as_dict('SELECT password_hash FROM users WHERE username = %s', (username,))

    if user is None:
      return False
    else:
      password_hash = user['password_hash']
      return sha256_crypt.verify(password, password_hash)