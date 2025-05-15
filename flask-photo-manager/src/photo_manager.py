Sure, here's the contents for the file: /flask-photo-manager/flask-photo-manager/src/photo_manager.py

from flask import current_app, request, redirect, url_for, flash
import os
import shutil

def get_next_photo(current_photo, photo_list):
    """Retrieve the next photo in the list."""
    if current_photo in photo_list:
        current_index = photo_list.index(current_photo)
        next_index = (current_index + 1) % len(photo_list)
        return photo_list[next_index]
    return None

def delete_photo(photo_path):
    """Delete the specified photo."""
    try:
        os.remove(photo_path)
        flash('Photo deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting photo: {e}', 'error')

def rename_photo(photo_path, new_name):
    """Rename the specified photo."""
    try:
        directory = os.path.dirname(photo_path)
        new_path = os.path.join(directory, new_name)
        os.rename(photo_path, new_path)
        flash('Photo renamed successfully.', 'success')
    except Exception as e:
        flash(f'Error renaming photo: {e}', 'error')

def move_photo(photo_path, new_directory):
    """Move the specified photo to a new directory."""
    try:
        if not os.path.exists(new_directory):
            os.makedirs(new_directory)
        shutil.move(photo_path, new_directory)
        flash('Photo moved successfully.', 'success')
    except Exception as e:
        flash(f'Error moving photo: {e}', 'error')