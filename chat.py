from openai import AsyncOpenAI, RateLimitError
from dotenv import load_dotenv
import os
from halo import Halo
import asyncio
import backoff
import time

load_dotenv()

# setup the OpenAI Client
client = AsyncOpenAI()

# Azure OpenAI variables from .env file
OPENAI_MODEL = os.environ.get("OPENAI_MODEL")


def open_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as infile:
        return infile.read()


def save_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as outfile:
        outfile.write(content)


###  OpenAI chat completions call with backoff for rate limits
@backoff.on_exception(backoff.expo, RateLimitError)
async def chat(**kwargs):
    try:
        spinner = Halo(text="Reasoning...", spinner="dots")
        spinner.start()

        start_time = time.time()  # Record the start time
        response = await client.chat.completions.create(**kwargs)
        end_time = time.time()  # Record the end time
        
        
        elapsed_time = end_time - start_time  # Calculate the elapsed time in seconds
        minutes, seconds = divmod(elapsed_time, 60)  # Convert seconds to minutes and seconds
        formatted_time = f"{int(minutes)} minutes and {seconds:.2f} seconds"  # Format the time


        text = response.choices[0].message.content
        tokens = response.usage

        spinner.stop()

        return text, tokens, formatted_time
    except Exception as yikes:
        print(f'\n\nError communicating with OpenAI: "{yikes}"')
        exit(0)


async def main():
    while True:
        # Get user query
        query = input(f"\nAsk GPT (using model: {OPENAI_MODEL}): ")
        if query.lower() == "exit":
            exit(0)

        # Create conversation
        conversation = list()
        # conversation.append({'role': 'system', 'content': open_file('./prompts/system.md')})
        conversation.append(
            {"role": "user", "content": [{"type": "text", "text": query}]}
        )
        response, tokens, formatted_time = await chat(
            model=OPENAI_MODEL,
            messages=conversation,
            stream=False,
            max_completion_tokens=2000,
            temperature=1,
        )

        print(f"{response}\n\nTokens: {tokens}\n\nTime elapsed: {formatted_time}")


if __name__ == "__main__":
    asyncio.run(main())
