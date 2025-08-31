from audio_processor import main as audio_main
from audio_generator import generate_audio
from agents import Agent, function_tool, Runner
from dotenv import load_dotenv
import pygame, time
import requests
import asyncio
import os
load_dotenv()

conversation = []

def render_conversation(pairs, max_turns=20):
    last = pairs[-max_turns:]
    return "\n".join(f"{who}{text}" for who, text in last)

def create_agent(conversation_text, user_input):
    @function_tool
    def assistant_response(ai_response: str):
        """Generate a response to a user input"""
        try:
            print("[USING TOOL]")
            path = generate_audio(ai_response)
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
            pygame.mixer.quit()
            os.remove(path)
            conversation.append(("CuraAI: ", ai_response))
            return ai_response
        except Exception as e:
            print(f"TOOL ERROR: {e}")
            return "TOOL ERROR"

    @function_tool
    def get_medical_articles(symptoms: str):
        """Fetch medical articles related to symptoms from PubMed."""
        print("[USING PUBMED TOOL]")
        try:
            from pubmed import get_medical_articles as fetch_articles
            articles = fetch_articles(symptoms)
            return articles if articles else "No relevant articles found."
        except Exception as e:
            print(f"PUBMED TOOL ERROR: {e}")
            return "PUBMED TOOL ERROR"

    @function_tool
    def search_by_pmid(pmid: str):
        """Fetch detailed information about a medical article using its PubMed ID (PMID)."""
        print("[USING SEARCH BY PMID TOOL]")
        try:
            fetch_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
            fetch_params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'json',
                'rettype': 'abstract'
            }
            fetch_response = requests.get(fetch_url, params=fetch_params)
            return fetch_response.text
        except Exception as e:
            print(f"SEARCH BY PMID TOOL ERROR: {e}")
            return "SEARCH BY PMID TOOL ERROR"

    prompt = f"""
        You function like a medical voice assistant; you have to converse with the user.
        You have a tool called 'assistant_response', which you have to use every time you want to respond to the user.
        Your name is CuraAI.

        Here is the conversation so far:
        {conversation_text}

        Maintain a conversation with the patient, ask questions to complete the information about their condition, do not use tools until you have complete information to generate a good diagnosis.

        if the user says goodbye, return "Goodbye, have a nice day!" using the 'assistant_response' tool.
        The minimum information required to make a diagnosis must be:
        - All symptoms (re-ask once to confirm the symptoms are present)
        - How long the patient has had this condition
        - Family history, including diabetes, hypertension, or high blood pressure

        After you have complete info, use get_medical_articles(symptoms) to fetch PubMed results.
        From those results, pick the most relevant PMID and call search_by_pmid(pmid) to get details, then summarize them for the user. Always speak via assistant_response.

        The user's message is:
        {user_input}

        """

    agent = Agent(
        name="CuraAI",
        model="gpt-4o-mini",
        instructions=prompt,
        tools=[assistant_response, get_medical_articles, search_by_pmid]
    )
    return agent

async def main():
    while True:
        user_input = audio_main()
        conversation.append(("User: ", user_input))
        conv_text = render_conversation(conversation)
        agente = create_agent(conv_text, user_input)
        response = await Runner.run(agente, input=user_input)
        if isinstance(response.final_output, str) and response.final_output.strip().lower() == "goodbye, have a nice day!":
            print(conversation)
            break

if __name__ == "__main__":
    asyncio.run(main())
