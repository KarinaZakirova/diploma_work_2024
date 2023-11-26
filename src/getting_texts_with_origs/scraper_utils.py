import re

def to_ids(author, page, href):
    if "authors" in href:
        return (author, page, 0, 0)
    if "readfic" in href:
        fanfic_ids = href.replace("https://ficbook.net/readfic/", "").replace("#part_content", "").split("/")
        if len(fanfic_ids) == 1:
            fanfic = fanfic_ids[0]
            return (author, page, fanfic, 0)
        fanfic, chapter = fanfic_ids
        return (author, page, fanfic, chapter)

def to_href_origs(ids):
    author, page, fanfic, chapter = ids
    return f"https://ficbook.net/find-fanfics-846555?fandom_filter=originals&fandom_group_id=1&pages_range=1&pages_min=&pages_max=&transl=1&author=1&author_id={author}&likes_min=&likes_max=&rewards_min=&date_create_min=2023-10-18&date_create_max=2023-11-18&date_update_min=2023-10-18&date_update_max=2023-11-18&title=&sort=1&rnd=1384098455&find=%D0%9D%D0%B0%D0%B9%D1%82%D0%B8!&p={page}#result"

def to_filename(ids):
    author, page, fanfic, chapter = ids
    return f"fanfics/{author}_{fanfic}_{chapter}.txt"

