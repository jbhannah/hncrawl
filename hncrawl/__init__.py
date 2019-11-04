from asyncio import Queue, create_task, gather, run, sleep

from aiohttp import ClientSession

from .hn import RateLimitError, get_index_stories


def main():
    run(_main())


async def _worker(i, queue, session):
    while True:
        try:
            story = await queue.get()
            print("Worker {} handling {}".format(i, story.id_))
            await story.get_comments(session)
        except RateLimitError as e:
            print("Worker {} encountered error: {}".format(i, e.message))
            await sleep(1)
            await queue.put(story)
        finally:
            queue.task_done()
            print("Worker {} done, {} in queue".format(i, queue.qsize()))


async def _main(max_workers=10):
    async with ClientSession() as session:
        queue = Queue(maxsize=max_workers)
        workers = [
            create_task(_worker(i, queue, session)) for i in range(max_workers)
        ]

        stories = await get_index_stories(session)

        for story in stories:
            await queue.put(story)

        print("Awaiting queue")
        await queue.join()

        for worker in workers:
            worker.cancel()

        print("Canceling workers")
        await gather(*workers, return_exceptions=True)

    for story in stories:
        print(story)
        print(story.top_words)
