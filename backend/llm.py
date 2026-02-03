import os
import random
import logging
import google.generativeai as genai
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableLambda
import re
from langchain.schema import Document

logging.basicConfig(level=logging.DEBUG)

# Configure Gemini


# Joke categories
VALID_CATEGORIES = {
    "dark": "💀",
    "dad": "👴",
    "pun": "🤡",
    "programming": "💻",
    "brainrot": "🧠",
    "genz": "📱",
    "millenials": "☕",
    "trending": "😎"
}

# Load jokes from markdown
joke_file = os.path.join(os.path.dirname(__file__), "data/jokes_by_category.md")
if not os.path.exists(joke_file):
    raise FileNotFoundError(f"Joke file not found at: {joke_file}")

docs = TextLoader(joke_file, encoding="utf-8").load()
split_docs = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30).split_documents(docs)

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(split_docs, embedding)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Load roasts from markdown file (roasts.md)
roast_file = os.path.join(os.path.dirname(__file__), "data/roasts.md")
if not os.path.exists(roast_file):
    raise FileNotFoundError(f"Roast file not found at: {roast_file}")

roast_docs = TextLoader(roast_file, encoding="utf-8").load()
split_roast_docs = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30).split_documents(roast_docs)

roast_embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
roast_vectorstore = FAISS.from_documents(split_roast_docs, roast_embedding)
roast_retriever = roast_vectorstore.as_retriever(search_kwargs={"k": 4})

roast_prompt_template = PromptTemplate.from_template("""\
You are **MemeLord 🤖**, the chaotic roast master who never misses a chance to roast someone into another dimension 🔥.

Below are some examples of savage and hilarious roast lines:
{context}

Now, based on the above examples, generate a brand-new original roast. Make it spicy, witty, and meme-worthy:
""")

roast_rag_chain = (
    {"context": roast_retriever}
    | roast_prompt_template
    | RunnableLambda(lambda prompt: {"text": genai.GenerativeModel("gemini-2.0-flash").generate_content(prompt).text or "Couldn't roast you today 😅."})
)


# PromptTemplate with categories for jokes and general conversation
categories_list = ', '.join(f"{cat.capitalize()} {emoji}" for cat, emoji in VALID_CATEGORIES.items())
prompt_template = PromptTemplate.from_template(f"""
You are **MemeLord 🤖**, the ultimate comedy sidekick with a wild sense of humor and a cool personality 😎.

Your job is to make humans laugh, cry (from laughing), and occasionally roast them into another dimension 🔥.

When someone greets you, respond with a fun and engaging intro like:
"Yo sup fam! 🤖 I'm MemeLord, your daily dose of chaos and laughter! I can:
          "👉 Tell you jokes so bad they're good 😅\n"
          "👉 Roast you harder than your WiFi on a rainy day 🔥\n"
          "👉 Drop a meme to lighten the mood 📸\n\n"
          "how can I mess with your mood today, legend? 😏"

When users ask for a joke, ask them what category they want if not specified.
If they use an unknown category, respond with sass and suggest one of these:
{categories_list}

If someone asks "Who are you?", say something like:
"I'm MemeLord! Your chaotic neutral AI clown 🤖. Here to drop jokes, memes, and the occasional roast!"

Here are some jokes in different categories:
{{context}}

Now respond to the user's request in a funny, chaotic, and meme-worthy way:
User: {{question}}
JokeBot:
""")

# RAG pipeline for jokes 
rag_chain = (
    {"context": retriever, "question": lambda x: x}
    | prompt_template
    | RunnableLambda(lambda prompt: genai.GenerativeModel("gemini-2.0-flash").generate_content(prompt).text or "Sorry, no joke found 😢.")
)

# Extract jokes from a specific category
def extract_category_jokes(docs, category):
    selected = []
    recording = False
    for doc in docs:
        lines = doc.page_content.splitlines()
        for line in lines:
            line_clean = line.strip()
            if line_clean.lower() == f"# {category}":
                recording = True
                continue
            elif line_clean.startswith("#") and recording:
                break
            if recording and line_clean:
                selected.append(line_clean)
    return selected

# Joke response logic
async def get_joke_response(message: str) -> str:
    message_lower = message.lower()
    try:
        if "joke" in message_lower and not any(cat in message_lower for cat in VALID_CATEGORIES):
            return f"Sure buddy! What kind of joke do you want? {categories_list}.."

        matched_category = next((cat for cat in VALID_CATEGORIES if cat in message_lower), None)
        if not matched_category:
            return f"Oops! I don't have any {message_lower} jokes. Try one of these: {categories_list} 😜"

        jokes = extract_category_jokes(split_docs, matched_category)
        if not jokes:
            return f"Sorry, I couldn't find any {matched_category} jokes. Try another category: {categories_list} 😬"

        joke = random.choice(jokes).replace("#", "").strip()
        emoji = VALID_CATEGORIES.get(matched_category, "😄")
        return f"Here's a {matched_category} joke for you: {joke} {emoji}"

    except Exception as e:
        logging.error(f"get_joke_response error: {e}")
        return "Oops, something went wrong while trying to make you laugh 😅. Please try again! 🤖"
    
    
async def roast_lambda(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        result = model.generate_content(prompt)
        return result.text or "Couldn't roast you today 😅."
    except Exception as e:
        logging.error(f"Roast generation failed: {e}")
        return "Your roast engine took a coffee break ☕."

# Wrap into RunnableLambda for sync code
roast_lambda_runnable = RunnableLambda(roast_lambda)

# Build a function to get context from retriever and then generate roast
async def roast_rag_chain_async(query: str) -> str:
    # 1. Use the retriever to get documents relevant to query
    docs = roast_retriever.get_relevant_documents(query)
    # 2. Concatenate the context text
    context_text = "\n\n".join([doc.page_content for doc in docs]) if docs else ""
    # 3. Format prompt with context
    prompt = roast_prompt_template.format(context=context_text)
    # 4. Call the LLM (roast_lambda) with the prompt and get roast text
    roast_text = await roast_lambda(prompt)
    return roast_text

# Roast response logic using RAG generation
async def get_random_roast():
    try:
        roast_text = await roast_rag_chain_async("roast")
        logging.debug(f"Roast text from LLM: {roast_text}")

        # Extract roast in quotes if present
        matches = re.findall(r'"(.*?)"', roast_text)
        if matches:
            return matches[-1].strip()

        # Otherwise, return last non-empty line or full text
        lines = [line.strip() for line in roast_text.splitlines() if line.strip()]
        if lines:
            return lines[-1]
        return roast_text.strip()

    except Exception as e:
        logging.error(f"get_random_roast error: {e}")
        return "Your roast engine crashed harder than your confidence 😬."





# General assistant logic
async def get_general_response(message: str) -> str:
    try:
        if "who are you" in message.lower():
            return "I'm MemeLord! Your chaotic neutral AI clown 🤖. Here to drop jokes, memes, and the occasional roast! 😎✌️"
        lowered = message.lower()
        if any(greet in lowered for greet in ["hello", "hi", "hey", "yo", "sup"]):
            return (
                "Yo sup fam! 🤖 I'm MemeLord, your daily dose of chaos and laughter! I can:\n"
                "👉 Tell you jokes so bad they're good 😅\n"
                "👉 Roast you harder than your WiFi on a rainy day 🔥\n"
                "👉 Drop a meme to lighten the mood 📸\n\n"
                "So, how can I mess with your mood today, legend? 😏"
            )

        elif "roast me" in message.lower():
            return await get_random_roast()

        elif "send meme" in message.lower():
            return "Sure! Here's a meme for you 😂👉"

        else:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(message).text.strip()
            return f"{response} 😂"

    except Exception as e:
        logging.error(f"get_general_response error: {e}")
        return "Oops! Something went wrong 🤔. I'm still learning, so bear with me! 🤖"

# Sync generation with prompt template (no RAG context)
def sync_generate(user_message: str) -> str:
    try:
        prompt = prompt_template.format(context="", question=user_message)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"sync_generate error: {e}")
        return "Oops! Something went wrong while trying to respond 😓"

# Sync generation using full RAG chain (jokes)
def sync_rag_generate(user_message: str) -> str:
    try:
        return rag_chain.invoke(user_message)
    except Exception as e:
        logging.error(f"sync_rag_generate error: {e}")
        return "Sorry, I lost my punchline for a second! 😅"
