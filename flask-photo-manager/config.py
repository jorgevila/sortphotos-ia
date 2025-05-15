import os

class Config:
    # General Config
    DEBUG = True  # Enable debugging

    # App configurations
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'  # for session security

    # Photo directory (where your photos are stored)
    PHOTO_DIRECTORY = os.environ.get('PHOTO_DIRECTORY') or '/path/to/your/photos'

    # Port configuration
    PORT = int(os.environ.get('PORT', 5000))  # Default port is 5000

    # Other configurations can be added here

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}