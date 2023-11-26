import spacy
from spacy.matcher import Matcher
nlp = spacy.load("ru_core_news_sm")

def get_entities(sent):
    ## chunk 1
    ent1 = ""
    ent2 = ""

    prv_tok_dep = "" # Теги зависимостей, ранее отмеченные в предложении
    prv_tok_text = "" # Предыдущая отметка в предложении
    prefix = ""
    modifier = ""

    #############################################################

    for tok in nlp(sent):
        ## chunk 2
                 # Если знак является знаком пунктуации, переходите к следующему знаку
        if tok.dep_ != "punct":
                         # Проверка: является ли знак составным
            if tok.dep_ == "compound":
                prefix = tok.text
                                 # Если предыдущее слово также составное, добавьте к нему текущее слово
                if prv_tok_dep == "compound":
                    prefix = prv_tok_text   + " " +  tok.text

                         # Проверка: является ли метка модификатором
            if tok.dep_.endswith("mod") == True:
                modifier = tok.text
                                 # Если предыдущее слово также составное, добавьте к нему текущее слово
                if prv_tok_dep == "compound":
                    modifier = prv_tok_text   + " " +  tok.text

            ## chunk 3
            if tok.dep_.find("subj") == True:
                ent1 = modifier  + " " +  prefix   + " " +  tok.text
                prefix = ""
                modifier = ""
                prv_tok_dep = ""
                prv_tok_text = ""

            ## chunk 4
            if tok.dep_.find("obj") == True:
                ent2 = modifier  + " " +  prefix  + " " +  tok.text

            ## chunk 5
                         # Обновить переменные
            prv_tok_dep = tok.dep_
            prv_tok_text = tok.text
    #############################################################

    return [ent1.strip(), ent2.strip()]

def get_relation(sent):

    doc = nlp(sent)

    # Объект класса Matcher
    matcher = Matcher(nlp.vocab)

    # Режим определения
    pattern = [{'DEP':'ROOT'},
               {'DEP':'prep','OP':"?"},
               {'DEP':'agent','OP':"?"},
               {'POS':'ADJ','OP':"?"}]

    matcher.add("matching_1", [pattern], on_match=None)

    matches = matcher(doc)
    if not matches:
        return
    k = len(matches) - 1

    span = doc[matches[k][1]:matches[k][2]]

    return(span.text)
