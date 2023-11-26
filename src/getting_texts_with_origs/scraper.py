from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from os.path import isfile
from os import listdir
from pathlib import Path

import csv

from scraper_logger import new_logger
from scraper_utils import (
    to_ids,
    to_href_origs,
    to_filename,
)

AUTHORS = [
    # (author id, num pages)
    (1198828, 4),
    (142095, 4),
    # (7286, 33),
    # (36163, 10),
    # (21482, 8),
    # (1625, 8),
    # (37893, 12),
    # (58628, 24),
    # (1635, 11),
    # (15650, 11),
    # (18704, 24),
    # (4, 9),
    # (94, 4),
    # (10857, 8),
    # (25628, 44),
    # (1252, 14),
    # (90393, 6),
    # (34768, 8),
    # (23313, 13),
    # (40376, 8),
    # (13818, 12),
    # (15855, 4),
    # (5597, 16),
]

AUTHORS_ORIGS = [
    # (author id, num pages)
    (1198828, 4),
    (142095, 4),
    (7286, 8),
    (36163, 3),
    (21482, 3),
    (1625, 4),
    (37893, 11),
    (58628, 8),
    (1635, 4),
    (15650, 8),
    (18704, 6),
    (4, 3),
    (94, 3),
    (10857, 6),
    (25628, 26),
    (1252, 5),
    (90393, 5),
    (34768, 4),
    (23313, 5),
    (40376, 4),
    (13818, 8),
    (15855, 3),
    (5597, 4),
]
CRAWLED = Path("crawled.csv")
QUEUE = Path("queue.csv")
ORIGS = Path("origs.csv")

class Scraper:
    def __init__(self):
        self.logger = new_logger("scraper")
        self.logger.debug(f"start chrome")
        self.driver = Driver(
            uc_cdp=True,
            incognito=True,
            headless=True,
            # headed=True,
        )
        self.logger.debug(f"started chrome")
        seed_gen = self.get_seed()
        while True:
            """
            If we are out of links, get new seed.
            If there are queued links available, use those.
            """
            if len(self.queue) == 0:
                self.queue = [next(seed_gen)]
            self.scrape()

    @property
    def crawled(self):
        """
        These pages have already been crawled,
        and may be skipped next time they are seen.
        """
        CRAWLED.touch(exist_ok=True)
        with open(CRAWLED) as f:
            return set(filter(any, map(tuple, csv.reader(f))))

    @crawled.setter
    def crawled(self, value):
        self.logger.debug(f"refreshing backlog: {len(value)} items")
        with open(CRAWLED, "w", encoding="utf-8") as f:
            return csv.writer(f).writerows(sorted(value, key=str))

    @property
    def queue(self):
        """
        These pages are yet to be crawled.
        """
        QUEUE.touch(exist_ok=True)
        with open(QUEUE) as f:
            return set(filter(any, map(tuple, csv.reader(f))))

    @queue.setter
    def queue(self, value):
        self.logger.debug(f"refreshing queue: {len(value)} items")
        with open(QUEUE, "w", encoding="utf-8") as f:
            return csv.writer(f).writerows(sorted(value, key=str))

    @property
    def origs(self):
        """
        These pages are yet to be crawled.
        """
        ORIGS.touch(exist_ok=True)
        with open(ORIGS) as f:
            return set(filter(any, map(tuple, csv.reader(f))))

    @origs.setter
    def origs(self, value):
        self.logger.debug(f"refreshing queue: {len(value)} items")
        with open(ORIGS, "w", encoding="utf-8") as f:
            return csv.writer(f).writerows(sorted(value, key=str))

    def get_seed(self):
        """
        Get initial page from a list of pre-selected pages.
        """
        # for author_id, num_pages in AUTHORS:
        for author_id, num_pages in AUTHORS_ORIGS:
            range_pages = list(reversed(range(num_pages)))
            for page in range_pages:
                seed = (author_id, page+1, 0, 0)
                self.logger.debug(f"{seed} - get new seed {range_pages}")
                self.logger.debug(f"{seed} - get new seed {page}")
                yield seed

    def pop_link(self):
        link, *self.queue = self.queue
        return link

    def scrape(self):
        """
        Find links in given url, add them to the queue.
        """
        ids = next(iter(self.queue))
        author, page, fanfic, chapter = ids
        self.load(ids)

        self.logger.debug(f"{ids} - scraping links")
        with self.driver:
            # find link tags
            elements = self.driver.find_elements(By.CLASS_NAME, "visit-link")
            # extract links from tags
            links = [i.get_attribute('href') for i in elements]
            links = [link for link in links if link]
            print(links)
        self.logger.debug(f"{ids} - links scraped")
        # self.driver.close()
        # self.add_links(author, page, links)
        self.save_links(author, page, links)

        if not links:
            try:
                self.logger.debug(f"{ids} - scraping text")
                # No links found. Try to find text
                with self.driver:
                    element = self.driver.find_element(by="id", value="content")
                    text = element.get_attribute('innerText')
                # self.driver.close()
                self.logger.debug(f"{ids} - text scraped")
                self.add_text(ids, text)
            except NoSuchElementException:
                pass

        # Finished scraping, remove item from queue.
        self.crawled = [*self.crawled, ids]
        self.queue -= set([ids])

    def load(self, ids):
        # link = to_href(ids)
        link = to_href_origs(ids)
        if self.driver.current_url == link:
            self.logger.debug(f"{ids} - same page, no reload")
            return
        self.logger.debug(f"{ids} - loading")
        with self.driver:
            self.driver.get(link)
        self.logger.debug(f"{ids} - loaded")

    def add_links(self, author, page, links):
        """
        Skip links to fanfics that have already been scraped.
        """
        count = 0
        for link in links:
            ids = to_ids(author, page, link)
            if isfile(to_filename(ids)):
                # Already downloaded.
                self.logger.debug(f"{ids} - already downloaded, skipping)")
                continue
            if ids in self.crawled:
                # Already crawled.
                self.logger.debug(f"{ids} - already crawled, skipping)")
                continue
            if ids in self.queue:
                # Already queued.
                self.logger.debug(f"{ids} - already queued, skipping)")
                continue
            self.queue = [ids, *self.queue]
            count += 1
        self.logger.debug(f"learned {count} queue (total: {len(self.queue)})")

    def save_links(self, author, page, links):
        """
        Save a list of fanfics to origs.csv
        """
        count = 0
        for link in links:
            ids = to_ids(author, page, link)
            self.origs = [ids, *self.origs]
            count += 1
        self.logger.debug(f"learned {count} origs (total: {len(self.origs)})")

    def add_text(self, ids, text):
        """
        New text has been received. Count the text and save it on the disk.
        """
        with open(to_filename(ids), "w", encoding="utf-8") as f:
            f.write(text)

        self.logger.debug(f"added text (total: {len(listdir('fanfics/'))})")
