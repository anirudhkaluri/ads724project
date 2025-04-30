from django.shortcuts import render
from django.http import HttpResponse
from sentence_transformers import SentenceTransformer
from .models import Items
#from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
#from langchain.embeddings import SentenceTransformerEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
import ollama
from django.http import JsonResponse
import os
import json
import urllib.request
import logging
import socket
db_host=os.environ['DB_HOST']
db_port=os.environ['DB_PORT']
db_name=os.environ['DB_NAME']
db_user=os.environ['DB_USER']
db_password=os.environ['DB_PASSWORD']
db_connection_string = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
model_name=os.environ['MODEL_NAME']
is_production=os.environ['IS_PRODUCTION'].lower()=="true"
# logger=logging.getLogger(__name__)
# pod_name=socket.gethostname()
import requests
def save_data(request):
    try: 
        body_text=request.body.decode('utf-8')
        #print(f"The body is {body_text}")
        embeddings_model=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Uses psycopg3!
        collection_name = "items"
        db = PGVector(
            embeddings=embeddings_model,
            collection_name=collection_name,
            connection=db_connection_string,
            use_jsonb=True,
        )
        #texts = ["Machine learning is powerful", "AI is transforming the world"]
        texts=[body_text]
        db.add_texts(texts)

        return HttpResponse('Data saved successfuly')
    except Exception as e:
        return HttpResponse(f'An exception occured  {e}')

def sayHi(request):
    try: 
        return HttpResponse('Hi hello how are you?')
    except Exception as e:
        return HttpResponse('An exception occured. {e}')
    
def ask_llm(request):
    try:
        req_unicode=request.body.decode('utf-8')
        req_data=json.loads(req_unicode)
        query_text=req_data.get("input","")
        req_num=req_data.get("req_num",0)
        print(f"The #request {req_num} received")
        # if is_production:
        #     logger.info(f"[{pod_name}] #Request {req_num} received")
        # embeddings_model=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        # embedded_query=embeddings_model.embed_query(query_text)
        # embedded_query=list(map(float, embedded_query))
        #print(f"Stored embedding size: {len(embedded_query)}")  # Should be 384
        # collection_name = "items"
        # db = PGVector(
        #     embeddings=embeddings_model,
        #     collection_name=collection_name,
        #     connection=db_connection_string,
        #     use_jsonb=True,
        # )
        #results = db.similarity_search_with_score(query_text, k=2)
        context=""
        # for doc in results:
        #     context=context+doc[0].page_content+"\n"

        prompt = f"Use the following context to answer the query:\n\nContext:\n{context}\n\nQuery: {query_text}"

        if is_production:
            #print("WE ARE IN PRODUCTION")
            #the below is for smollm
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            json_data = json.dumps(payload).encode("utf-8")

            # Build and send the request using urllib
            # url = "http://ollama-service:11434/api/generate"
            # req = urllib.request.Request(
            #     url,
            #     data=json_data,
            #     headers={"Content-Type": "application/json",
            #      "Connection": "close" },
            #     method="POST"
            # )
            #print("Calling the ollama service. database called already")
            try: 
                # with urllib.request.urlopen(req,timeout=2000) as response:
                #     response_data = response.read().decode("utf-8")
                #     response_json = json.loads(response_data)
                #     answer = response_json.get("response", "")
                response = requests.post(
                        "http://ollama-service:11434/api/generate",
                        json={
                            "model": model_name,
                            "prompt": prompt,
                            "stream": False
                        },
                        headers={"Connection": "close","Content-Type":"application/json"},
                        timeout=2000
                    )

                answer = response.json().get("response", "")
            except Exception as e:
                answer=f"Ollama Exception MOSTLY TIMEOUT #Request: {req_num}"
        else:
            #print("WE ARE NOT IN PRODUCTION")
            url="http://127.0.0.1:11434/api/chat"
            payload = {
                "model": "llama3.2",
                "messages": [{"role": "user", "content": prompt}],
                "stream":False
            }
            json_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            # Get and parse the response
            with urllib.request.urlopen(req) as response:
                
                answer = response.read().decode()
                
                #print("The answer is ",answer)

        print(f"The #request {req_num} responded")
        return HttpResponse(answer)
    
    except Exception as e:
        return HttpResponse(f"An exception occured  {e}")
