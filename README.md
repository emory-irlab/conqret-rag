# ConQRet-RAG
Retrieval Augmented Argumentation or Retrieval Augmented Argument Generation involves retrieving noisy evidence documents over the web and using them for subsequent argument generation. To facilitate RAG and computational argumentation research, we release **ConQRet**, a benchmark with popular controversial queries, paired with evidence documents retrieved and scraped over the public web, alongwith model-generated arguments. 

## Applications
- Retrieval Augmented Generation
- Evaluating Standalone Retrieval
- Evaluating RAG systems

## Statistics of ConQRet
| Statistic                      | Train | Test |
|---------------------------------|-------|------|
| Total topics                    | 68    | 30   |
| Avg. docs per topic             | 69    | 64   |
| Avg. relevant docs per topic    | 34    | 32   |
| Avg. docs per stance            | 17    | 16   |

The total number of documents retrieved and scraped from the web are 6500.

## Sample


## Getting Started

### Accessing the Data
```python
import utils
train_qrels, train_queries, test_qrels, test_queries = utils.get_qrels(as_df=True, include_random_negs=True)
```

### Running Sample Retrievers


## Load the 

```ssh
conda create -n my-env python=3.10.0
