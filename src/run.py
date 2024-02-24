import os
import sys

from langchain_openai import ChatOpenAI, OpenAI
from langchain.prompts import PromptTemplate
from SPARQLWrapper import SPARQLWrapper, JSON
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCHEMA = os.getenv("SCHEMA")
GRAPHDB_URL = os.getenv("GRAPHDB_URL")


GRAPHDB_SPARQL_GENERATION_TEMPLATE = """
  Write a SPARQL SELECT query for querying a graph database.
  The ontology schema delimited by triple backticks is:
  ```
  {schema}
  ```
  Use only the classes and properties provided in the schema to construct the SPARQL query.
  Do not use any classes or properties that are not explicitly provided in the SPARQL query.
  Include all necessary prefixes.
  Do not include any explanations or apologies in your responses.
  Do not wrap the query in backticks.
  Do not include any text except the SPARQL query generated.
  The question delimited by triple backticks is:
  ```
  {question}
  ```
  Use following scheme during substring search: 'CONTAINS(LCASE())''.
  """
GRAPHDB_SPARQL_GENERATION_PROMPT = PromptTemplate(
    input_variables = ["schema", "question"],
    template = GRAPHDB_SPARQL_GENERATION_TEMPLATE,
)


# queryStr = "Search for datasets which contain 'Cocain' in their names. The name of the dataset's measurement technique and the alternate name of the dataset's measurement technique has to contain either 'nuclear magnetic resonance' or 'NMR'."

GRAPHDB_SPARQL_GENERATION_PROMPT_FORMATTED = GRAPHDB_SPARQL_GENERATION_PROMPT.format(
    schema = SCHEMA,
    question = sys.argv[1]
    )
# print(GRAPHDB_SPARQL_GENERATION_PROMPT_FORMATTED)

llm = OpenAI(temperature = 0)

prediction = llm.invoke(GRAPHDB_SPARQL_GENERATION_PROMPT_FORMATTED)
print(prediction)




sparql = SPARQLWrapper(
    endpoint = GRAPHDB_URL,
)
sparql.setReturnFormat(JSON)

sparql.setQuery(prediction)

try:
    result = sparql.queryAndConvert()

    for r in result["results"]["bindings"]:
        print(r)
    
    # RESULT_TEMPLATE = """
    #     List the result.
    #     The ontology schema used in the SPARQL query delimited by triple backticks is:
    #     ```
    #     {schema}
    #     ```
    #     """

    # RESULT_PROMPT = PromptTemplate(
    #     input_variables = ["schema"],
    #     template = RESULT_TEMPLATE,
    # )

    # RESULT_PROMPT_FORMATTED = RESULT_PROMPT.format(
    #     schema = SCHEMA,
    # )
    # print(RESULT_PROMPT_FORMATTED)

    # llm2 = OpenAI(temperature=0)
    # prediction2 = llm2.invoke(RESULT_PROMPT_FORMATTED)
    # print(prediction2)

except Exception as e:
    print(e)













