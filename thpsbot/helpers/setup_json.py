import os
import shutil


def setup_json():
    json_dir = "json/"
    os.makedirs(json_dir, exist_ok=True)

    for file in os.listdir(".json/"):
        og_path = ".json/" + file
        file_path = json_dir + file
        if not os.path.exists(file_path):
            shutil.copy2(og_path, file_path)
