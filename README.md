# ConQRet-RAG
Retrieval Augmented Argumentation or Retrieval Augmented Argument Generation involves retrieving noisy evidence documents over the web and using them for subsequent argument generation. To facilitate RAG and computational argumentation research, we release **ConQRet**, a benchmark with popular controversial queries, paired with evidence documents retrieved and scraped over the public web, alongwith model-generated arguments. 

## Applications
- Retrieval Augmented Generation
- Evaluating Standalone Retrieval
- Evaluating RAG systems

## Statistics of ConQRet
| Statistic                      |     |
|---------------------------------|-----|
| Total topics                    | 98  |
| Avg. docs per topic             | 133 |
| Avg. relevant docs per topic    | 66  |
| Avg. docs per stance            | 33  |

The total number of documents retrieved and scraped from the web are 6500.

## Sample


## Getting Started

Download the data from this [Google Drive link](https://drive.google.com/file/d/1jzNKVsc9VRc6kTOWFYdvp6NDoT4NQqak/view?usp=sharing), unzip it and copy it in the project home folder ("conqret-rag"). The password is provided at the end of the README. 
### Reproducing the Retrieval Results
```bash
python retriever.py
```
OR
```bash
```

### Running Sample Retrievers


## Load the 

```ssh
pip install -r requirements.txt
pip install --upgrade git+https://github.com/emory-irlab/pyterrier_genrank.git
```


### Password for Unzipping the Documents
SaglyanchaVichaarVasudhaivaKutumbakam01293872

Do not publicly upload elsewhere. We are sharing the documents separately to mitigate the possibility of it being used for training, although we do not guarantee that many of them might already be used by popular models through other means.