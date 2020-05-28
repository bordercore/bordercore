import argparse
import logging
import os
import sys

from lib.admin import fix_file_modified, get_s3_metadata

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M:%S",
                    filename=f"{os.environ['HOME']}/logs/s3-procmail.log",
                    filemode="a")

logger = logging.getLogger("bordercore.sync_s3_to_wumpus")


def do_action(operation, force, limit, sha1sum, uuid):

    if operation == "fix_file_modified":
        fix_file_modified(uuid)
    elif operation == "get_s3_metadata":
        get_s3_metadata(sha1sum, uuid)
    else:
        raise TypeError(f"operation not support: {operation}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", "-f",
                        help="force the operation",
                        action="store_true")
    parser.add_argument("--limit", "-l", default=100000, type=int,
                        help="limit the number of blobs affected")
    parser.add_argument("--sha1sum", "-s", type=str,
                        help="the sha1sum of a single blob")
    parser.add_argument("--verbose", "-v",
                        help="increase output verbosity",
                        action="store_true")
    parser.add_argument("--uuid", "-u", type=str,
                        help="the uuid of a single blob")
    parser.add_argument("--operation", "-o", type=str,
                        help="the operation to perform")

    args = parser.parse_args()

    force = args.force
    limit = args.limit
    verbose = args.verbose
    uuid = args.uuid
    sha1sum = args.sha1sum
    operation = args.operation

    if operation is None:
        logger.error("Please specify the operation to perform")
        sys.exit(1)

    try:
        do_action(operation, force, limit, sha1sum, uuid)
    except Exception as e:
        logger.error(e, exc_info=1)
