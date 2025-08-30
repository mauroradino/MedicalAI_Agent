import os
from dotenv import load_dotenv
from openai import OpenAI
import pyaudio
import wave
import keyboard
import tempfile

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAPI_KEY"))

def record_audio(frecuency=16000, channels=1, fragment=1024):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=channels, rate=frecuency, input=True, frames_per_buffer=fragment)
    print("presiona ENTER para comenzar a grabar")
    frames=[]
    keyboard.wait('enter')
    print("grabando... suelta ENTER para detener la grabacion")
    while keyboard.is_pressed('enter'):
        data = stream.read(fragment)
        frames.append(data)
    print("grabacion detenida")
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    return frames, frecuency

def save_audio(frames, frecuency):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
        wf = wave.open(temp_audio_file.name, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(frecuency)
        wf.writeframes(b''.join(frames))
        wf.close()
        return temp_audio_file.name    
    
def transcribe_audio(file_path):
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(file=(os.path.basename(file_path), audio_file.read()),
                                                            model="whisper-1",
                                                            prompt="transcribe the following audio",
                                                            response_format="text",
                                                            language="en")
        return transcript    
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None            
    

def main():
        frames, frecuency = record_audio()
        audio_file_path = save_audio(frames, frecuency)
        print("transcribiendo audio...")
        transcript = transcribe_audio(audio_file_path)
        if transcript:
            return transcript
        else:
            print("No se pudo transcribir el audio.")    
        os.remove(audio_file_path)


if __name__ == "__main__":
    main()            