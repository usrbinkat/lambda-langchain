import os
import json
import azure.functions as func

# Third-party libraries
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain import PromptTemplate

# Validate and fetch environment variables at startup
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key is missing")

# Initialize the chatbot at startup to avoid re-initialization for each request
chatbot = None
def initialize_chatbot():
    global chatbot
    chatbot = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(
            openai_api_key=api_key,
            temperature=0,
            model_name="gpt-3.5-turbo",
            max_tokens=100
        ),
        chain_type="custom_chain",
        retriever=FAISS.load_local("faiss_midjourney_docs", OpenAIEmbeddings()
                    ).as_retriever(search_type="similarity", search_kwargs={"k": 1})
    )

initialize_chatbot()

# Create a reusable prompt template
template_str = "respond as succinctly as possible. {query}?"
prompt = PromptTemplate(
    input_variables=["query"],
    template=template_str,
)

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Content-Type": "application/json"
    }

    if req.method == "OPTIONS":
        return func.HttpResponse("", headers=headers, status_code=204)

    try:
        body = json.loads(req.get_body().decode())
    except ValueError:
        return func.HttpResponse(
            json.dumps({'error': 'Invalid JSON payload'}),
            headers=headers,
            status_code=400
        )

    question = body.get("question")
    if question is None:
        return func.HttpResponse(
            json.dumps({'error': 'No question was provided'}),
            headers=headers,
            status_code=400
        )

    try:
        response = chatbot.run(prompt.format(query=question))
    except Exception as e:  # Replace with specific exception types
        return func.HttpResponse(
            json.dumps({'error': f'Chatbot operation failed: {str(e)}'}),
            headers=headers,
            status_code=500
        )

    return func.HttpResponse(
        json.dumps(response),
        headers=headers,
        status_code=200
    )
