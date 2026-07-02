import zipfile
import os
import shutil

zip_path = "master.zip"
extract_path = "temp_extract"
target_dir = "frontend/public/shizuku"

print("Extracting...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)
    
print("Copying Shizuku model to public directory...")
source_dir = os.path.join(extract_path, "pixi-live2d-display-master", "test", "assets", "shizuku")

if os.path.exists(target_dir):
    shutil.rmtree(target_dir)
    
shutil.copytree(source_dir, target_dir)
print(f"Successfully installed Shizuku to {target_dir}!")

# Cleanup
if os.path.exists(zip_path):
    os.remove(zip_path)
if os.path.exists(extract_path):
    shutil.rmtree(extract_path)
