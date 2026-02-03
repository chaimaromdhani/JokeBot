from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models import ChatRequest, ChatResponse
from utils import get_random_meme
from llm import get_joke_response, get_general_response, get_random_roast
import os
import logging
import re

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for memes
static_path = os.path.join(os.path.dirname(__file__), "../static/memes")
app.mount("/memes", StaticFiles(directory=static_path), name="memes")

# List of supported joke categories
JOKE_CATEGORIES = ["dark", "dad", "pun", "programming", "brainrot", "genz", "millenials", "trending"]

def extract_category_from_message(message: str) -> str | None:
    # Look for exact category words in the message (word boundary)
    for category in JOKE_CATEGORIES:
        if re.search(r'\b' + re.escape(category) + r'\b', message):
            return category
    # If none found, try to extract any word following "joke" (simple heuristic)
    match = re.search(r'joke(?: about| on| of)? (\w+)', message)
    if match:
        return match.group(1).lower()
    return None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        message = request.message.lower()

        # Roast detection
        if "roast me" in message:
            roast_reply = await get_random_roast()
            return ChatResponse(reply=roast_reply)

        # Meme detection
        if any(word in message for word in ["meme", "funny image", "send a meme"]):
            meme_url = get_random_meme()
            if meme_url:
                return ChatResponse(reply="Sure! Here's a meme for you 😂👉", meme_url=meme_url)
            raise HTTPException(status_code=500, detail="No memes found")

        # Extract category if mentioned or implied
        requested_category = extract_category_from_message(message)

        if requested_category:
            if requested_category in JOKE_CATEGORIES:
                # Known category — just get joke from Gemini
                reply = await get_joke_response(message)
                return ChatResponse(reply=reply)
            else:
                # Unknown category — get Gemini's reply anyway but prefix with apology
                gemini_reply = await get_joke_response(message)
                prefixed_reply = (
                    f"Sorry, I don't have that type of joke but here's what '{requested_category}' could mean: {gemini_reply}"
                )
                return ChatResponse(reply=prefixed_reply)

        # If user just says "joke" with no category, prompt for category
        if "joke" in message:
            return ChatResponse(
                reply="What type of joke would you like? Try: Dark, Dad, Pun, Programming, Brainrot, GenZ, or Millenials 😎"
            )

        # Otherwise, general funny response
        reply = await get_general_response(request.message)
        return ChatResponse(reply=reply)

    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
