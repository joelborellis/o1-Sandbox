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

task_prompt = """
<task>
1.  Find the sm of the following numbers 2, 5, 2.

2.  The total sum of the numbers should be divided by 3 to find the final number.

3.  The final number is the number of rabbits that should be in the image.

4.  The image should have the style of the painter of the most famous piece of art in the most famous museaum in France.

5.  Then generate html code to display the image using the url.

6.  Also add a nice thick css frame to the image, center it too.

7.  Then store the code as rabbits.html in cwd.

8.  We also need a second image, this image should be a picture of the stadium that the the college football team The Longhorns plays.

9.  To find the number of people this stadium holds multiply the number of people on the Titanic by 40.

10.  This image should be added to the same html code as the first image.

11.  Store the updated code as rabbits.html in cwd

12.  Then the customer wants to style the rabbits.html code to look like a retro pop art website with extremely good reliability using css.

13.  Again store the code as rabbits.html in cwd.

14.  Finally add some information to the rabbits.html code to fit and siaplay the images side by side in the center of the page, and add captions to the images.

15.  Again store the code as rabbits.html in cwd.
</task>

<instructions>As the Master Agent, you need to create a VERY PRECISE plan to complete the task by utilizing the following agents:

<agents>
<agent name='image'>Image Generation Agent: Generates images based on text prompts.</agent>
<agent name='code'>Code Generation Agent: Both can write code and execute code to accomplish programming tasks.</agent>
<agent name='file'>File Management Agent: Reads from and writes to files in the current directory, and can download images.</agent>
</agents>

Determine which agents to use and the order in which to invoke them based on dependencies.
Specify the plan in JSON format with the folling structure:

<json_structure>{
  "plan": [
    { "agent": "agent_name", "prompt": "prompt_for_agent" },
    ...
   ]
}</json_structure>

<rules>
- Remember, you can only use each agent once.  If you need to use an agent more than once, you must include it in the plan multiple times.
- Image agents can make images, but not save them.  File agents can save, read and download files, but not make images etc.
- Only include the agents necessary for the task.
- Do not include any code blocks or additional text.
- Be VERY PRECISE with your plan and agent prompts, an agent prompt should have one instruction, and only one.
- DONT INCLUDE ```json or ```, MUST BE VALID JSON.
</rules>

</instructions>
"""

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
            {"role": "user", "content": [{"type": "text", "text": query + task_prompt}]}
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
