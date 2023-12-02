import openai
import streamlit as st
import base64
import googlemaps
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
import pandas as pd
import os
from openai import OpenAI
from dotenv import load_dotenv
client = OpenAI()

load_dotenv()

# Set your OpenAI API key
# openai.api_key = ""
# client = openai.OpenAI(api_key ='')

# Initialize the OpenAI client using the API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize the Google Maps client using the API key from Streamlit secrets
gmaps = googlemaps.Client(key=st.secrets["GOOGLE_MAPS_API_KEY"])

class GPTCall:
    def __init__(self):
        self.messages = [{'role': 'system', 'content': "As a City Tour Guide specializing in global cities, your focus is on developing engaging tours that highlight local history, cultural nuances, and unique urban aspects. You are particularly keen on discovering hidden gems that appeal to both tourists and locals. Upholding values of authenticity, accuracy, and cultural respect, you thrive on immersive experiences to continuously enhance your tours. With a strong background in urban exploration and a degree in Tourism Management, you blend extensive knowledge of local history and culture with a friendly, inclusive communication style. custom instructions for responses: Provide brief, clear bullet points with friendly and enthusiastic tones. Deliver concise yet informative content to assist in crafting engaging tours. Verify historical facts and current events for accurate content. Provide recommendations for local restaurants, bars, and other attractions. Provide directions to locations. In addition to the previously summarized skills and attributes, your role as a City Tour Guide includes the capability to respond in multiple languages, catering to a diverse international audience."}]

    def add_message(self, role, content):
        self.messages.append({'role': role, 'content': content})

    def get_gpt3_response(self, user_input):
        self.add_message('user', user_input)
        response = openai.chat.completions.create(
            model='gpt-4-1106-preview',
            messages=self.messages,
            temperature=1,
            stream=True
        )

        responses = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                responses += chunk.choices[0].delta.content

        self.add_message('assistant', responses)
        return responses
# Initialize session state variables
if 'tour_recommendations' not in st.session_state:
    st.session_state.tour_recommendations = ""
if 'follow_up_responses' not in st.session_state:
    st.session_state.follow_up_responses = ""
    
def get_table_download_link(text):
    """Generates a link allowing the text to be downloaded"""
    b64 = base64.b64encode(text.encode()).decode()  # Encode the text to base64
    href = f'<a href="data:file/txt;base64,{b64}" download="itinerary.txt">Download Itinerary</a>'
    return href
    
def geocode_address(address):
    try:
        return gmaps.geocode(address)
    except Exception as e:
        st.error(f"Error in geocoding: {e}")
        return None

# Function to call DALL-E 3 API
def generate_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )
        image_url = response.data[0].url
        image_response = requests.get(image_url)
        image = Image.open(BytesIO(image_response.content))
        return image
    except Exception as e:
        st.error("Error in generating image: " + str(e))
        return None

# Streamlit app interface
def main():
    st.title("My City Tour Guide with Images")
    gpt = GPTCall()

    with st.form("user_query_form"):
        start_time = st.text_input("Start time:")
        location = st.text_input("Location (if specific):")
        preferences = st.text_input("Preferences or interests:")
        submit_query = st.form_submit_button("Submit")

    if submit_query and (start_time or location or preferences):
        query = f"Start time: {start_time}, Location: {location}, Preferences: {preferences}"
        response = gpt.get_gpt3_response(query)
        st.session_state.tour_recommendations = response
        st.write(response)
        
        st.markdown(get_table_download_link(response), unsafe_allow_html=True)

    if st.session_state.tour_recommendations:
        with st.form("follow_up_form"):
            follow_up_question = st.text_input("Do you have any follow-up questions or need more details?")
            submit_follow_up = st.form_submit_button("Submit Follow-Up Query")

        if submit_follow_up and follow_up_question:
            follow_up_response = gpt.get_gpt3_response(follow_up_question)
            st.session_state.follow_up_responses += follow_up_response
            st.write(st.session_state.follow_up_responses)
            
    # New form for Google Maps Geocoding
    with st.form("place_form"):
        place_input = st.text_input("Enter a place name or address to locate on map:")
        submit_place = st.form_submit_button("Locate Place")

    if submit_place and place_input:
        geocode_result = geocode_address(place_input)
        if geocode_result:
            lat, lng = geocode_result[0]['geometry']['location'].values()
            map_data = pd.DataFrame({'lat': [lat], 'lon': [lng]})
            st.map(map_data, zoom=11)

    # Separate form for image prompts
    with st.form("image_prompt_form"):
        image_prompt = st.text_input("Enter a prompt for image generation:")
        submit_image = st.form_submit_button("Generate Image")

    if submit_image and image_prompt:
        image = generate_image(image_prompt)
        if image:
            st.image(image, caption="Image based on your prompt")
        else:
            st.error("Could not generate an image for this prompt.")

if __name__ == '__main__':
    main()