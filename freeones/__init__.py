import requests
import json
import yaml
import re
from lxml import etree
from bs4 import BeautifulSoup
from os import path, mkdir
import urllib.request
from urllib.parse import urlparse

freeonesyaml = '''\
name: FreeonesCommunity
performerByName:
  action: scrapeXPath
  queryURL: https://www.freeones.com/babes?q={}&v=teasers&s=relevance&l=96&m%5BcanPreviewFeatures%5D=0
  scraper: performerSearch
performerByURL:
  - action: scrapeXPath
    url:
      - freeones.xxx
      - freeones.com
    scraper: performerScraper

xPathScrapers:
  performerSearch:
    performer:
      Name: //div[@id="search-result"]//p[@data-test="subject-name"]/text()
      URL:
        selector: //div[@id="search-result"]//div[@data-test="teaser-subject"]/a/@href
        postProcess:
          - replace:
              - regex: ^
                with: https://www.freeones.com
              - regex: /feed$
                with: /bio

  performerScraper:
    performer:
      Name:
        selector: //h1
        postProcess:
          - replace:
              - regex: \sBio\s*$
                with: ""
      URL: //link[@rel="alternate" and @hreflang="x-default"]/@href
      Twitter: //form//a[contains(@href,'twitter.com/')]/@href
      Instagram: //form//a[contains(@href,'instagram.com/')]/@href
      Birthdate:
        selector: //span[contains(text(),'Born On')]
        postProcess:
          - replace:
              - regex: Born On
                with:
          - parseDate: January 2, 2006
      Ethnicity:
        selector: //a[@data-test="link_ethnicity"]/span/text()
        postProcess:
          - map:
              Asian: Asian
              Caucasian: White
              Black: Black
              Latin: Hispanic
      Country: //a[@data-test="link-country"]/span/text()
      EyeColor: //span[text()='Eye Color']/following-sibling::span/a
      Height:
        selector: //span[text()='Height']/following-sibling::span/a
        postProcess:
          - replace:
              - regex: \D+[\s\S]+
                with: ""
          - map:
              Unknown: ""
      Measurements:
        selector: //span[text()='Measurements']/following-sibling::span/span/a
        concat: " - "
        postProcess:
          - map:
              Unknown: ""
      FakeTits:
        selector: //span[text()='Boobs']/following-sibling::span/a
        postProcess:
          - map:
              Unknown: ""
              Fake: "Yes"
              Natural: "No"
      CareerLength:
        selector: //div[contains(@class,'timeline-horizontal')]//p[@class='m-0']
        concat: "-"
      Aliases: //p[@data-test='p_aliases']/text()
      Tattoos:
        selector: //span[text()='Tattoos']/following-sibling::span/span
        postProcess:
          - map:
              Unknown: ""
      Piercings:
        selector: //span[text()='Piercings']/following-sibling::span/span
        postProcess:
          - map:
              Unknown: ""
      Image:
        selector: //div[contains(@class,'image-container')]//a/img/@src
      Gender:
        fixed: "Female"
      Details: //div[@data-test="biography"]
      DeathDate:
        selector: //div[contains(text(),'Passed away on')]
        postProcess:
          - replace:
              - regex: Passed away on (.+) at the age of \d+
                with: $1
          - parseDate: January 2, 2006
      HairColor: //span[@data-test="link_span_hair_color"]
      ShoeSize: //span[@data-test="link_span_shoe_size"]
      Weight:
        selector: //span[@data-test="link_span_weight"]
        postProcess:
        - replace:
            - regex: \D+[\s\S]+
              with: ""

# Last Updated April 16, 2021
'''

class Album:
    url = ""
    slug = ""
    pictures = []
    base_url = "https://www.freeones.com"

    def __init__(self, slug):
        self.slug = slug.strip('/').rsplit('/', 1)[-1]
        self.url = f"{self.base_url}{slug}"


class Babe:
    base_url = "https://www.freeones.com"
    months = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr': 4,
        'may': 5,
        'jun': 6,
        'jul': 7,
        'aug': 8,
        'sep': 9,
        'oct': 10,
        'nov': 11,
        'dec': 12
    }

    def __init__(self, slug, write_log):
        self.slug = slug
        self.biography = {}
        self.album_list = []
        self.picture_list = []
        self.log = write_log

        if self.log:
            print(f"Fetching: {self.slug}")

    def bio(self):
        try:
            structure = yaml.load(freeonesyaml, Loader=yaml.FullLoader)
#            with open(r"./FreeonesCommunity.yml") as file:
#                structure = yaml.load(file, Loader=yaml.FullLoader)
            bio_paths = structure['xPathScrapers']['performerScraper']['performer']
        except IOError as ex:
            if self.log:
                print("Structure YAML file not found")
            return

        url = f"{self.base_url}/{self.slug}/bio"
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
                    #value = value.strip()

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
                        match = re.search('([a-zA-Z]+) ([0-9]{1,2}), ([0-9]{4})', value)
                        if match:
                            year = int(match.group(3))
                            month = self.months[match.group(1).lower()[0:3]]
                            day = int(match.group(2))
                            value = f"{year:04d}-{month:02d}-{day:02d}"

            if value:
                self.biography[key.lower()] = value

    def albums(self):
        if self.log:
            print("Processing album list")
        self.album_list = []
        url = f"{self.base_url}/{self.slug}/photos?s=subject-latest&m[route]=subject_gallery_list&m[subjectScope]=1&l=96&p=1"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        album_links = soup.find_all("a", class_="teaser__link")
        for link in album_links:
            self.album_list.append(Album(link['href']))
        if self.log:
            print(f"Found {len(self.album_list)} albums")

    def pictures(self):
        if self.log:
            print("Processing albums", end=" ")
        found = 0
        for album in self.album_list:
            page = requests.get(album.url)
            soup = BeautifulSoup(page.content, "html.parser")
            picture_links = soup.find_all("a", class_="gallery__flex__link", attrs={"data-type": "photo"})

            album.pictures = []
            for link in picture_links:
                album.pictures.append(link['href'])
            found += len(album.pictures)
            if self.log:
                print(".", end="")
        if self.log:
            print(" done")
            print(f"Found {found} pictures")

    def write(self, write_bio, write_pictures):
        # Leave if no valid name for subfolder
        if not self.slug:
            if self.log:
                print("Missing/wrong name")

            return

        # Create target directory
        babe_path = f"./babes"
        if not path.exists(babe_path):
            mkdir(babe_path)
        babe_path = f"{babe_path}/{self.slug}/"
        if not path.exists(babe_path):
            mkdir(babe_path)

        # Write biography to JSON file
        if write_bio:
            json_path = f"{babe_path}bio.json"
            try:
                with open(json_path, 'w') as outfile:
                    json.dump(self.biography, outfile)
                if self.log:
                    print("Biography file written")
            except IOError:
                if self.log:
                    print("Failed to write biography file")

        # Download pictures
        if write_pictures:
            if self.log:
                print("Downloading pictures", end=" ")
            album_base_path = f"{babe_path}/photos"
            if not path.exists(album_base_path):
                mkdir(album_base_path)
            for album in self.album_list:
                album_path = f"{album_base_path}/{album.slug}"
                if not path.exists(album_path):
                    mkdir(album_path)
                for picture in album.pictures:
                    parsed_url = urlparse(picture)
                    target_file = f"{album_path}/{path.basename(parsed_url.path)}"
                    if not path.exists(target_file):
                        try:
                            urllib.request.urlretrieve(picture, target_file)
                        except:
                            if self.log:
                                print(f"Download failed for {picture}")
                if self.log:
                    print(len(album.pictures), end=" ")
            if self.log:
                print("done")
