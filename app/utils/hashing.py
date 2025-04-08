import hashlib

def get_file_hash(content: str):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
