import os
from PIL import Image
import random

# Define the folder where images will be saved
output_folder = 'generated_images'
os.makedirs(output_folder, exist_ok=True)

# Generate 5,000 images
num_images = 5000
for i in range(num_images):
    # Create a new image with random colors
    img = Image.new('RGB', (100, 100), color=(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    ))
    
    # Define the file path
    img_path = os.path.join(output_folder, f'image_{i+1}.jpg')
    
    # Save the image as JPEG
    img.save(img_path, 'JPEG')

print(f'{num_images} images have been generated in the folder "{output_folder}".')
