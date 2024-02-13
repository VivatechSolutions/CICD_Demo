from dotenv import load_dotenv
load_dotenv()
from langchain.vectorstores import Qdrant
from langchain.embeddings.openai import OpenAIEmbeddings
import qdrant_client
from flask import Flask, request, jsonify, session
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from pymongo import MongoClient
from datetime import datetime
import os
import uuid
from langchain.prompts.chat import SystemMessagePromptTemplate


app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure random value in production

# MongoDB URI
# mongodb_uri = "mongodb+srv://darshan:VG4inwNtIDZEvLrF@cluster1.4b09mmq.mongodb.net/?retryWrites=true&w=majority"

OPENAI_API_KEY= os.getenv('OPENAI_API_KEY')


QDRANT_HOST = os.getenv('QDRANT_HOST')
app.config['QDRANT_HOST'] = QDRANT_HOST
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
app.config['QDRANT_API_KEY'] = QDRANT_API_KEY
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION')
app.config['QDRANT_COLLECTION'] = QDRANT_COLLECTION
mongodb_uri = os.getenv('mongodb_uri')
app.config['mongodb_uri'] = QDRANT_HOST

# Connect to MongoDB
client = MongoClient(mongodb_uri)
mongo_db = client['viva']
mongo_collection = mongo_db['chat_history']

def send_message(user, message):
    timestamp = datetime.now()
    data = {'user': user, 'message': message, 'timestamp': timestamp}
    mongo_collection.insert_one(data)

def get_chat_history(user):
    mongo_history = mongo_collection.find({'user': user})
    return [message['message'] for message in mongo_history]


def get_vector_store():
    client = qdrant_client.QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)
    embeddings = OpenAIEmbeddings()
    vector_store = Qdrant(client=client, collection_name=QDRANT_COLLECTION, embeddings=embeddings)
    return vector_store

template = """
    Use the following context (delimited by <ctx></ctx>) and the chat history (delimited by <hs></hs>) to answer the question:
    The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details only from its context and it will suggest some information based on the provided context. If the question is out of context, AI  replies back  with it is out of context.
    {context}
    </ctx>
    ------
    <hs>
    {chat_history}
    </hs>
    ------
    {question}
    Answer:
    """

prompt = PromptTemplate(input_variables=["chat_history", "context", "question"], template=template)

from openai.error import OpenAIError

def get_conversation_chain(vector_store, prompt):
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True, output_key='answer')
    print(memory)
    user_id = get_or_create_user_id()
    chat_history = get_chat_history(user_id)
    print(chat_history)
    # print("Is chat_history a list of strings?", all(isinstance(msg, str) for msg in chat_history))
    formatted_chat_history = [{'message': msg} for msg in chat_history]
    print("Formatted chat history:", formatted_chat_history)

    try:
        qa = ConversationalRetrievalChain.from_llm(
            ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.5, max_tokens=100),
            retriever=vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5, "include_metadata": True}),
            return_source_documents=True,
            verbose=True,
            chain_type="stuff",
            get_chat_history=lambda h: formatted_chat_history,
            combine_docs_chain_kwargs={'prompt': prompt},
            memory=memory
        )
        return qa
    except OpenAIError as e:
        # Handle rate limit error
        print("OpenAI API Rate Limit Exceeded. Please wait and retry later.")
        raise


@app.route('/ask', methods=['POST'])
def ask_question():
    user_question = request.json['question']
    user_id = get_or_create_user_id()
    conversation_chain1 = get_conversation_chain(get_vector_store(), prompt)
    response = handle_userinput(user_question, conversation_chain1, user_id)
    return jsonify({'response': response['answer']})

def get_or_create_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def handle_userinput(user_question, conversation_chain1, user_id):
    chat_history = get_chat_history(user_id)
    response = conversation_chain1({'question': user_question, 'chat_history': chat_history})
    send_message(user_id, user_question)
    send_message(user_id, response['answer'])
    return {"answer": response['answer']}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
