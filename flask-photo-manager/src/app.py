from flask import Flask, render_template, request, redirect, url_for
import os
from .photo_manager import PhotoManager  # Use relative import
from config import Config  # Import the Config class

app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from the Config class

photo_directory = app.config['PHOTO_DIRECTORY']  # Access the photo directory from config
photo_manager = PhotoManager(photo_directory)

@app.route('/')
def index():
    photo = photo_manager.get_next_photo()
    return render_template('photo.html', photo=photo)

@app.route('/delete/<filename>', methods=['POST'])
def delete_photo(filename):
    photo_manager.delete_photo(filename)
    return redirect(url_for('index'))

@app.route('/rename/<filename>', methods=['POST'])
def rename_photo(filename):
    new_name = request.form.get('new_name')
    photo_manager.rename_photo(filename, new_name)
    return redirect(url_for('index'))

@app.route('/move/<filename>', methods=['POST'])
def move_photo(filename):
    new_directory = request.form.get('new_directory')
    photo_manager.move_photo(filename, new_directory)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], port=app.config['PORT'])  # Read port from config