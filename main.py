import argparse
import logging
from scrapers.freeones.site import FreeOnes


if __name__ == '__main__':
    write_bio = True
    write_media = True
    list_pictures = True
    list_videos = True

    # Process command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("site", help="Site to scrape data from")
    parser.add_argument("--target", help="Target identifier (eg. URL slug) to retrieve info from")
    parser.add_argument("--no-bio", help="Don't fetch biography", action="store_true")
    parser.add_argument("--no-album", help="Don't look for photo galleries", action="store_true")
    parser.add_argument("--no-video", help="Don't look for videos", action="store_true")
    parser.add_argument("--no-download", help="Don't download photos/videos", action="store_true")
    parser.add_argument("--log", help="Set log level (error|warning|info|debug)")
    args = parser.parse_args()

    if args.log is not None:
        numeric_level = getattr(logging, args.log.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {args.log}")
        logging.basicConfig(level=numeric_level)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        fh = logging.FileHandler('error.log')
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)

    if args.target:
        write_bio = not args.no_bio
        write_media = not args.no_download
        list_pictures = not args.no_album
        list_videos = not args.no_video

        if args.site == "freeones":
            # Scrape freeones.com, write logs
            f = FreeOnes(write_bio)

            # Select babe
            f.select_target(args.target)

            # Biography

            bio = f.bio()

            # Photo albums
            if list_pictures:
                logging.info("Albums")
                while (a := f.next_album()) is not None:
                    logging.debug(a.meta())
                    ps = 0
                    while (p := a.next_photo(download=write_media)) is not None:
                        ps += 1
                    logging.info(f"Album had {ps} photos")

            # Videos
            if list_videos:
                logging.info("Videos")
                while (v := f.next_video()) is not None:
                    logging.debug(v.meta())
                    if write_media:
                        v.download()

        elif args.site == "warashi":
            logging.warning("Not implemented yet")
        else:
            logging.warning(f"Unknown site: {args.site}")

    else:
        logging.info("No target set, list 1st page")
        # Scrape freeones.com, write logs
        f = FreeOnes()

        # List first page of target listing
        babes = f.list_targets()
        logging.info(f"Found {len(babes)} babes")
