from scrapers.scraper import Video
from bs4 import BeautifulSoup
from os import path, makedirs
import urllib.request
import requests
import json


class FreeOnesVideo(Video):
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
            print("Processing video")
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

        # Video
        scripts = soup.findAll('script', type='application/ld+json')
        for s in scripts:
            data = json.loads(s.text)
            if data['@type'] == "VideoObject":
                self.source_url = data["contentUrl"]
        self.loaded = True

    def meta(self):
        # Load metadata if needed
        if not self.loaded:
            self.load()

        return self.metadata

    def data(self):
        # Load if needed
        if not self.loaded:
            self.load()

        return requests.get(self.source_url).text

    def download(self):
        # Load if needed
        if not self.loaded:
            self.load()

        last_slug = self.slug.split('/')[-1]
        videos_path = f"./babes/{self.target}/videos"
        makedirs(videos_path, exist_ok=True)
        target_file = f"{videos_path}/{last_slug}.mp4"
        if not path.exists(target_file):
            try:
                urllib.request.urlretrieve(self.source_url, target_file)
                if self.log:
                    print("Video downloaded")
            except:
                if self.log:
                    print(f"Download failed for {self.source_url}")
