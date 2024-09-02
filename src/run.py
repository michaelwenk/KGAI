import os
import sys


from langchain.prompts import PromptTemplate
from langchain_community.graphs import OntotextGraphDBGraph
from langchain_openai import OpenAI
from langchain.chains.llm import LLMChain
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCHEMA = os.getenv("SCHEMA")
PREFIX = os.getenv("PREFIX")
GRAPHDB_URL = os.getenv("GRAPHDB_URL")

QUESTION = sys.argv[1]

def query(generated_sparql:str):
   return graph.query(query = generated_sparql)    

def setPrefix(objects: list, prefix: str):
    mappedClasses = map(lambda x: prefix + ":" + x, objects)
    return ",\n".join(mappedClasses)

OPTIMISATION_TEMPLATE = """
  Task: Rephrase an input question into a new one!
  
  The input question delimited by triple backticks is:
  ```
  {question}
  ```
  
  Follow the {schema} ontology and use it to guide the rephrasing of the input question.

  During the rephrasing follow the rules delimited by triple backticks below:
  ```
    When semantically searching for names, then compare for both the name and the alternate name of a property if available. 
    Transform the term "measured with" into "and where either the measurement technique's name or the measurement technique's alternate name contains".
    During string comparison, use the regex operator and ignore case sensitivity.

    If you detect the term "NMR" in the input question, then use both "NMR" and "nuclear magnetic resonance" in the rewritten question.
    If you detect the term "nuclear magnetic resonance" in the input question, then use both "NMR" and "nuclear magnetic resonance" in the rewritten question.
    If you detect the term "MS" in the input question, then also use both "MS" and "mass spectrometry" in the rewritten question.
    If you detect the term "mass spectrometry" in the input question, then also use "MS" and "mass spectrometry" in the rewritten question.
    If you detect the term "IR" in the input question, then also use both "IR" and "infrared spectroscopy" in the rewritten question.
    If you detect the term "infrared spectroscopy" in the input question, then also use both "IR" and "infrared spectroscopy" in the rewritten question.
  ```
  
  Do not return the original question in your response, only the rewritten one.
  Do not include any explanations or apologies in your response.
  Do not wrap your response in backticks.
  Do not include any text except the rewritten question which you have generated.  

  """



OPTIMISATION_TEMPLATE_PROMPT = PromptTemplate(
    input_variables = ["question", "schema"], #, "classes", "properties"],
    template = OPTIMISATION_TEMPLATE,
)

graph = OntotextGraphDBGraph(
    query_endpoint = "http://localhost:7200/repositories/NFDI4Chem",
    query_ontology = "CONSTRUCT {?s ?p ?o} FROM " + SCHEMA + " WHERE {?s ?p ?o}",
)

llm = OpenAI(        
        model_name = "gpt-3.5-turbo-instruct", 
        api_key = OPENAI_API_KEY,
        temperature = 0)

optimisation_of_question = LLMChain(llm = llm, prompt = OPTIMISATION_TEMPLATE_PROMPT)
optimisation_result = optimisation_of_question.invoke(input = {
   "question": QUESTION, 
   "schema": SCHEMA, 
   "prefix": PREFIX
   })
print("\n\nOriginal question: " + QUESTION)
print("Rewritten question: \n\"" + optimisation_result["text"] + "\n\"")


GRAPHDB_SPARQL_GENERATION_TEMPLATE = """
  Task: Write a SPARQL SELECT query for querying a GraphDB graph database.
  
  The underlying ontology schema is {schema} and the prefix name {prefix}.
  
  The question delimited by triple backticks is:
  ```
  {question}
  ```

  Include all necessary prefixes.
  Do not include any explanations or apologies in your responses.
  Do not wrap the query in backticks.
  Do not include any text except the SPARQL query generated.
  Only create exactly one SPARQL query.
  """

GRAPHDB_SPARQL_GENERATION_PROMPT = PromptTemplate(
    input_variables = ["schema", "question", "prefix"],
    template = GRAPHDB_SPARQL_GENERATION_TEMPLATE,
)

sparql_generation_chain = LLMChain(llm = llm, prompt = GRAPHDB_SPARQL_GENERATION_PROMPT)

sparql_generation_chain_result = sparql_generation_chain.invoke(
    input = {        
        "schema": SCHEMA,
        "question": optimisation_result["text"],
        "prefix": PREFIX,
        }, 
    )
generated_sparql = sparql_generation_chain_result[sparql_generation_chain.output_key]

GRAPHDB_SPARQL_FIX_TEMPLATE = """
      This following SPARQL query delimited by triple backticks
      ```
      {generated_sparql}
      ```
      is not valid.
      The error delimited by triple backticks is
      ```
      {error_message}
      ```
      Give me a correct version of the SPARQL query.
      Do not change the logic of the query.
      Do not include any explanations or apologies in your responses.
      Do not wrap the query in backticks.
      Do not include any text except the SPARQL query generated.
      The ontology schema delimited by triple backticks in Turtle format is:
      ```
      {schema}
      ```
    """
GRAPHDB_SPARQL_FIX_TEMPLATE_PROMPT = PromptTemplate(
      input_variables = ["schema", "generated_sparql", "error_message"],
      template = GRAPHDB_SPARQL_FIX_TEMPLATE,
    )

GRAPHDB_SPARQL_GENERATION_TEMPLATE_2 = """
      Task: Reconstruct an input SPARQL query into a SPARQL query which builds a graph via the CONSTRUCT command.

      The underlying ontology schema is {schema} and the prefix name {prefix}.
      
      The input SPARQL query delimited by triple backticks is:
      ```
      {generated_sparql}
      ```
      """

GRAPHDB_SPARQL_GENERATION_PROMPT_2 = PromptTemplate(
        input_variables = ["generated_sparql", "schema", "prefix"],
        template = GRAPHDB_SPARQL_GENERATION_TEMPLATE_2,
    )

sparql_generation_chain_2 = LLMChain(llm = llm, prompt = GRAPHDB_SPARQL_GENERATION_PROMPT_2)

trials = 2
query_result = None
i = 1
while i <= trials and query_result == None:
  try: 
    print("\n" + str(i) + ". try to query with: ")
    print(generated_sparql)
    query_result = query(generated_sparql)
    print("\n -> query 1 was successful!!!")

    sparql_generation_chain_result_2 = sparql_generation_chain_2.invoke(
        input = {        
            "generated_sparql": generated_sparql,
            "schema": SCHEMA,
            "prefix": PREFIX,
            }, 
        )
    generated_sparql_2 = sparql_generation_chain_result_2[sparql_generation_chain_2.output_key]

    print(generated_sparql_2)

    query_result = graph.graph.query(query_object=generated_sparql_2)
    print("\n -> query 2 was successful!!!")
      
    break
      
  except Exception as error_message:
    print("\nquery invalid: ")
    print(error_message)
      
    sparql_generation_chain = LLMChain(llm = llm, prompt = GRAPHDB_SPARQL_FIX_TEMPLATE_PROMPT)
    sparql_generation_chain_result = sparql_generation_chain.invoke(
      input = {        
        "schema": SCHEMA,
        "generated_sparql": generated_sparql,
        "error_message": error_message,
      }, 
    )
    generated_sparql = sparql_generation_chain_result[sparql_generation_chain.output_key]      
    i = i + 1
    
if query_result != None:
  print("\nquery_result: ")
  print(len(query_result))

else:
  print("No result after " + str(i - 1) + " tries.")













