class PhotoAlbum:
    url = ""
    metadata = None
    pictures = []
    loaded = False

    def meta(self):
        pass

    def next_photo(self):
        pass


class Video:
    url = ""
    source_url = None
    metadata = None
    loaded = False

    def meta(self):
        pass

    def next_video(self):
        pass


class Scraper:
    options = {
        "write_bio": False,
        "write_media": False,
        "list_albums": False,
        "list_videos": False
    }
    base_url = ""
    target = None
    biography = None

    def __init__(self, write_bio=False):
        self.options['write_bio'] = write_bio

    def list_targets(self, page=1):
        pass

    def select_target(self, name):
        self.target = name

    def bio(self):
        pass

    def next_album(self):
        pass

    def next_video(self):
        pass
