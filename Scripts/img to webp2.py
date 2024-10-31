from flask import Flask, request, send_file, render_template_string
from PIL import Image
import io
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# HTML template with enhanced CSS
html_template = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image to WebP Converter</title>
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
    <h2>Convert Images to WebP</h2>
    <div class="upload-container">
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="files" accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff,.gif,.raw" multiple required>
            <button type="submit">Convert</button>
        </form>
    </div>
</body>
</html>
"""

def convert_to_webp(file):
    """Convert an image file to WebP format in memory."""
    img = Image.open(file.stream).convert("RGB")
    webp_io = io.BytesIO()
    img.save(webp_io, "webp")
    webp_io.seek(0)
    return webp_io.getvalue(), file.filename

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('files')
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif', '.raw'}

        if not files or not any(file.filename.lower().endswith(tuple(valid_extensions)) for file in files):
            return "Please upload at least one valid image file."

        # Create an in-memory ZIP file
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            # Process files in parallel
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(convert_to_webp, file) for file in files if file.filename.lower().endswith(tuple(valid_extensions))]
                for future in futures:
                    webp_data, original_filename = future.result()
                    # Add each converted image to the ZIP file with .webp extension
                    zip_file.writestr(f"{original_filename.rsplit('.', 1)[0]}.webp", webp_data)

        zip_io.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        zip_filename = f"converted_images_{timestamp}.zip"

        # Send the ZIP file as a download
        return send_file(zip_io, mimetype="application/zip", download_name=zip_filename)

    return render_template_string(html_template)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
