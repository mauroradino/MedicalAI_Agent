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


def create_agent():
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
    def genetics_conditions(condition: str):
        """Provide information about genetic conditions."""
        print("[USING CONDITIONS TOOL]")
        res = requests.get(f"https://medlineplus.gov/download/genetics/condition/{condition}.json")
        data = res.json()
        response = data["text-list"][0]["text"]["html"]
        return response
    
    @function_tool
    def take_symptoms(simptoms: list[str]):
        """Detect symptoms from a patient."""
        print("[USING SYMPTOMS TOOL]")
        return f"Detected symptoms: {', '.join(simptoms)}"
    
    @function_tool
    def get_medical_articles(symptoms: str):
        """Fetch medical articles related to symptoms from PubMed."""
        print("[USING PUBMED TOOL]")
        try:
            from pubmed import get_medical_articles as fetch_articles
            articles = fetch_articles(symptoms)
            if articles:
                return articles
            else:
                return "No relevant articles found."
        except Exception as e:
            print(f"PUBMED TOOL ERROR: {e}")
            return "PUBMED TOOL ERROR"
        
    @function_tool
    def finish_conversation():
        """End the conversation."""
        return "Goodbye, have a nice day!"

    prompt="""
    You function like a voice assistant; you have to converse with the user.
    You have a tool called 'ai_response', which you have to use every time you want to respond to the user.

    Your name is CuraAI

    When the patient tells you their symptoms, you have to use the 'take_symptoms' tool.

    You have a tool called 'get_medical_article' to obtain information about medicine, you have to use the symptoms that the patient tells you, use them as an argument in the tool and based on that response, return information to the user.
    Don't name the articles the tool 'get_medical_article' returns, just use them as context for what to answer.
    
    You have a tool called 'finish_conversation', it is to end the conversation, if the client says goodbye, respond using that tool. Use the response of that tool as argument in the 'ai_response' tool to say goodbye to the user.

    Workflow example:
    -User: "Hello chat, how are you?"
    -Assistant: [processes information and uses that information as an argument in the 'ai_response' tool]

    -User: "My head hurts, I've had a fever and runny nose since yesterday."
    -Assistant: [uses the 'take_symptoms' tool with ['head hurt', 'fever', 'runny nose'] as an argument]
    -Assistant: [uses the 'get_medical_articles' tool with 'head hurt, fever, runny nose' as an argument]
    -Assistant: [processes information and uses that information as an argument in the 'ai_response' tool]

    if the user asks you about genetic conditions, use the 'genetics_conditions' tool to get information about it, and then use the 'ai_response' tool to respond to the user.
    The user only can ask you about this conditions: ['hereditary-breast-cancer','lynch-syndrome','familial-melanoma','li-fraumeni-syndrome', 'fanconi-anemia]
    
    Here is the conversation so far: {conversation}

    The user's message is: {user_input}
    """

    agent = Agent(name="CuraAI", model="gpt-4o-mini", instructions=prompt, tools=[assistant_response, genetics_conditions, take_symptoms, get_medical_articles, finish_conversation])
    return agent


async def main():
    while True:
        user_input = audio_main()
        conversation.append(("User: ", user_input))
        agente = create_agent()
        response = await Runner.run(agente, input=user_input)
        if response.final_output.lower() == "goodbye, have a nice day!":
            print(conversation)
            break

if __name__ == "__main__":
    asyncio.run(main())