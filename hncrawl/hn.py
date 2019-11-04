from bs4 import BeautifulSoup
from requests import get

from .story import Story


def get_index_stories():
    index = get("https://news.ycombinator.com/")
    index_soup = BeautifulSoup(index.content, "html.parser")
    return [
        Story(id_=row['id'],
              rank=int(float(row.find("span", "rank").string)),
              title=row.find("a", "storylink").string)
        for row in index_soup.find_all("tr", "athing")
    ]
