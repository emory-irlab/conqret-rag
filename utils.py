import glob
import json
import os
import random
import re
import pandas as pd

PROJECT_FOLDER = os.getcwd() # Folder conqret-rag exists.
PROCON_TRAIN_FOLDER = f'{PROJECT_FOLDER}/procon/train_public/*.json'
PROCON_TEST_FOLDER = f'{PROJECT_FOLDER}/procon/test_public/*.json'
DOCUMENT_FOLDER = f'{PROJECT_FOLDER}/documents/*.json'
DOCUMENT2_FOLDER = f'{PROJECT_FOLDER}/documents_sep20/*.json'
DOCID_LIST = [f.removesuffix('.json').split('/')[-1] for f in glob.glob(DOCUMENT_FOLDER)]
DOCID_LIST.extend([f.removesuffix('.json').split('/')[-1] for f in glob.glob(DOCUMENT2_FOLDER)])

RETRIEVAL_ANNOTATIONS = f'{PROJECT_FOLDER}/retrieval_annotations'
TRAIN_QRELS = RETRIEVAL_ANNOTATIONS + '/train_qrels.csv'
TEST_QRELS = RETRIEVAL_ANNOTATIONS + '/test_qrels.csv'
TRAIN_QUERIES = RETRIEVAL_ANNOTATIONS + '/train_queries.csv'
TEST_QUERIES = RETRIEVAL_ANNOTATIONS + '/test_queries.csv'

def get_retrieval_data():
    train_qrels, test_qrels = map(
        lambda file: pd.read_csv(file).astype({'qid': str, 'docno': str}),
        [TRAIN_QRELS, TEST_QRELS]
    )
    train_queries, test_queries = map(
        lambda file: pd.read_csv(file).astype({'qid': str}),
        [TRAIN_QUERIES, TEST_QUERIES]
    )
    return train_qrels, train_queries, test_qrels, test_queries

from itertools import chain

with open(f'{PROJECT_FOLDER}/titles2.json', 'r+') as tfile:
    url2titles = json.loads(tfile.read())

with open(f'{PROJECT_FOLDER}/interrogative_titles.json', 'r+') as tfile:
    interrogative_titles = json.loads(tfile.read())

def get_interrogative(qid):
    return interrogative_titles[str(qid)]

def flatten_iterative(nested_list):
    # Flatten one level of nesting
    return list(chain.from_iterable(nested_list))


def get_query(titles):
    for title in titles:
        if title.strip().endswith('?'):
            return title
    return titles[1] if len(titles) > 1 else titles[0]


def get_ending_docids(paragraph):
    pattern = r"\[(\d+)\]"
    # Find all matches in the paragraph
    ids = re.findall(pattern, paragraph)
    return ids, re.sub(pattern, "", paragraph)

def cleanup(s1):
    return "".join([x if x.isalnum() else " " for x in s1.strip()])

def get_all_document_id_lists(json_data):
    # first get local ids (those in brackets)
    pids = [[get_ending_docids(p)[0] for p in ps['paragraphs']] for ps in json_data['pros']]  #
    cids = [[get_ending_docids(p)[0] for p in ps['paragraphs']] for ps in json_data['cons']]
    pids = set(flatten_iterative(flatten_iterative(pids)))
    cids = set(flatten_iterative(flatten_iterative(cids)))
    # then get the global ids
    sources = json_data['sources']
    localid2globalid = {}
    cids_global = []
    for id in cids:
        for source in sources:
            if str(source['id']) == id:
                cids_global.append(str(source['docid']))
                localid2globalid[id] = str(source['docid'])
    pids_global = []
    for id in pids:
        for source in sources:
            if str(source['id']) == id:
                pids_global.append(str(source['docid']))
                localid2globalid[id] = str(source['docid'])
    cids_global = [cid for cid in cids_global if cid in DOCID_LIST]
    pids_global = [cid for cid in pids_global if cid in DOCID_LIST]
    return cids_global, pids_global, localid2globalid

class QREL:
    """Contains query, qid, documentid and relevance score"""

    def __init__(self, query=None, qid=None, docid=None, relevance=None, stance=None):
        self.query = query
        self.docid = docid
        self.relevance = relevance
        self.qid = qid
        if stance:
            assert stance in ['pro', 'con']
            self.stance = stance
        else:
            self.stance = ''

    def __str__(self):
        return f'{self.query}\t{self.docid}\t{self.relevance}\t{self.stance}'

    def as_dict(self):
        return {'qid': self.qid, 'docno': self.docid, 'label': self.relevance, 'stance': self.stance}

def get_split_qrels(as_df, include_hard_negatives, include_random_negs, include_wikipedia_docs, test_files,
                    stance_condition):
    test_queries = []
    qrels = []
    for file_name in test_files:
        with open(file_name, 'r') as file:
            # Load JSON content
            json_data = json.load(file)
            url = json_data['url'].rstrip('/')
            titles = url2titles[url]['titles']
            qid = url2titles[url]['qid']
            sources = json_data['sources']
            # (1) POSITIVE PAIRS
            # Global pairs (topic as query, all citations on the page as document ids)
            cids, pids, _ = get_all_document_id_lists(json_data)
            query = get_interrogative(qid)
            test_queries.append({'qid': qid, 'query': query})
            if not stance_condition:
                qrels.extend([QREL(query, qid, docid=id, relevance=1, stance='pro') for id in pids])
                qrels.extend([QREL(query, qid, docid=id, relevance=1, stance='con') for id in cids])
            elif stance_condition == 'pro':
                # If stance condition is pro, all other documents relevance is set to zero.
                qrels.extend([QREL(query, qid, docid=id, relevance=1, stance='pro') for id in pids])
                qrels.extend([QREL(query, qid, docid=id, relevance=0, stance='con') for id in cids])
            elif stance_condition == 'con':
                qrels.extend([QREL(query, qid, docid=id, relevance=0, stance='pro') for id in pids])
                qrels.extend([QREL(query, qid, docid=id, relevance=1, stance='con') for id in cids])
            # (2) NEGATIVE PAIRS
            if include_random_negs:
                # open 5 random files in the PROCON folder and get all its document ids
                negs_list = list(test_files)
                negs_list.remove(file_name)
                negs_list = random.sample(negs_list, 5)  # random 5 files
                _neg_docs = []
                for neg_file in negs_list:
                    with open(neg_file, 'r') as f:
                        negs_json = json.load(f)
                        _cids, _pids, _ = get_all_document_id_lists(negs_json)
                        _neg_docs.extend(_cids);
                        _neg_docs.extend(_pids)
                # select out of them
                _neg_docs = random.sample(_neg_docs, min(len(cids) + len(pids), len(_neg_docs)))
                qrels.extend([QREL(query, qid, docid=id, relevance=0, stance='') for id in _neg_docs])
            if include_hard_negatives:
                print();
            if include_wikipedia_docs:
                print();
    if as_df:
        qrels_df = pd.DataFrame.from_dict([qr.as_dict() for qr in qrels])
        qrels_df['qid'] = qrels_df['qid'].apply(str)
        test_queries = pd.DataFrame.from_dict(test_queries)
        test_queries['query'] = test_queries['query'].apply(cleanup)
        test_queries['qid'] = test_queries['qid'].apply(str)
        return qrels_df, test_queries
    return qrels, test_queries


def get_qrels(as_df=False, include_random_negs=False, include_hard_negatives=False, include_wikipedia_docs=False,
              test_from=.7, stance_condition=None):
    if stance_condition:
        assert stance_condition in ['pro', 'con'], 'stance_condition must be pro or con'
    train_files = glob.glob(PROCON_TRAIN_FOLDER)
    test_files = glob.glob(PROCON_TEST_FOLDER)
    print(f'Test files: {len(test_files)}')
    test_qrels, test_queries = get_split_qrels(as_df, include_hard_negatives, include_random_negs,
                                               include_wikipedia_docs, test_files, stance_condition)
    print(f'Train files: {len(train_files)}')
    train_qrels, train_queries = get_split_qrels(as_df, include_hard_negatives, include_random_negs,
                                                 include_wikipedia_docs, train_files, stance_condition)
    return train_qrels, train_queries, test_qrels, test_queries


def get_no_of_documents():
    return len(glob.glob(DOCUMENT_FOLDER)) + len(glob.glob(DOCUMENT2_FOLDER))


def get_documents(skip_html=True):
    # List to hold data
    data = []
    # Loop through each JSON file in the folder
    # for file_name in glob.glob(DOCUMENT_FOLDER):
    for file_name in glob.glob(DOCUMENT_FOLDER) + glob.glob(DOCUMENT2_FOLDER):
        with open(file_name, 'r') as file:
            # Load JSON content
            json_data = json.load(file)
            if skip_html:
                # Remove the 'HTML' key from the dictionary
                json_data.pop('html', None)
            # Rename 'docid' to 'docno'
            json_data['docno'] = json_data.pop('docid', None)  # Pop 'docid' and assign its value to new key 'docno'
            json_data['docno'] = str(json_data['docno'])
            json_data['text'] = json_data.pop('stripped_html', None)
            if not json_data['text']:
                continue
            if 'It would eliminate the need for re-calibrations in the' in json_data['text']:
                print()
            data.append(json_data)
    # Convert list to DataFrame
    return data, pd.DataFrame(data)


if __name__ == '__main__':
    documents_jsons, documents_df = get_documents()
    # If you've extracted procon data from procon-parser.py. uncomment below
    #train_qrels, train_queries, test_qrels, test_queries = get_qrels(as_df=True, include_random_negs=True, test_from=.7)
    # Else load from the data we extracted (retrieval_annotations) folder
    train_qrels, train_queries, test_qrels, test_queries = get_retrieval_data()
    print(len(train_qrels))