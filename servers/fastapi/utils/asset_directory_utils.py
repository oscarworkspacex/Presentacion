import os
from utils.get_env import get_app_data_directory_env

PLACEHOLDER_IMAGE_URL = "/static/images/placeholder.jpg"


def get_images_directory():
    images_directory = os.path.join(get_app_data_directory_env(), "images")
    os.makedirs(images_directory, exist_ok=True)
    return images_directory


def get_exports_directory():
    export_directory = os.path.join(get_app_data_directory_env(), "exports")
    os.makedirs(export_directory, exist_ok=True)
    return export_directory

def get_uploads_directory():
    uploads_directory = os.path.join(get_app_data_directory_env(), "uploads")
    os.makedirs(uploads_directory, exist_ok=True)
    return uploads_directory


def to_image_web_url(path: str) -> str:
    """Convert a filesystem or remote path to a browser-servable URL."""
    if not path:
        return PLACEHOLDER_IMAGE_URL

    if path.startswith("http://") or path.startswith("https://"):
        return path

    if path.startswith("/app_data/") or path.startswith("/static/"):
        return path

    app_data_dir = get_app_data_directory_env() or ""
    normalized_path = os.path.normpath(path)
    normalized_app_data = os.path.normpath(app_data_dir) if app_data_dir else ""

    if normalized_app_data and normalized_path.startswith(normalized_app_data):
        relative_path = normalized_path[len(normalized_app_data) :].lstrip(os.sep)
        return f"/app_data/{relative_path.replace(os.sep, '/')}"

    images_directory = get_images_directory()
    normalized_images = os.path.normpath(images_directory)
    if normalized_path.startswith(normalized_images):
        relative_path = normalized_path[len(normalized_images) :].lstrip(os.sep)
        return f"/app_data/images/{relative_path.replace(os.sep, '/')}"

    return path
