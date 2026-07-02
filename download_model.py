import urllib.request
import zipfile
import os
import shutil

url = "https://github.com/guansss/pixi-live2d-display/archive/refs/heads/master.zip"
zip_path = "master.zip"
extract_path = "temp_extract"
target_dir = "frontend/public/shizuku"

print("Downloading Live2D models...")
try:
    urllib.request.urlretrieve(url, zip_path)
    print("Download complete. Extracting...")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        
    print("Extracted. Copying Shizuku model to public directory...")
    # The path inside the zip
    source_dir = os.path.join(extract_path, "pixi-live2d-display-master", "playground", "assets", "shizuku")
    
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
        
    shutil.copytree(source_dir, target_dir)
    print(f"Successfully installed Shizuku to {target_dir}!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    # Cleanup
    if os.path.exists(zip_path):
        os.remove(zip_path)
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
