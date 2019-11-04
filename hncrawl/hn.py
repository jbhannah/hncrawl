import re
from collections import Counter
from logging import getLogger
from os import path

from aiohttp import request
from bs4 import BeautifulSoup

logger = getLogger(__name__)

fail_message = "Sorry, we're not able to serve your requests this quickly."
words = re.compile(r"[A-Za-z']+")

with open(path.join(path.dirname(__file__), "stopwords-en.txt"), "r") as file:
    stopwords = [s for s in map(str.strip, file.readlines())]


class RateLimitError(Exception):
    def __init__(self, id_):
        self.id_ = id_
        self.message = "Rate limited when attempting to get comments for {}".format(
            self.id_)


class Story:
    def __init__(self, id_=None, rank=None, title=None):
        self.id_ = id_
        self.rank = rank
        self.title = title
        self.comment_count = 0
        self.comments = []
        self.top_words = []

    def __repr__(self):
        return "{}. {} [{}] ({} comment{})".format(
            self.rank, self.title, self.id_, self.comment_count,
            "" if self.comment_count == 1 else "s")

    async def get_comments(self, session):
        self.comments = await get_story_comments(session, self.id_)
        self.comment_count = len(self.comments)
        self._get_top_comment_words()

    def _get_top_comment_words(self):
        comment_words = map(str.lower, words.findall(" ".join(self.comments)))
        c = Counter(filter(lambda w: w not in stopwords, comment_words))
        self.top_words = c.most_common(5)


async def get_index_stories(session):
    index = await _get(session, "https://news.ycombinator.com/")
    index_soup = BeautifulSoup(index, "html.parser")

    return [
        Story(id_=row['id'],
              rank=int(float(row.find("span", "rank").string)),
              title=row.find("a", "storylink").string)
        for row in index_soup.find_all("tr", "athing")
    ]


async def get_story_comments(session, id_):
    logger.debug("Getting comments for {}".format(id_))
    story = await _get(session,
                       "https://news.ycombinator.com/item?id={}".format(id_))
    story_soup = BeautifulSoup(story, "html.parser")

    comments = [
        _sanitized_comment_string(comment)
        for comment in story_soup.find_all("span", "commtext")
    ]

    if len(comments) > 0 or "".join(
            s for s in story_soup.strings).find(fail_message) == -1:
        logger.debug("Got {} comments for {}".format(len(comments), id_))
        return comments

    raise RateLimitError(id_)


def _sanitized_comment_string(comment):
    while comment.a:
        comment.a.decompose()

    return " ".join(string for string in comment.strings)


async def _get(session, url):
    response = await session.get(url)
    return await response.text()
