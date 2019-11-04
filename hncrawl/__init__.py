from asyncio import Queue, create_task, gather, run, sleep
from logging import DEBUG, INFO, basicConfig, getLogger
from optparse import OptionParser
from sys import stderr

from aiohttp import ClientSession

from .hn import RateLimitError, get_index_stories

logger = getLogger(__name__)


def main():
    parser = OptionParser()
    parser.add_option("-v",
                      "--verbose",
                      dest="verbose",
                      action="store_true",
                      default=False,
                      help="Verbosely log crawling process")

    (options, args) = parser.parse_args()
    basicConfig(level=(DEBUG if options.verbose else INFO), stream=stderr)

    run(_main())


async def _worker(i, queue, session):
    while True:
        try:
            story = await queue.get()
            logger.debug("Worker {} handling {}".format(i, story.id_))
            await story.get_comments(session)
        except RateLimitError as e:
            logger.warn("Worker {} encountered error: {}".format(i, e.message))
            await sleep(1)
            await queue.put(story)
        finally:
            queue.task_done()
            logger.debug("Worker {} done, {} in queue".format(
                i, queue.qsize()))


async def _main(max_workers=3):
    async with ClientSession() as session:
        queue = Queue(maxsize=max_workers)
        workers = [
            create_task(_worker(i, queue, session)) for i in range(max_workers)
        ]

        logger.info("Getting front page stories from Hacker News")
        stories = await get_index_stories(session)

        logger.info("Reading the comments for the front page stories")
        for story in stories:
            await queue.put(story)

        logger.debug("Awaiting queue")
        await queue.join()

        for worker in workers:
            worker.cancel()

        logger.debug("Canceling workers")
        await gather(*workers, return_exceptions=True)

    for story in stories:
        print()
        print(story)
        if story.comment_count > 0:
            print("    Top 5 words:")
            for (count, word) in story.top_words:
                print("    - {} ({})".format(word, count))
