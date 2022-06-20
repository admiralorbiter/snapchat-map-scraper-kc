#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import pathlib
import platform
import select
import shutil
import sqlite3
import subprocess
import sys
import time
import re

import requests

def get_latest_tileset():
    url = 'https://ms.sc-jpl.com/web/getLatestTileSet'
    headers = {
        'content-type': 'application/json'
    }
    resp = requests.post(url, headers=headers, json={})
    resp.raise_for_status()
    return resp.json()

def get_epoch():
    tiles = get_latest_tileset()
    for t in tiles['tileSetInfos']:
        if t['id']['type'] == 'HEAT':
            return int(t['id']['epoch'])
    return 0

def _open_default(filepath: pathlib.Path):
    import subprocess, os, platform
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', str(filepath)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif platform.system() == 'Windows':    # Windows
        os.startfile(str(filepath))
    else:                                   # linux variants
        subprocess.call(('xdg-open', str(filepath)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def download_file(file: pathlib.Path, url: str):
    if file.exists():
        return
    tries = 3
    while tries > 0:
        try:
            with requests.get(url, stream=True) as resp:
                resp.raise_for_status()
                with open(str(file), 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                _open_default(file)
            break
        except (requests.HTTPError, requests.exceptions.ConnectionError):
            if tries == 0:
                raise
            time.sleep(3)
            tries -= 1
        


def download_media(idnum, preview_url, media_url, overlay_url):
    base_folder = pathlib.Path('media')
    if not base_folder.exists():
        base_folder.mkdir(parents=True)
    media_file = None
    preview_file = None
    overlay_file = None

    if media_url:
        media_file = (base_folder / idnum).with_suffix('.mp4')
        download_file(media_file, media_url)

    if preview_url:
        preview_file = (base_folder / idnum).with_suffix('.jpg')
        download_file(preview_file, preview_url)

    if overlay_url:
        overlay_file = (base_folder / (idnum + '_overlay')).with_suffix('.png')
        download_file(overlay_file, overlay_url)

    return (str(preview_file) if preview_file is not None else None,
            str(media_file) if media_file is not None else None,
            str(overlay_file) if overlay_file is not None else None)



epoch = get_epoch()

if epoch == 0:
    print('Error getting latest Snapchat tile data')
    sys.exit(1)

latitude = 39.095250
longitude = -94.576120
location_id = '0'

data = {
    "requestGeoPoint":{
        "lat": latitude,
        "lon": longitude
    },
    "zoomLevel": 16,
    "tileSetId": {
        "flavor": "default",
        "epoch": epoch,
        "type": 1
    },
    #"radiusMeters": 87.96003668860504,
    "radiusMeters": 500.0, # 1 mi
    "maximumFuzzRadius": 0
}

headers = {
    'Content-Type': 'application/json'
}

url = 'https://ms.sc-jpl.com/web/getPlaylist'

tries = 3
resp = None

db_file = pathlib.Path('sql/test.db')

while tries > 0:
    try:
        resp = requests.post(url, json=data, headers=headers)
        resp.raise_for_status()
        break
    except (requests.HTTPError, requests.exceptions.ConnectionError):
        if tries == 0:
            raise
        time.sleep(3)
        tries -= 1
if resp is None:
    print('Error getting response')
    sys.exit(1)

j = resp.json()
new_records = 0
for vid in j['manifest']['elements']:
    idnum = vid['id']
    duration_s = vid.get('duration')
    timestamp = vid.get('timestamp')
    
    info = vid['snapInfo']
    titles = info['title']['strings']
    title = [t['text'] for t in titles if t['locale'] == 'en']
    if title:
        title = title[0]
    else:
        title = info['title'].get('fallback')
    overlay_text = info.get('overlayText')

    media = info.get('streamingMediaInfo')
    preview_url = None
    media_url = None
    overlay_url = None
    if media:
        if media.get('previewUrl'):
            preview_url = media['prefixUrl'] + media['previewUrl']
        if media.get('mediaUrl'):
            media_url = media['prefixUrl'] + media['mediaUrl']
        if media.get('overlayUrl'):
            overlay_url = media['prefixUrl'] + media['overlayUrl']
            if not overlay_url.endswith('png'):
                print(f'Overlay url: {overlay_url}')
    else:
        media = info.get('publicMediaInfo')
        if media:
            preview_url = media['publicImageMediaInfo']['mediaUrl']
        else:
            media = info.get
            print('Unable to get video info')
            print(json.dumps(vid))
            continue
        
    try:
        (preview_path, media_path, overlay_path) = download_media(idnum, preview_url, media_url, overlay_url)
    except requests.HTTPError:
        pass

    with sqlite3.connect(str(db_file)) as conn:
        cur = conn.cursor()
        try:
            sel = cur.execute('SELECT EXISTS(SELECT 1 FROM media WHERE id=?)', (idnum,))
            if sel.fetchone() == (1,):
                continue
            cur.execute('INSERT INTO media '
                '(id, location_id, duration_seconds, timestamp, title, preview_path, media_path, overlay_path, overlay_text) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (idnum, location_id, duration_s, timestamp, title, preview_path, media_path, overlay_path, overlay_text))
            conn.commit()
            new_records += 1
        finally:
            cur.close()
