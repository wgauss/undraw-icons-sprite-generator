#!/usr/bin/env python3

import time
import os
import json
import requests
import shutil
from multiprocessing.pool import ThreadPool

def build_index():
    page = 1
    URLs = []

    while True:
        res = requests.get(f"https://undraw.co/api/illustrations?page={page}")
        json_body = res.json()

        for item in json_body['illos']:
            title = item['title']
            url = item['image']
            print(f"Title: {title} => URL: {url}")
            URLs.append([title, url])

        page = json_body['nextPage']
        print(f"Proceeding to Page {page}")

        if not json_body['hasMore']:
            print("Finished Gathering JSON.")
            return URLs

def download_from_entry(entry):
    title, url = entry
    file_name = f"{title.lower().replace(' ', '_')}.svg"
    print(f"Downloading {file_name}")

    os.makedirs('./temporarySvg', exist_ok=True)

    path = f"./temporarySvg/{file_name}"
    if not os.path.exists(path):
        for attempt in range(3):  # Retry up to 3 times
            try:
                res = requests.get(url, stream=True)
                res.raise_for_status()  # Raise an error for bad responses
                with open(path, 'wb') as f:
                    for chunk in res.iter_content(1024):
                        f.write(chunk)
                
                # Verify that the file was downloaded
                if os.path.exists(path):
                    print(f"Successfully downloaded {file_name}")
                else:
                    print(f"Failed to download {file_name} after writing.")

                return file_name
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {file_name}: {e}")
                time.sleep(2)  # Wait before retrying
                if attempt == 2:  # If it's the last attempt, log a message
                    print(f"Failed to download {file_name} after 3 attempts.")

    return file_name  # Return the file name for further checks

def generate_sprite():
    sprite_path = 'src/assets/svg/undraw-icons.svg'
    os.makedirs(os.path.dirname(sprite_path), exist_ok=True)

    with open(sprite_path, 'w') as sprite_file:
        sprite_file.write('<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n')

        for svg_file in os.listdir('./temporarySvg'):
            if svg_file.endswith('.svg'):
                file_path = f"./temporarySvg/{svg_file}"
                with open(file_path, 'r') as f:
                    svg_content = f.read()
                    # Replace underscores with hyphens for the ID
                    file_id = svg_file[:-4].replace('_', '-')
                    svg_content = svg_content.replace('<svg', f'<symbol id="{file_id}"')
                    svg_content = svg_content.replace('</svg>', '</symbol>')
                    sprite_file.write(svg_content)

        sprite_file.write('</svg>\n')

    print(f"Generated sprite at {sprite_path}")


def clean_up():
    if os.path.exists('./temporarySvg'):
        shutil.rmtree('./temporarySvg')
        print("Cleaned up temporarySvg directory.")

if __name__ == "__main__":
    urls = build_index()
    print(f"Downloading {len(urls)} files.")
    
    with ThreadPool(20) as pool:
        results = pool.imap_unordered(download_from_entry, urls)
        for path in results:
            if path:
                print(f"Downloaded {path}")

    print(f"Downloaded {len(urls)} files.")

    generate_sprite()
    clean_up()

