from collections import deque
# from dotenv import load_dotenv
from langchain.vectorstores import Qdrant
from langchain.embeddings.openai import OpenAIEmbeddings
import qdrant_client
import os
import openai
from flask import Flask, request, jsonify

from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain


app = Flask(__name__)
# Initialize chat history as a deque with a maximum length
MAX_HISTORY_LENGTH = 100  # Adjust the maximum history length as needed
chat_history = deque(maxlen=MAX_HISTORY_LENGTH)

os.environ["OPENAI_API_KEY"] = "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"

QDRANT_HOST = "https://a07bb1c0-0275-4297-ae4a-c7610f2ade8c.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "M2y27uEHjgj0tdcT00h1Il_B2PHKV2eLIHdScov5dzjjT1mIvTJAmQ"
QDRANT_COLLECTION = "gradeupai"

def get_vector_store():
    client = qdrant_client.QdrantClient(
         QDRANT_HOST,
        api_key=QDRANT_API_KEY
    )
    embeddings = OpenAIEmbeddings()
    vector_store = Qdrant(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embeddings=embeddings,
    )
    return vector_store

def get_conversation_chain(vector_store):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True
    )
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(),
        memory=memory
    )
    return conversation_chain

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/apt',  methods=['POST'])
def index1():
    return QDRANT_COLLECTION

@app.route('/ask', methods=['POST'])
def ask_question():
    user_question = request.json['question']
    conversation_chain = get_conversation_chain(get_vector_store())
    
    response = handle_userinput(user_question, conversation_chain)
    
    return jsonify({'response': response['answer']})
    
    


def handle_userinput(user_question, conversation_chain):
    response = conversation_chain({'question': user_question})
    
    chat_history.append({'role': 'user', 'content': user_question})
    chat_history.append({'role': 'assistant', 'content': response['answer']})
    
    return response

# def main():
#     load_dotenv()

#     chat_history = []
    
#     vector_store = get_vector_store()
#     conversation_chain = get_conversation_chain(vector_store)

#     user_question = input("Ask a question about your documents:")

#     while user_question.lower() not in ['quit', 'exit']:
#         response = handle_userinput(user_question, conversation_chain,chat_history)
        
#         # Display the conversation history
#         for message in chat_history:
#             if message['role'] == 'user':
#                 print("You:", message['content'])
#             elif message['role'] == 'assistant':
#                 print("Bot:", message['content'])
        
#         user_question = input("Ask a question about your documents:")

if __name__ == '__main__':
    # load_dotenv()
    app.run(host="0.0.0.0",port=8000,debug=True)



