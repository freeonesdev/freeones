import argparse
from scrapers.freeones.site import FreeOnes

if __name__ == '__main__':
    write_bio = False
    write_pictures = False
    write_videos = False
    write_log = False

    # Process command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("site", help="Site to scrape data from")
    parser.add_argument("--target", help="Target identifier (eg. URL slug) to retrieve info from")
    parser.add_argument("--no-bio", help="Don't fetch biography", action="store_true")
    parser.add_argument("--no-album", help="Don't download pictures", action="store_true")
    parser.add_argument("--no-video", help="Don't download videos", action="store_true")
    parser.add_argument("--log", help="Print log messages", action="store_true")
    args = parser.parse_args()

    if args.log:
        write_log = True

    if args.target:
        if not args.no_bio:
            write_bio = True
        if not args.no_album:
            write_pictures = True
        if not args.no_video:
            write_videos = True

        if args.site == "freeones":
            # Scrape freeones.com, write logs
            f = FreeOnes(write_log)

            # Select babe
            f.select_target(args.target)

            # Biography
            print("Biography")
            f.write_bio(write_bio)
            bio = f.bio()

            # Photo albums
            print("Albums")
            f.write_albums(write_pictures)
            while (a := f.next_album()) is not None:
                print(a.meta())
                ps = 0
                while (p := a.next_photo(download=True)) is not None:
                    ps += 1
                print(f"Album had {ps} photos")

            # Videos
            print("Videos")
            f.write_videos(write_videos)
            while (v := f.next_video()) is not None:
                print(v.meta())
                v.download()

        elif args.site == "warashi":
            print("Not implemented yet")
        else:
            print(f"Unknown site: {args.site}")

    elif write_log:
        print("No target set, list 1st page")
        # Scrape freeones.com, write logs
        f = FreeOnes(write_log)

        # List first page of target listing
        babes = f.list_targets()
        print(f"Found {len(babes)} babes")
