import argparse
import datetime
import pickle
import pprint
import zlib


def dump_file(filename):

    with open(filename, "rb") as f:
        expiration = datetime.datetime.fromtimestamp(pickle.load(f))
        print(f"Expiration: {expiration.strftime('%B %d, %Y %I:%M %p')}")
        pprint.pprint(pickle.loads(zlib.decompress(f.read())))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Show the contents of a Django cache file")
    parser.add_argument("-f", "--filename", help="The cache filename.", required=True)
    args = parser.parse_args()

    filename = args.filename

    return_code = dump_file(filename)
