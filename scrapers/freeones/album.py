from scrapers.scraper import PhotoAlbum
from bs4 import BeautifulSoup
from os import path, makedirs
from urllib.parse import urlparse
import urllib.request
import requests


class FreeOnesAlbum(PhotoAlbum):
    base_url = ""
    slug = ""
    target = ""

    def __init__(self, write_log):
        super().__init__(write_log)
        self.base_url = "https://www.freeones.com"

    def init(self, slug, title, target):
        self.slug = slug
        self.target = target
        self.url = f"{self.base_url}{slug}"
        self.metadata = {
            'url': self.url,
            'title': title,
            'upload_date': "",
            'performers': []
        }

    def load(self):
        if self.log:
            print("Processing album")
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, "html.parser")

        # Metadata
        date_box = soup.find("div", class_="uploaded-date")
        if date_box:
            date = date_box.text
            if date:
                self.metadata['upload_date'] = date
        cast_boxes = soup.findAll("div", class_="cast")
        if cast_boxes:
            for box in cast_boxes:
                actor = box.find("a")
                if actor:
                    self.metadata['performers'].append((actor.text.strip(), actor['href'][:-4].strip('/')))

        # Pictures
        self.pictures = []
        picture_links = soup.find_all("a", class_="gallery__flex__link", attrs={"data-type": "photo"})
        for link in picture_links:
            self.pictures.append(link['href'])
        self.loaded = True
        if self.log:
            print(f" done, found {len(self.pictures)} pictures")

    def meta(self):
        # Load metadata if needed
        if not self.loaded:
            self.load()

        return self.metadata

    def download(self, picture_url):
        last_slug = self.slug.split('/')[-1]
        album_path = f"./babes/{self.target}/photos/{last_slug}"
        makedirs(album_path, exist_ok=True)
        parsed_url = urlparse(picture_url)
        target_file = f"{album_path}/{path.basename(parsed_url.path)}"
        if not path.exists(target_file):
            try:
                urllib.request.urlretrieve(picture_url, target_file)
            except:
                if self.log:
                    print(f"Download failed for {picture_url}")
        if self.log:
            print("Picture downloaded")

    def next_photo(self, data=False, download=False):
        # Load pictures if needed
        if not self.loaded:
            self.load()

        # Out of pictures
        if len(self.pictures) < 1:
            return None

        # Get URL of next picture
        picture_url = self.pictures.pop(0)

        # Download if requested
        if download:
            self.download(picture_url)

        # Return next photo
        if data:
            return requests.get(picture_url).text
        else:
            return picture_url
