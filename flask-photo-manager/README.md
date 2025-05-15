# Flask Photo Manager

Flask Photo Manager is a web application that allows users to view photos from a specified directory and provides options to delete, rename, move the photo to another directory, or proceed to the next photo.

## Project Structure

```
flask-photo-manager
├── src
│   ├── static
│   │   └── css
│   │       └── style.css
│   ├── templates
│   │   ├── base.html
│   │   └── photo.html
│   ├── __init__.py
│   ├── app.py
│   └── photo_manager.py
├── config.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd flask-photo-manager
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application by editing `config.py` to set the desired upload folder and allowed file types.

## Usage

1. Run the application:
   ```
   python src/app.py
   ```

2. Open your web browser and navigate to `http://127.0.0.1:5000`.

3. Use the interface to view photos and manage them as needed.

## Features

- View photos from a specified directory.
- Options to delete, rename, or move photos.
- Navigate to the next photo in the directory.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.