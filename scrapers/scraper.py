class PhotoAlbum:
    url = ""
    metadata = None
    pictures = []
    loaded = False

    def __init__(self, write_log):
        self.log = write_log

    def meta(self):
        pass

    def next_photo(self):
        pass


class Video:
    url = ""
    source_url = None
    metadata = None
    loaded = False

    def __init__(self, write_log):
        self.log = write_log

    def meta(self):
        pass

    def next_video(self):
        pass


class Scraper:
    options = {
        "write_bio": True,
        "write_albums": True,
        "write_videos": True
    }
    base_url = ""
    target = None
    biography = None

    def __init__(self, write_log):
        self.log = write_log

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

    def write_bio(self, write):
        self.options['write_bio'] = write

    def write_albums(self, write):
        self.options['write_albums'] = write

    def write_videos(self, write):
        self.options['write_videos'] = write
