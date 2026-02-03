import os
import random

def get_random_meme():
    memes_dir = os.path.join(os.path.dirname(__file__), "../static/memes")
    if not os.path.exists(memes_dir):
        return None

    meme_files = [f for f in os.listdir(memes_dir) if f.endswith((".jpg", ".jpeg", ".png", ".gif"))]
    if not meme_files:
        return None

    selected = random.choice(meme_files)
    return f"http://localhost:8000/memes/{selected}"


