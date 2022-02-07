import argparse
from babe import Babe


if __name__ == '__main__':
	write_bio = False
	write_pictures = False
	write_log = False

	# Process command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("slug", help="URL slug to retrieve info from")
	parser.add_argument("--no-bio", help="Don't fetch biography", action="store_true")
	parser.add_argument("--no-album", help="Don't download pictures", action="store_true")
	parser.add_argument("--log", help="Print log messages", action="store_true")
	args = parser.parse_args()

	if args.log:
		write_log = True

	if args.slug:
		if not args.no_bio:
			write_bio = True
		if not args.no_album:
			write_pictures = True

		if write_bio or write_pictures:
			b = Babe(args.slug, write_log)
			if write_bio:
				b.bio()
			if write_pictures:
				b.albums()
				b.pictures()
			b.write(write_bio, write_pictures)
		elif write_log:
			print("Nothing to do")

	elif write_log:
		print("No slug set")
