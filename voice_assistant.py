import streamlit as st
import os
import time
import pyttsx3
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv

st.set_page_config(page_title = "Voice Assistant",layout = "wide")

#$env:VOICE_API_KEY = "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"

# loading the api key from local enviornment for safty purpose
load_dotenv()
VOICE_API_KEY = "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"

if not VOICE_API_KEY:
    st.error("Missing API Key in ENV")
    st.stop()

# Client to connect with Groq cloud
client = Groq(api_key=VOICE_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# initializing speech recognizer
@st.cache_resource
def get_recognizer():
    return sr.Recognizer()
recognizer = get_recognizer()
def get_tts_engine():
    try:
        engine = pyttsx3.init()
        return engine
    except Exception as e:
        st.error("Failed to initialize the TTS engine")
        return None

# function for speech
def speak(text,voice_gender = "girl"):
    try:
        engine = get_tts_engine()
        if engine is None:
            return
        voices = engine.getProperty("voices")
        if voices:
            if voice_gender == "boy":
                for voice in voices:
                    if "male" in voice.name.lower():
                        engine.setProperty("voice",voice.id)
                        break
            else:
                for voice in voices:
                    if "female" in voice.name.lower():
                        engine.setProperty("voice",voice.id)
                        break
        engine.setProperty('rate', 200)
        engine.setProperty('volume', 0.8)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        st.error(f"TTS error: {e}")

# help to listen from the micro
def listen_to_speech():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source,duration = 1)
            audio = recognizer.listen(source,phrase_time_limit = 10)
        text = recognizer.recognize_google(audio)
        return text.lower()
    except sr.UnknownValueError:
        return "Sorry, I don't Catch You"
    except sr.RequestError as e:
        return "Speech service not available"
    except Exception as e:
        return f"Some Error Occour : {e}"

# Connect with LLM Model through Groq Cloud

def get_ai_response(messages):
    try:
        response = client.chat.completions.create(
            model = MODEL,
            messages = messages,
            temperature = 0.7
        )
        result = response.choices[0].message.content
        return result.strip() if result else "Sorry, I could not generate a response"
    except Exception as e:
        return f"Error in getting AI response: {e}"

# Glue main code

def main():
    st.title("VOICE ASSISTANT : JARVIS")
    st.markdown("---")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{"role" : "system", "content" : "Reply like walter white, he is a character in Breaking Bad. Reply only one line"}]
    # Here we are creating streamlit message list 
    # This will help us to pass all previous messages to LLM fro better reply
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("CONTROLS")

        tts_enabled = st.checkbox("Enable Text-to-speech", value = True)

        voice_gender = st.selectbox(
            label = "Voice Gender",
            options = ["girl","boy"],
            help = "Choose between girl or boy voice for your assistant"
        )

        if st.button("Start voice input"):
            user_input = listen_to_speech()

            if user_input and user_input not in ["Sorry, I don't catch you", "Speech service not available"]:
                st.session_state.messages.append({"role": "user", "content":user_input})
                st.session_state.chat_history.append({"role": "user","content":user_input})

                # get AI reply
                with st.spinner("Thinking...."):
                    ai_response = get_ai_response(st.session_state.chat_history)
                    st.session_state.messages.append({"role": "user", "content":ai_response}) # to pass conversation to LLM
                    st.session_state.chat_history.append({"role": "user","content":ai_response}) # used for display data on screen

                # speak the reply if enabled
                if tts_enabled:
                    speak(ai_response,voice_gender)
                st.rerun()
        st.markdown("---")
        st.subheader("TEXT INPUT")
        user_text_input = st.text_input("Type your message")
        if st.button("Send", use_container_width=True) and user_text_input:
            st.session_state.messages.append({"role":"user","content":user_text_input})
            st.session_state.chat_history.append({"role":"user","content":user_text_input})

            #get AI reply
            with st.spinner("Thinking...."):
                ai_response = get_ai_response(st.session_state.chat_history)
                st.session_state.messages.append({"role":"user","content":ai_response})
                st.session_state.chat_history.append({"role":"user","content":ai_response})
            if tts_enabled:
                speak(ai_response,voice_gender)
            st.rerun()
        st.markdown("---")

        #clear conversation
        if st.button("Clear chat",use_container_width=True):
            st.session_state.message = []
            st.session_state.chat_history = [{"role" : "system", "content" : "Reply like Jessy pinkman, he is a character in Breaking Bad. Reply only one line"}]
            st.rerun()
    st.subheader("Conversation")
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("user"):
                st.write(message["content"])
    # Welcome Message
    if not st.session_state.messages:
        st.info("Welcome: Use the voice button to start the conversation")

    st.markdown('---')
    st.markdown(

        """
        <div style = "text-align: center">
        <p> Powered by GROQ and STREAMLIT * Copyright : Kalyan</p>
        </div>
        """,
        unsafe_allow_html = True
    )

if __name__ == "__main__":
    main()