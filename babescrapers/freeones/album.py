from babescrapers.scraper import PhotoAlbum
from babescrapers.utils import json_serial
from bs4 import BeautifulSoup
from os import path, makedirs
from urllib.parse import urlparse
from datetime import datetime
import urllib.request
import requests
import logging
import json


class FreeOnesAlbum(PhotoAlbum):
    base_url = 'https://www.freeones.com'
    slug = ''
    target = ''

    def __init__(self, slug=None, title='', target=None):
        super().__init__()

        self.slug = slug
        self.target = target
        self.url = f"{self.base_url}{slug}"
        self.metadata = {
            'url': self.url,
            'title': title,
            'upload_date': None,
            'performers': []
        }

    def load(self):
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, 'html.parser')

        # Metadata
        date_box = soup.find('div', class_='uploaded-date')
        if date_box:
            date = date_box.text
            if date:
                self.metadata['upload_date'] = datetime.strptime(date, 'on %B %d, %Y')
        cast_boxes = soup.find_all('div', class_='cast')
        if cast_boxes:
            for box in cast_boxes:
                actor = box.find('a')
                if actor:
                    self.metadata['performers'].append((actor.text.strip(), actor['href'][:-4].strip('/')))

        # Pictures
        self.pictures = []
        picture_links = soup.find_all('a', class_='gallery__flex__link', attrs={'data-type': 'photo'})
        for link in picture_links:
            self.pictures.append(link['href'])
        self.loaded = True
        logging.info(f"Album processed, found {len(self.pictures)} pictures")

    def meta(self):
        # Load metadata if needed
        if not self.loaded:
            self.load()

        return self.metadata

    def download(self, picture_url, download=False, metadata=False):
        last_slug = self.slug.split('/')[-1]
        base_path = f"./babes/{self.target}/photos"
        album_path = f"./babes/{self.target}/photos/{last_slug}"

        if metadata:
            makedirs(base_path, exist_ok=True)
            json_path = album_path + '.json'
            if not path.exists(json_path):
                with open(json_path, 'w') as fh:
                    fh.write(json.dumps(self.metadata, default=json_serial))
                    fh.write("\n")
                logging.debug(f"Metadata downloaded ({json_path})")
        if download:
            makedirs(album_path, exist_ok=True)
            parsed_url = urlparse(picture_url)
            target_file = f"{album_path}/{path.basename(parsed_url.path)}"
            if not path.exists(target_file):
                try:
                    urllib.request.urlretrieve(picture_url, target_file)
                except:
                    logging.error(f"Download failed for {picture_url}")
            logging.debug(f"Picture downloaded ({picture_url})")

    def next_photo(self, data=False, download=False, metadata=True):
        # Load pictures if needed
        if not self.loaded:
            self.load()

        # Out of pictures
        if len(self.pictures) < 1:
            return None

        # Get URL of next picture
        picture_url = self.pictures.pop(0)

        # Download file/metadata as requested
        self.download(picture_url, download=download, metadata=metadata)

        # Return next photo
        if data:
            return requests.get(picture_url).text
        else:
            return picture_url
