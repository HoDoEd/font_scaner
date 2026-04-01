import hashlib

def calculate_sha256(file_content: bytes) -> str:
    """Вычислить SHA256 хеш файла"""
    return hashlib.sha256(file_content).hexdigest()

def calculate_font_hash(file_content: bytes) -> dict:
    """Вычислить хеши для шрифта"""
    return {
        "sha256": calculate_sha256(file_content),
        "size": len(file_content)
    }