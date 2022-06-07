# Utilities Module

import hashlib

# SHA-2 Hash
def hash(id: str):
    hash_function = hashlib.sha256()
    hash_function.update(id)
    hash_result = hash_function.hexdigest()
    return hash_result