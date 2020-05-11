import argparse
import json
import pprint

import boto3

client = boto3.client("lambda")


def invoke(url, parse_domain):

    payload = {
        "url": url,
        "parse_domain": parse_domain
    }

    response = client.invoke(
        ClientContext="MyApp",
        FunctionName="SnarfFavicon",
        InvocationType="Event",
        LogType="Tail",
        Payload=json.dumps(payload)
    )

    pprint.PrettyPrinter(indent=4).pprint(response)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--parse_domain", "-p", default=True,
                        help="should we parse the domain from the url?",
                        action="store_true")
    parser.add_argument("--url", "-u", type=str, required=True,
                        help="the url whose favicon you want to snarf")

    args = parser.parse_args()

    parse_domain = args.parse_domain
    url = args.url

    invoke(url, parse_domain)
