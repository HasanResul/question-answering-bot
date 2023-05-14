import os
import json
from os.path import join, dirname
from dotenv import load_dotenv
from pathlib import Path
from html2text import html2text
from langchain.llms import Cohere
from langchain.vectorstores import Chroma
from langchain.embeddings.cohere import CohereEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# loading environment variables
load_dotenv(join(dirname(__file__), '.env'))

COHERE_API_KEY = os.environ.get("COHERE_API_KEY")

class QABot:
    def __init__(self) -> None:

        # load documents
        self._get_documents()

        # select embeddings
        self.embeddings = CohereEmbeddings(cohere_api_key=COHERE_API_KEY)

        # create the vectorestore to use as the index
        self.vector_store = Chroma.from_texts(self.documents, self.embeddings)

        # expose this index in a retriever interface
        # provide the most 5 relevant documents
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

        # get custom prompt
        self._get_prompt()

        # create a chain to answer questions 
        # chain type "stuff" is used because the context is not long
        # temperature=0 is used for llm to no improvise
        self.qa_chain = RetrievalQA.from_chain_type(llm=Cohere(cohere_api_key=COHERE_API_KEY, temperature=0), 
                                                chain_type="stuff", retriever=self.retriever,
                                                return_source_documents=True,
                                                chain_type_kwargs={"prompt": self.prompt})

    # create a customized prompt
    def _get_prompt(self):
        prompt_template = """Only use the following context to answer. 
        If you cannot find the answer in the context, say the answer is not found in the documentation. 
        Accept 'Dial Code' given in the context same as 'country code'.
        Accept 'MCC' for a country as the number given right after 'MCC' in the context.

        {context}

        Question: {question}"""
        self.prompt = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

    # preprocess the documents to delete html elements
    def _get_documents(self):
        file_path="./documentation.json"
        data = json.loads(Path(file_path).read_text())

        # title and body are combined because some body parts did not have country in the beginning
        # html elements are cleaned not to confuse the llm
        def doc_organizer(data):
            title = data["title"]
            text = html2text(data["body"]).replace("*","").strip()
            return title + "\n" + text
        self.documents = [doc_organizer(dt) for dt in data]

    # query the chain
    def query(self, query):
        result = self.qa_chain({"query": query})
        full_answer = result["result"]
        start = full_answer.find('Answer')
        end = full_answer.find('\n', start)
        answer = full_answer[start:end]
        return answer + "\n\n" + result["source_documents"][0].page_content