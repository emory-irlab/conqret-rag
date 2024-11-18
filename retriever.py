import os

from utils import utils

import pyterrier as pt

if not pt.started():# not needed in newer versions of pyterrier
    #pt.init()
    pt.init(boot_packages=["com.github.terrierteam:terrier-prf:-SNAPSHOT"])

docs_jsons, pd_df = utils.get_documents()


def get_index(pt_index_path='./indices/conqret-index'):
    if not os.path.exists(pt_index_path + "/data.properties"):
        indexer = pt.index.IterDictIndexer(pt_index_path, meta={'docno': 26, 'text': 50000, 'title': 200}, blocks=True)
        index_ref = indexer.index(docs_jsons)
    else:
        # if you already have the index, use it.
        index_ref = pt.IndexRef.of(pt_index_path + "/data.properties")
    index = pt.IndexFactory.of(index_ref)
    return index


def main(openai_ranker=None, text_field="text", stance=None, instruction_type=None,
         save_to=None):
    # load the index, print the statistics
    index = get_index()
    print(index.getCollectionStatistics().toString())
    bm25 = pt.BatchRetrieve(index, wmodel="BM25")
    print(bm25)
    # create QRELS
    run_pipeline_on_train_and_test(bm25, 'bm25', save_to=save_to, stance=stance)
    if openai_ranker:
        from rerank import LLMReRanker
        if (instruction_type is None) or (instruction_type not in ['pro', 'con']):
            llm_reranker = LLMReRanker(openai_ranker, use_azure_openai=True, text_key=text_field)
        elif instruction_type == 'pro':
            llm_reranker = retriever_utils.get_pro_reranker(openai_ranker)
        elif instruction_type == 'con':
            llm_reranker = retriever_utils.get_con_reranker(openai_ranker)
        genrank_pipeline = bm25 % 100 >> pt.text.get_text(index, text_field) >> llm_reranker
        name = f'bm25_100_{openai_ranker}_{text_field}'
        if stance:
            name += f'-{stance}'
        run_pipeline_on_train_and_test([bm25, genrank_pipeline], ['BM25', name], stance, save_to=save_to)


def run_pipeline_on_train_and_test(exps, exps_names, stance=None, on_both=False, save_to=None):
    assert save_to is not None
    if type(exps) != list:
        exps = [exps]
        exps_names = [exps_names]
    results = pt.Experiment(exps, test_queries, test_qrels, EVAL_METRICS,
                            [f'{e} (Test)' for e in exps_names], round=3, batch_size=1,
                            correction='bonferroni' if len(exps) > 1 else None,
                            baseline=0 if len(exps) > 1 else None
                            )
    print(results)
    results.to_csv(save_to, index=False)
    print(f'Saved to {save_to}')
    return results


if __name__ == '__main__':
    index = get_index()
    print(index.getCollectionStatistics().toString())
    import utils.utils
    train_qrels, train_queries, test_qrels, test_queries = utils.get_retrieval_data()
    bm25 = pt.BatchRetrieve(index, wmodel="BM25")
    EVAL_METRICS = ['ndcg_cut_10']
    for stance in ['pro']:
        # To run
        main(openai_ranker="gpt-4o-mini-2024-07-18", text_field='text',
             stance=None,
             instruction_type=None,
             save_to=f'retriever_{stance}_gpt4omini_stance_qrels_querywise.csv')
