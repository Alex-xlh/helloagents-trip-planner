import urllib.request
import zipfile
import os

url = "https://github.com/guansss/pixi-live2d-display/archive/refs/heads/master.zip"
zip_path = "master.zip"

print("Downloading...")
urllib.request.urlretrieve(url, zip_path)
print("Download complete. Reading zip...")

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    for name in zip_ref.namelist():
        if 'shizuku' in name:
            print(name)

os.remove(zip_path)
