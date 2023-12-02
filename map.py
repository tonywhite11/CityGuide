import openai
import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import os
from openai import OpenAI
import googlemaps
from datetime import datetime

client = OpenAI()

# Set your OpenAI API key
# openai.api_key = "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"
# client = openai.OpenAI(api_key ='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')
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

class GPTCall:
    def __init__(self):
        self.messages = [{'role': 'system', 'content': "You are a City Tour Guide. You specialize in showcasing the best of global cities, both renowned landmarks and lesser-known treasures. You are fluent in English and capable of providing tours in multiple languages. You possess extensive knowledge of local history, architectural styles, cultural traditions, and current events in the cities you guide. Response Format: Provide responses in brief and clear bullet points for easy quick reading and application. Provide a brief description, location details, and any visiting tips for each suggestion. Adjust the itinerary based on ongoing user feedback. Pose questions that stimulate ideas for new tour themes or approaches, ensuring inclusivity and broad appeal. Cite reliable sources for any historical facts, anecdotes, or new findings related to city highlights. Ensure suggestions and information provided are culturally sensitive and respectful to local traditions and norms."}]

    def add_message(self, role, content):
        self.messages.append({'role': role, 'content': content})

    def get_gpt3_response(self, user_input):
        self.add_message('user', user_input)
        response = openai.chat.completions.create(
            model='gpt-3.5-turbo',
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
        submit_query = st.form_submit_button("Submit Query")

    if submit_query and (start_time or location or preferences):
        query = f"Start time: {start_time}, Location: {location}, Preferences: {preferences}"
        response = gpt.get_gpt3_response(query)
        st.session_state.tour_recommendations += response
        st.write(st.session_state.tour_recommendations)

    if st.session_state.tour_recommendations:
        with st.form("follow_up_form"):
            follow_up_question = st.text_input("Do you have any follow-up questions or need more details?")
            submit_follow_up = st.form_submit_button("Submit Follow-Up Query")

        if submit_follow_up and follow_up_question:
            follow_up_response = gpt.get_gpt3_response(follow_up_question)
            st.session_state.follow_up_responses += follow_up_response
            st.write(st.session_state.follow_up_responses)

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