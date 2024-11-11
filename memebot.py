#!/usr/bin/env python3

""" SUCHO Memebot - RSS to Mastodon """

import argparse
import json
import logging
import os
import random
import sys

import feedparser
import requests
from requests.exceptions import RequestException


class UnconfiguredEnvironment(Exception):
    pass


MEME_WALL_RSS_FEED = "https://memes.sucho.org/rss.xml"

MASTODON_HOST = "https://mastodon.online"
TOKEN = os.environ.get("MASTODON_TOKEN")
if not TOKEN:
    raise UnconfiguredEnvironment("MASTODON_TOKEN not set")

STATUS_CHARACTER_LIMIT = 500

POSTED_LOG = "posted.log"
MASTODON_STATUSES_API_ENDPOINT = (
    MASTODON_HOST + "/api/v1/statuses?access_token=" + TOKEN
)

MASTODON_MEDIA_API_ENDPOINT = MASTODON_HOST + "/api/v2/media?access_token=" + TOKEN


def post_status(post, media_id):
    """Post to Mastodon"""
    headers = {
        "Content-Type": "application/x-www-form-URLencoded",
        "Idempotency-Key": post["meme_id"],
    }

    data = {
        "status": build_status(post),
        "media_ids[]": [media_id],
    }

    try:
        response = requests.post(
            MASTODON_STATUSES_API_ENDPOINT, headers=headers, data=data
        )
    except RequestException as exp:
        raise SystemExit(exp)

    if response.status_code != 200:
        # Note: 404 status when testing could be an "Idempotency-Key" collision...
        logging.warning(f"{response.status_code}: {response.text}")
        raise SystemExit(response.status_code)

    return response.json()


def post_image(post):
    files = {
        "file": (
            post["media_fn"],
            requests.get((post["media_href"]), stream=True).raw,
            post["media_mime"],
        )
    }

    try:
        response = requests.post(MASTODON_MEDIA_API_ENDPOINT, files=files)
    except RequestException as exp:
        raise SystemExit(exp)

    if response.status_code != 200:
        logging.warn(response.text)
        raise SystemExit(response.status_code)

    return response.json()["id"]


def assemble_post(entry):
    media = next(_ for _ in entry.links if _.rel == "enclosure")
    return {
        "meme_id": get_meme_id(entry),
        "link": entry.link,
        "summary": entry.summary.replace("<br />", "\n").strip(),
        "media_href": media.href,
        "media_fn": media.href.split("/")[-1],
        "media_mime": media.type,
    }


def build_status(post):
    summary = post["summary"]
    postscript = f"\n\n{post['link']}\n\n#SUCHO"

    postscript_length = (
        len("#SUCHO")  # hashtag
        + 4  # newlines
        + 23  # URLs count for 23 characters, regardless of length (https://docs.joinmastodon.org/user/posting/#links)
    )

    if len(post["summary"]) > STATUS_CHARACTER_LIMIT - postscript_length:
        summary = (
            post["summary"][: STATUS_CHARACTER_LIMIT - postscript_length - 1] + "…"
        )

    return summary + postscript


def log_posted(meme_id, post_date, post_link):
    with open(POSTED_LOG, "a", encoding="utf8") as _fh:
        _fh.write(f"{meme_id} {post_date} {post_link}\n")


def get_posted_ids():
    with open(POSTED_LOG, "r", encoding="utf8") as _fh:
        return [_.split(" ")[0].strip() for _ in _fh.readlines()]


def choose_meme():
    rss_feed = feedparser.parse(MEME_WALL_RSS_FEED)
    posted_ids = get_posted_ids()
    entries = rss_feed.entries
    random.shuffle(entries)
    for entry in entries:
        if get_meme_id(entry) not in posted_ids:
            return entry
        logging.debug(f"{get_meme_id(entry)} already posted")

    raise StopIteration("No memes found to post")


def get_meme_id(meme):
    return meme.id.split("#")[-1]


def memebot_go_beepboop():
    info("Fetching memes and selecting an unposted meme...")
    try:
        meme = choose_meme()
    except StopIteration:
        info("No unposted memes found -- exiting!")
        return
    debug(json.dumps(meme, indent=2) + "\n\n")

    post = assemble_post(meme)
    debug(json.dumps(post, indent=2) + "\n\n")

    info("Posting image to mastodon...")
    media_id = post_image(post)
    debug(f"Media ID: {media_id}" + "\n\n")

    info("Posting status to mastodon...")
    post_response = post_status(post, media_id)
    debug(json.dumps(post_response, indent=2) + "\n\n")

    log_posted(get_meme_id(meme), post_response["created_at"], post_response["uri"])

    info("...completed!")


def info(msg):
    if sys.stdout.isatty():
        logging.info(f"\u001b[33m{msg}\u001b[0m")
    else:
        logging.info(msg)


def debug(msg):
    if isinstance(msg, str):
        logging.debug(msg + "\n\n")
    else:
        logging.debug(json.dumps(msg, indent=2) + "\n\n")


def main():
    """Command-line entry-point."""

    parser = argparse.ArgumentParser(description="Description: {}".format(__doc__))
    parser.add_argument(
        "-v", "--verbose", action="store_true", default=False, help="Increase verbosity"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", default=False, help="quiet operation"
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_level = logging.CRITICAL if args.quiet else log_level
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    memebot_go_beepboop()


if __name__ == "__main__":
    main()
