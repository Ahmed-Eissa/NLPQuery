#-----------------------------------------------------------------------------------
# Description: NLP API that allow end user to query Database using Natural language
# Developed By: Ahmed Eissa (Ahmed.Eissa@linkdev.com)
# Date: 26 May 2023
#------------------------------------------------------------------------------------
import os
from langchain.llms import AzureOpenAI
import openai
from langchain.prompts.prompt import PromptTemplate
from langchain import SQLDatabase, SQLDatabaseChain
from flask import Flask , jsonify
import time

#----------------------------------------------------------------------
# Setting variables and initialization
#----------------------------------------------------------------------

os.environ["OPENAI_API_KEY"] = "96d4f4e8e9384446b4896a90243cbffc"
openai.api_type = "azure"
openai.api_base = "https://linkdevopenai01.openai.azure.com/"
openai.api_version = "2022-12-01"
_DEFAULT_TEMPLATE =  """Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
this year mean 2023 and last year mean 2022,this month mean May, last or previous month mean April, Category mean products.productcategory , Use the following format:

Question: "Question here"
SQLQuery: "SQL Query to run"
SQLResult: "Result of the SQLQuery"
Answer: "Final answer here"
Question:
{table_info}
 {input}"""

PROMPT = PromptTemplate(
    input_variables=["input", "table_info", "dialect"], template=_DEFAULT_TEMPLATE
)

llm = AzureOpenAI( temperature=0,  verbose=True, deployment_name="davinci", model_name="text-davinci-003")
print(llm)
#db = SQLDatabase.from_uri("mssql+pyodbc://sa:abc_123@localhost/NLPQuery?driver=ODBC+Driver+17+for+SQL+Server",sample_rows_in_table_info=0)
db = SQLDatabase.from_uri("mssql+pyodbc://esissa:Ahmed_Eissa@LINKDEVDEMO.DATABASE.WINDOWS.NET/LangChain?driver=ODBC+Driver+17+for+SQL+Server",sample_rows_in_table_info=0)

db_chain = SQLDatabaseChain(database=db, llm=llm , prompt= PROMPT,  return_intermediate_steps=True)

#----------------------------------------------------------------------
# Exposed Functions:
#   1- analyze: return POS + NE + Lemma
#   2- getLemma: return Lemma only
#   3- getPOS: return POS only
#   4- getNE: return Named Entities only
#----------------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def Home(inputText):
    return 'Hello NLP Query Project'

@app.route('/QueryDB/<string:inputText>')
def QueryDB(inputText):
    print("start")
    start_time = time.time()

    r = db_chain(inputText) #compare sales this months and last month per color
    l = len(r['intermediate_steps'])
    print('raw result:')
    raw_result = r['intermediate_steps'][l - 2]['input']
    print(raw_result)
    a = raw_result.index('inputText=')
    b = raw_result.index('SQLQuery:')
    c = raw_result.index('SQLResult:')
    d = raw_result.index('Answer:')
    p1_start = a + len('inputText=')
    p1_end = b
    p2_start = b + len('SQLQuery:')
    p2_end = c
    p3_start = c + len('SQLResult:')
    p3_end = d
    Question = raw_result[p1_start:p1_end]
    print(Question)
    Query = raw_result[p2_start:p2_end]
    print(Query)
    Result = raw_result[p3_start:p3_end]
    print(Result)
    Output = {}
    Output['Question'] = Question
    Output['Query'] = Query
    Output['Result'] = Result
    Output['Answer'] = r['intermediate_steps'][l - 1]
    Output['Columns'] = Query[Query.index('SELECT ') + len('SELECT '): Query.index('FROM ')].split(',')
    print(Output)
    print('--------------------------------------------------')


    print("--- %s seconds ---" % (time.time() - start_time))
    return jsonify(Output)



#----------------------------------------------------------------------
app.run( host='0.0.0.0' , port=8001 , debug=True)
