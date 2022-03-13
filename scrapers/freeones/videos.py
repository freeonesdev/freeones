from scrapers.scraper import Video
from datetime import datetime, date
from bs4 import BeautifulSoup
from os import path, makedirs
import urllib.request
import requests
import logging
import json


class FreeOnesVideo(Video):
    base_url = "https://www.freeones.com"
    slug = ""
    target = ""

    def json_serial(self,obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError ("Type %s not serializable" % type(obj))

    def __init__(self, slug=None, title="", target=None):
        super().__init__()

        self.slug = slug
        self.target = target
        self.url = f"{self.base_url}{slug}"
        self.metadata = {
            'url': self.url,
            'title': title,
            'source': None,
            'upload_date': None,
            'performers': []
        }

    def load(self):
        logging.debug("Processing video")
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, "html.parser")

        # Metadata
        date_box = soup.find("div", class_="uploaded-date")
        if date_box:
            date = date_box.text
            if date:
                self.metadata['upload_date'] = datetime.strptime(date, "on %B %d, %Y")
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
                self.metadata['source'] = self.source_url
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

    def download(self, download=False, metadata=False):
        # Load if needed
        if not self.loaded:
            self.load()

        last_slug = self.slug.split('/')[-1]
        videos_path = f"./babes/{self.target}/videos"
        makedirs(videos_path, exist_ok=True)
        json_file = f"{videos_path}/{last_slug}.json"
        target_file = f"{videos_path}/{last_slug}.mp4"

        if metadata and not path.exists(json_file):
            if not path.exists(json_file):
                with open(json_file,'w') as fh:
                    fh.write(json.dumps(self.metadata,default=self.json_serial))
                    fh.write("\n")
                logging.debug(f"Metadata downloaded ({json_file})")
  
        if download and not path.exists(target_file):
            try:
                urllib.request.urlretrieve(self.source_url, target_file)
                logging.info(f"Video downloaded: {self.source_url} -> {target_file}")
            except:
                logging.error(f"Download failed for {self.source_url}")
