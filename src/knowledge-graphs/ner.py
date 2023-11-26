
from os.path import isfile
from os import listdir
import spacy
import re
from itertools import zip_longest, groupby
from pymystem3 import Mystem
from collections import Counter
import csv

from entity_extraction import get_entities, get_relation

# nlp = spacy.load("ru_core_news_sm")
# nlp = spacy.load("ru_core_news_lg")
# nlp = spacy.load("training/output/model-last")

def iter_fanfics(entity_dir, out_dir):
    for key, group in groupby(listdir(entity_dir), lambda x: x[:7]):
        group = list(group)
        # if len(group) > 1:
        #     print(key, len(list(group)))
        print("===============================")
        print(key)

        if key in listdir(out_dir):
            continue
        yield key, group


def iter_chapters(text_dir, group):
    for filename in group:
        # print("===============================")
        # print(key, filename)
        with open(text_dir + filename, "r", encoding="utf-8") as f:
            yield f.read()


def iter_sentences(text):
    text = re.split('\.|!|\?', text)
    for sentence in text:
        yield sentence


def extract_tags(lemmatised):
    return [tag for tag in re.findall("\<(.*?)\>", lemmatised) if tag]


def extract_predicate(sentence):
    #find predicate in sentence
    predicate = get_relation(sentence.replace("<", "").replace(">", ""))
    if not predicate:
        return
    predicate = mystem.lemmatize(predicate)[0]
    if len(predicate) < 3:
        return
    if predicate[-2:] not in ("ть", "ти", "чь", "ся"):
        return
    return predicate


def knowledge_graph(
        text_dir="ner/",
        entity_dir="entities/",
        out_dir="graph/",
    ):
    for key, group in iter_fanfics(entity_dir, out_dir):
        #iterate all tags and remember nonerroneous
        multipage_tags = []
        for text in iter_chapters(text_dir, group):
            for sentence in iter_sentences(text):
                print(sentence)
                lemmatised = "".join(mystem.lemmatize(sentence))
                print(lemmatised)
                if tags := extract_tags(lemmatised):
                    if len("".join(tags))/len(sentence) > 0.5 and len(sentence.split()) > 10:
                        # These are sentences which erroneously received
                        # an unusually high number of tags. Skip them.
                        continue

                    # print(tags)
                    multipage_tags.extend(tags)
        counted_tags = Counter(multipage_tags)
        # for tag in sorted(counted_tags, key=counted_tags.get, reverse=True):
        #     count = counted_tags[tag]
        #     if count > 2:
        #         print(tag, count)
        counted_tags = {k: v for k, v in counted_tags.items() if v > 2}

        tag_groups = []
        # find all relevant triplet
        for text in iter_chapters(text_dir, group):
            for sentence in iter_sentences(text):
                lemmatised = "".join(mystem.lemmatize(sentence))
                tags = extract_tags(lemmatised)
                relevant_tags = set(counted_tags) & set(tags)
                if len(relevant_tags) > 1:
                    subj, obj, *_ = relevant_tags
                    if predicate := extract_predicate(sentence):
                        triplet = (subj, predicate, obj)
                        tag_groups.append(triplet)

        counted_tag_groups = Counter(tag_groups)
        with open(out_dir + key, "w", encoding="utf-8") as f:
            write = csv.writer(f, dialect='unix')
            for index, tag in enumerate(sorted(counted_tag_groups, key=counted_tag_groups.get, reverse=True)):
                # count = counted_tag_groups[tag]
                # if len(tag) != 2:
                #     # Sentence has multiple tags. Difficult to treat.
                #     continue
                # if index/len(counted_tag_groups) <= 0.1 and count >= 5:
                #     status = "взаимосвязан с"
                # elif count >= 2:
                #     status = "имеет отношение к"
                # else:
                #     status = "незначимо связан с"
                # write.writerow([tag[0], status, tag[1]])
                print(tag)
                write.writerow(tag)

if __name__ == "__main__":
    mystem = Mystem()
    # extract_entities(out_dir="entities/sm/")
    # corpus_markup()
    knowledge_graph()
    # clean_entities()
    # corpus_markup(text_dir="fanfics/", entity_dir="entities/sm/", out_dir="ner/sm/")
    # corpus_reformat()
    #extract_entities(out_dir="entities-trained/")
    #corpus_markup(entity_dir="entities-trained/")
    #clean_entities(in_dir="entities/ourmodel/", out_dir="entities/ourmodel-clean/")
    stats()
