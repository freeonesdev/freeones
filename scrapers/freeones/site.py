from scrapers.scraper import Scraper
from scrapers.freeones.album import FreeOnesAlbum
from scrapers.freeones.videos import FreeOnesVideo
from datetime import datetime
from lxml import etree
from bs4 import BeautifulSoup
from os import makedirs
import requests
import logging
import json
import yaml
import re


class FreeOnes(Scraper):
    base_url = "https://www.freeones.com"
    out_path = f"./babes"
    album_page = 0
    videos_page = 0

    def __init__(self, write_bio=False):
        super().__init__(write_bio)

        self.babe_path = self.out_path
        self.album_list = []
        self.video_list = []

        logging.info(f"FreeOnes scraper")

    def list_targets(self, page=1):
        babes = []
        list_url = f"{self.base_url}/babes?s=rank.currentRank&o=asc&l=12&p={page}"
        page = requests.get(list_url)
        soup = BeautifulSoup(page.content, "html.parser")
        babes_boxes = soup.findAll("div", {'class': ['grid-item', 'teaser-subject']})
        for box in babes_boxes:
            feed_link = box.find('a', class_="teaser__link")['href']
            feed_parts = feed_link.split('/')
            babes.append(feed_parts[1])

        return babes

    def select_target(self, name):
        super().select_target(name)
        self.babe_path = f"{self.out_path}/{self.target}/"

    def bio(self):
        if self.biography is not None:
            return self.biography

        self.biography = {}
        try:
            with open(r"./CommunityScrapers/scrapers/FreeonesCommunity.yml") as file:
                structure = yaml.load(file, Loader=yaml.FullLoader)
            bio_paths = structure['xPathScrapers']['performerScraper']['performer']
        except IOError as ex:
            logging.error("Structure YAML file not found")
            self.biography = None
            return None

        url = f"{self.base_url}/{self.target}/bio"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        dom = etree.HTML(str(soup))

        for key in bio_paths:
            # Read simple entry
            if type(bio_paths[key]) == str:
                value = dom.xpath(bio_paths[key])

                if type(value) == list:
                    values = []
                    for v in value:
                        if hasattr(v, 'text'):
                            values.append(''.join(t.strip() for t in v.itertext()))
                        else:
                            values.append(v.strip())
                    value = ', '.join(values)
                else:
                    value = ''.join(t.strip() for t in value.itertext())

                if value:
                    self.biography[key.lower()] = value
                continue

            # Entry without selector
            if 'selector' not in bio_paths[key].keys():
                continue

            # Read complex entry
            value = dom.xpath(bio_paths[key]['selector'])
            if type(value) == list:
                if len(value) > 0:
                    # Concatenate from parts
                    if 'concat' in bio_paths[key].keys():
                        parts = []
                        for v in value:
                            parts.append(''.join(t.strip() for t in v.itertext()))
                        value = bio_paths[key]['concat'].join(parts)
                    else:
                        value = value[0]
                else:
                    value = ""
            if hasattr(value, 'text'):
                value = ''.join(t.strip() for t in value.itertext())
            else:
                value = value.strip()

            # Post-processing value
            if 'postProcess' in bio_paths[key].keys():
                post_process = bio_paths[key]['postProcess']
                for process in post_process:
                    # Replace process
                    if 'replace' in process.keys():
                        replaces = process['replace']
                        for step in replaces:
                            replace_with = ""
                            if 'with' in step.keys():
                                replace_with = str(step['with'] or "")
                            value = re.sub(step['regex'], replace_with, value)

                    # Mapping process
                    elif 'map' in process.keys():
                        map_values = process['map']
                        if value in map_values.keys():
                            value = map_values[value].strip()

                    # Parse date process
                    elif 'parseDate' in process.keys():
                        date_input = value.strip()
                        if date_input:
                            value = datetime.strptime(date_input, '%B %d, %Y')
                        else:
                            value = None

            if value:
                self.biography[key.lower()] = value

        # Convert career dates to datetime objects
        if self.biography is not None and 'careerlength' in self.biography.keys():
            career_parts = self.biography['careerlength'].split('-')
            del self.biography['careerlength']
            self.biography['careerStart'] = None
            self.biography['careerEnd'] = None
            if career_parts[0]:
                year = re.search(r'\d+|$', career_parts[0]).group()
                if year:
                    self.biography['careerStart'] = datetime.strptime(f"{year}-01-01", '%Y-%m-%d')
            if career_parts[1]:
                year = re.search(r'\d+|$', career_parts[1]).group()
                if year:
                    self.biography['careerEnd'] = datetime.strptime(f"{year}-01-01", '%Y-%m-%d')

        # Write biography to JSON file
        if self.options['write_bio']:
            makedirs(self.babe_path, exist_ok=True)
            json_path = f"{self.babe_path}bio.json"
            try:
                bio_output = {}
                for key, value in self.biography.items():
                    if isinstance(value, datetime):
                        bio_output[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        bio_output[key] = value
                with open(json_path, 'w') as outfile:
                    json.dump(bio_output, outfile)
                logging.info(f"Biography file written: {json_path}")
            except IOError:
                logging.warning(f"Failed to write biography file: {json_path}")

        return self.biography

    def next_album(self):
        # All album pages already processed
        if self.album_page < 0:
            return None

        # No more album in active page, get next one
        if len(self.album_list) < 1:
            self.album_page += 1
            logging.info(f"Fetching album page {self.album_page}")
            self.album_list = []
            url = f"{self.base_url}/{self.target}/photos?s=subject-latest&l=12&p={self.album_page}"
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            album_links = soup.find_all("a", class_="teaser__link")
            for link in album_links:
                album_slug = link['href']
                album_title = link.find("p", class_="title-clamp").getText().strip()
                album = FreeOnesAlbum(album_slug, album_title, self.target)
                self.album_list.append(album)
            logging.debug(f"Found {len(self.album_list)} albums")

            # Last page of albums is empty, no more albums to fetch
            if len(self.album_list) < 1:
                self.album_page = -1

                return None

        # Next album exists, return it
        if len(self.album_list) > 0:
            return self.album_list.pop(0)

        # Nothing to return
        return None

    def next_video(self):
        # All video pages already processed
        if self.videos_page < 0:
            return None

        # No more pictures in active album, go for next album page
        if len(self.video_list) < 1:
            self.videos_page += 1
            logging.info(f"Fetching videos page {self.videos_page}")
            self.video_list = []
            url = f"{self.base_url}/{self.target}/videos?s=subject-latest&l=12&p={self.videos_page}"
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            video_links = soup.find_all("a", class_="teaser__link")
            for link in video_links:
                video_slug = link['href']
                video_title = link.find("p", class_="title-clamp").getText().strip()
                video = FreeOnesVideo(video_slug, video_title, self.target)
                self.video_list.append(video)
            logging.debug(f"Found {len(self.video_list)} videos")

            # Last page of videos is empty, no more videos to fetch
            if len(self.video_list) < 1:
                self.video_list = -1

                return None

        # Next video page exists, return it
        if len(self.video_list) > 0:
            return self.video_list.pop(0)

        # Nothing to return
        return None
