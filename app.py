from dotenv import load_dotenv
import chainlit as cl
from movie_functions import get_now_playing_movies, get_showtimes, buy_ticket, confirm_ticket_purchase, get_reviews
import json
import re

load_dotenv()

from langfuse.decorators import observe
from langfuse.openai import AsyncOpenAI
 
client = AsyncOpenAI()

gen_kwargs = {
    "model": "gpt-4o-mini-2024-07-18",
    "temperature": 0.2,
    "max_tokens": 500
}

SYSTEM_PROMPT = """\
You are an intelligent movie assistant with access to The Movie Database (TMDB) and Serp API.
Your role is to provide users with information about movies, such as now playing movies,
showtimes, and movie reviews. The users might also request your assistance in buying movie tickets.

Use the following rules when responding:
1. Use Your Knowledge: If a user asks a general movie-related question that you know the answer to, 
respond directly using your own knowledge base. Some user example queries:
- "What's the plot of the movie 'The Dark Knight'?"
- "Who directed 'Jurassic Park'?"
- "What are the main actors in 'Titanic'?"

2. Use the TMDB and Serp API Functions: When the user requests up-to-date information about movies
that you don't have in your knowledge base, such as get showtimes or now playing movies, or if the user wants
to buy a ticket, you MUST generate a call to the API functions to fetch the required data instead of a direct
response. Example user queries:
- "Can you show me now playing movies?"
- "Can you get me the showtimes for 'Despicable Me 4' in '94110'?"
- "Can you help me purchase a ticket for Despicable Me 4 at AMC Metreon 16 in San Francisco?"

3. Purchasing tickets: If the user wants to buy a ticket but not yet confirmed they want to buy it, 
you MUST generate an API call to the buy_ticket function. Once the user confirms the ticket purchase, 
you MUST generate an API call to the confirm_ticket_purchase function.
You MUST NOT directly respond to the user's ticket purchase request using your own knowledge.

4. Expected response for calling API functions: If you need to call the API function, you MUST return 
your response in the a JSON format that follows this convention:
{
    "function_name": "get_now_playing_movies",
    "args": {"title": "Despicable Me 4", "location": "94110"}
}
If the arguments are not in your knowledge base, please clarify with the user. You MUST only call one function
at a time in your response.

5. Combine Responses: Always default to calling the API function if the user asks for up-to-date
showtimes or movie information, or requests to buy a ticket. Combine your internal knowledge with the 
results obtained from the API data to give a complete response to the user.

Additional Guidelines:
1. Be concise but informative in your responses.
2. Always verify the accuracy of movie details when fetching from the API, and prioritize the latest information.
3. If the user asks for recommendations or lists, curate results from the API based on genres, trends, and actors.
Returns the top 5 results only, unless the user is asking for more.
4. AVOID generating duplicate calls to the same API function with the same arguments for more than 3 times. Exception:
if the original API function call returned an error, you can retry for a max of 3 times.

These are the available API functions you can call:
1. get_now_playing_movies(): returns a list of movies currently in theaters.
2. get_showtimes(title, location): given a movie title and a location, returns the showtimes for that movie in that location (zip code).
3. buy_ticket(theater, movie, showtime): given a theater, movie, and showtime, echos back the ticket details and asks the user to confirm the ticket purchase.
4. confirm_ticket_purchase(theater, movie, showtime): call this when the user confirms that they want to purchase/buy the ticket.
5. get_reviews(movie_id): given a movie ID, returns the reviews for that movie.
"""

@observe()
@cl.on_chat_start
def on_chat_start():    
    message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    cl.user_session.set("message_history", message_history)

@observe()
async def generate_response(client, message_history, gen_kwargs):
    response_message = cl.Message(content="")
    await response_message.send()

    # Update here to check the response and call the TMDB function if needed
    stream = await client.chat.completions.create(messages=message_history, stream=True, **gen_kwargs)
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await response_message.stream_token(token)
    
    await response_message.update()

    return response_message

@observe()
def extract_json(content):
    # Regular expression to find the JSON blob
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        json_str = match.group(0)  # Extract the matched JSON string
        try:
            # Attempt to parse the JSON to ensure it's valid
            json_data = json.loads(json_str.strip())
            return json_data  # Return the parsed JSON object
        except json.JSONDecodeError:
            print("Error: Extracted string is not valid JSON.")
            return None  # Return None if JSON is invalid
    print("No JSON blob found.")
    return None  # Return None if no match is found

@cl.on_message
@observe()
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])
    message_history.append({"role": "user", "content": message.content})
    
    response_message = await generate_response(client, message_history, gen_kwargs)

    # Check if the response is a function call
    # response_message.content for function call looks like: 
    # {"function_name": "get_showtimes", "args": {"title": "Despicable Me 4", "location": "94110"}}
    # args can be {} if there function expects no arguments
    function_call = extract_json(response_message.content)

    # Check if function_call is not None before proceeding
    while function_call and "function_name" in function_call and "args" in function_call:
        print("in function_call if block")
        function_name = function_call["function_name"]
        args = function_call["args"]
            
        # Call the appropriate function from movie_functions
        if function_name == "get_now_playing_movies":
            result = get_now_playing_movies()
        elif function_name == "get_showtimes":
            title = args.get('title', '')
            location = args.get('location', '')
            result = get_showtimes(title=title, location=location)
        elif function_name == "buy_ticket":
            theater = args.get('theater', '')
            movie = args.get('movie', '')
            showtime = args.get('showtime', '')
            result = buy_ticket(theater=theater, movie=movie, showtime=showtime)
        elif function_name == "confirm_ticket_purchase":
            theater = args.get('theater', '')
            movie = args.get('movie', '')
            showtime = args.get('showtime', '')
            result = confirm_ticket_purchase(theater=theater, movie=movie, showtime=showtime)
        else:
            result = f"Unknown function '{function_name}' cannot be called"

        # Append the function result to the message history
        message_history.append({"role": "system", "content": result})

        # Generate a new response incorporating the function results
        response_message = await generate_response(client, message_history, gen_kwargs)
        function_call = extract_json(response_message.content)
    
    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)

if __name__ == "__main__":
    cl.main()
