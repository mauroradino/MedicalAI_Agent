from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_audio(input_text: str):
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=input_text,
        instructions="Speak as a doctor in a friendly tone."
    )as response:
        response.stream_to_file("response3.mp3")

    return "response3.mp3"