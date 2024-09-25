import streamlit as st
from openai import AsyncOpenAI, RateLimitError
import os
from dotenv import load_dotenv
import asyncio
import backoff
import time
import markdown

load_dotenv()

# Azure OpenAI model from .env file
OPENAI_MODEL = os.environ.get("OPENAI_MODEL")
# Azure OpenAI key from .env file
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

st.title("Chat with o1-preview")

# Set OpenAI API key from Streamlit secrets
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


@backoff.on_exception(backoff.expo, RateLimitError)
async def chat(**kwargs):
    try:
        start_time = time.time()  # Record the start time
        response = await client.chat.completions.create(**kwargs)
        end_time = time.time()  # Record the end time

        elapsed_time = end_time - start_time  # Calculate the elapsed time in seconds
        minutes, seconds = divmod(
            elapsed_time, 60
        )  # Convert seconds to minutes and seconds
        formatted_time = (
            f"{int(minutes)} minutes and {seconds:.2f} seconds"  # Format the time
        )

        text = response.choices[0].message.content
        tokens = response.usage

        return text, tokens, formatted_time
    except Exception as yikes:
        print(f'\n\nError communicating with OpenAI: "{yikes}"')
        exit(0)


# Streamed response emulator
def response_generator(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.05)


# Asynchronous main function
async def main():
    # Set a default model
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "o1-preview"

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": f"{prompt}.  Always return your response in markdown format"})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container

        with st.chat_message("assistant"):
            text, tokens, formatted_time = await chat(
                model=OPENAI_MODEL,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    # {"role": m["role"], "content": [{"type": "text", "text": m["content"]}]}
                    for m in st.session_state.messages
                ],
                stream=False,
                max_completion_tokens=4000,
                temperature=1,
            )
            text_md = markdown.markdown(text) # the string text converted to true markdown
            # Initialize a placeholder for streaming
            placeholder = st.empty()           
            # Stream the response as markdown
            markdown_text = ""
            for chunk in response_generator(text_md):
                markdown_text += chunk
                placeholder.html(markdown_text)  # Update the placeholder with streamed markdown
            #response = (st.write_stream(response_generator(text_md)))
            #response = st.write(text)
        # st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.messages.append({"role": "user", "content": text})


# Run the asynchronous main function
if __name__ == "__main__":
    asyncio.run(main())
