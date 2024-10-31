from flask import Flask, request, send_file, render_template_string
from PIL import Image
import io
import zipfile
import os
from datetime import datetime

app = Flask(__name__)

# HTML template with enhanced CSS
html_template = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JPG to WebP Converter</title>
    <style>
        body {
            background-color: #f8f1f6;
            font-family: Arial, sans-serif;
            color: #333;
            text-align: center;
        }
        h2 {
            color: #e91e63;
            font-size: 2em;
        }
        .upload-container {
            max-width: 500px;
            margin: 20px auto;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
        }
        .upload-container input[type="file"] {
            margin-top: 20px;
            padding: 10px;
            width: 100%;
            background-color: #ffffff;
            border: 2px solid #e91e63;
            border-radius: 5px;
        }
        .upload-container button {
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #e91e63;
            color: #fff;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .upload-container button:hover {
            background-color: #c2185b;
        }
    </style>
</head>
<body>
    <h2>Convert JPG to WebP</h2>
    <div class="upload-container">
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="files" accept=".jpg" multiple required>
            <button type="submit">Convert</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('files')

        if not files or not any(file.filename.lower().endswith('.jpg') for file in files):
            return "Please upload at least one JPG file."

            # Create an in-memory ZIP file
            zip_io = io.BytesIO()
            with zipfile.ZipFile(zip_io, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                for file in files:
                    if file.filename.lower().endswith('.jpg'):
                        img = Image.open(file.stream)
                        webp_io = io.BytesIO()
                        img.save(webp_io, 'webp')
                        webp_io.seek(0)
                        # Add each converted image to the ZIP file
                        zip_file.writestr(f"{os.path.splitext(file.filename)[0]}.webp", webp_io.getvalue())
    
            zip_io.seek(0)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            zip_filename = f"converted_images_{timestamp}.zip"
    
            # Send the ZIP file as a download
            return send_file(zip_io, mimetype="application/zip", download_name=zip_filename)
        
        return render_template_string(html_template)
    
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000, debug=True)