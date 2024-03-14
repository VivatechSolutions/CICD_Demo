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
from datetime import datetime
import os
import uuid

app = Flask(__name__)

secret_key = os.urandom(24)
app.secret_key = secret_key.hex()

app.secret_key = "your_secret_key"  # Change this to a secure random value in production

# Qdrant configuration
QDRANT_HOST = os.getenv('QDRANT_HOST')
app.config['QDRANT_HOST'] = QDRANT_HOST
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
app.config['QDRANT_API_KEY'] = QDRANT_API_KEY
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION')
app.config['QDRANT_COLLECTION'] = QDRANT_COLLECTION

def get_vector_store():
    client = qdrant_client.QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)
    embeddings = OpenAIEmbeddings()
    vector_store = Qdrant(client=client, collection_name=QDRANT_COLLECTION, embeddings=embeddings)
    return vector_store

template = """
Use the following context (delimited by <ctx></ctx>) and the chat_history {chat_history} (delimited by <hs></hs>) to answer the question:
You are a gentle AI designed for educational conversations with students to act as a teacher . 
You provide information based on the stored context  on the database for answers.
If a question is outside the stored context, you should reply with 'I don't have information on that topic.'
Additionally, you should be able to provide summaries of topics and generate your own questions based on the mentioned topic and give suggestions for 1 marks, 2 marks, 5 marks and 10 marks questions if asked.
However, it is crucial to remember that you should only answer based on the information stored in documents.
Clearly understand the question and continue following the conversation chain based on previous interactions
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

condense_question_template = """
    Return text in the original language of the follow up question.
    If the follow up question does not need context, return the exact same text back.
    Never rephrase the follow up question given the chat history unless the follow up question needs context.
    
    Chat History: {chat_history}
    Follow Up question: {question}
    Standalone question:
"""
condense_question_prompt = PromptTemplate.from_template(condense_question_template)


def get_conversation_chain(vector_store, prompt, chat_history):
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True, output_key='answer')
    print(chat_history)

    try:
        qa = ConversationalRetrievalChain.from_llm(
            ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.6, max_tokens=200),
            retriever=vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5, "include_metadata": True}),
            return_source_documents=True,
            verbose=True,
            chain_type="stuff",
            condense_question_prompt=condense_question_prompt,
            get_chat_history=lambda h: chat_history,
            combine_docs_chain_kwargs={'prompt': prompt},
            memory=memory
        )
        return qa
    except Exception as e:
        print(f"Error: {e}")
        raise

@app.route('/ask', methods=['POST'])
def ask_question():
    request_data = request.json
    user_question = request_data['question']
    chat_history = request_data['chat_history']

    conversation_chain1 = get_conversation_chain(get_vector_store(), prompt, chat_history)
    response = handle_user_input(user_question, conversation_chain1, chat_history)
    
    return jsonify({'response': response['answer']})

@app.route('/v1/ask', methods=['POST'])
def ask_question_v1():
    request_data = request.json
    user_question = request_data['question']
    chat_history = request_data['chat_history']

    conversation_chain1 = get_conversation_chain(get_vector_store(), prompt, chat_history)
    response = handle_user_input(user_question, conversation_chain1, chat_history)
    
    return jsonify({'response': response['answer']})


def handle_user_input(user_question, conversation_chain1, chat_history):
    response = conversation_chain1({'question': user_question, 'chat_history': chat_history})
    return {"answer": response['answer']}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)