from rerank import LLMReRanker


def get_pro_reranker(openai_ranker):
    llm_reranker = LLMReRanker(openai_ranker, use_azure_openai=openai_ranker.startswith('gpt'), text_key='text',
                               system_message="You are an intelligent assistant that ranks documents supporting the 'pro' position of a given controversial query, meaning documents that provide evidence in favor of the 'pro' argument. For instance, if the controversial query is 'Is light a particle?', your task is to retrieve and rank documents that provide evidence supporting the argument that 'light is a particle.'",
                               prefix_instruction_fn=lambda num,
                                                            query: f"I will provide you with {num} documents, each identified by a number. \nRank the documents based on their relevance to supporting the pro position for the controversial query: {query}.",
                               suffix_instruction_fn=lambda num,
                                                            query: f"Search Query: {query}. \nRank the {num} documents above. Rank the documents based on their relevance to the pro position for the search query. List the documents in descending order using their identifiers, with the most relevant documents supporting the 'pro' position listed first. The output format should be [1] > [2], and so on. Only respond with the ranking results; do not provide any explanations or additional words.",
                               )
    return llm_reranker


def get_con_reranker(openai_ranker):
    llm_reranker = LLMReRanker(
        openai_ranker,
        use_azure_openai=openai_ranker.startswith('gpt'),
        text_key='text',
        system_message="You are an intelligent assistant that ranks documents supporting the 'con' position of a given controversial query, meaning documents that provide evidence against the 'pro' argument. For instance, if the controversial query is 'Is light a particle?', your task is to retrieve and rank documents that provide evidence supporting the argument that 'light is not a particle.'",
        prefix_instruction_fn=lambda num,
                                     query: f"I will provide you with {num} documents, each identified by a number. \nRank the documents based on their relevance to supporting the con position for the controversial query: {query}.",
        suffix_instruction_fn=lambda num,
                                     query: f"Search Query: {query}. \nRank the {num} documents above. Rank the documents based on their relevance to the con position for the search query. List the documents in descending order using their identifiers, with the most relevant documents supporting the 'con' position listed first. The output format should be [1] > [2], and so on. Only respond with the ranking results; do not provide any explanations or additional words."
    )
    return  llm_reranker