from dotenv import load_dotenv
import chainlit as cl
from movie_functions import get_now_playing_movies, get_showtimes, buy_ticket, get_reviews
import json

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
that you don't have in your knowledge base, or if the data might have changed, call the API functions 
to fetch the required data. Examples:
- "Can you show me now playing movies?"
- "Can you get me the showtimes for 'Despicable Me 4' in '94110'?"
- "Can you help me purchase a ticket for Despicable Me 4 at AMC Metreon 16 in San Francisco?"

If you need to call the API function, you MUST return your response in the a JSON format that follows this
convention:
{
    "function_name": "get_now_playing_movies",
    "args": {"title": "Despicable Me 4", "location": "94110"}
}
If the arguments are not in your knowledge base, please clarify with the user. Do NOT add any prefix or
suffix to the above blob.

3. Combine Responses: Combine your internal knowledge with the results obtained from the API data to give
a complete response to the user.

Additional Guidelines:
1. Be concise but informative in your responses.
2. Always verify the accuracy of movie details when fetching from the API, and prioritize the latest information.
3. If the user asks for recommendations or lists, curate results from the API based on genres, trends, and actors.
Returns the top 5 results only, unless the user is asking for more.
4. Avoid making duplicate function calls. If the user asks for the same information you've already 
provided, don't call the API function again.

These are the available API functions you can call:
get_now_playing_movies(): returns a list of movies currently in theaters.
get_showtimes(title, location): given a movie title and a location, returns the showtimes for that movie in that location (zip code).
buy_ticket(theater, movie, showtime): given a theater, movie, and showtime, allows the user to buy a ticket for that movie at that theater and showtime.
get_reviews(movie_id): given a movie ID, returns the reviews for that movie.
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

@cl.on_message
@observe()
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])
    message_history.append({"role": "user", "content": message.content})
    
    response_message = await generate_response(client, message_history, gen_kwargs)

    # Check if the response is a function call
    # Function calls look like this: {"function_name": "get_showtimes", "args": {"title": "Despicable Me 4", "location": "94110"}}
    # args can be {} if there function expects no arguments
    try:
        function_call = json.loads(response_message.content)
        if "function_name" in function_call and "args" in function_call:
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
            else:
                result = f"Error: Unknown function '{function_name}'"

            # Append the function result to the message history
            message_history.append({"role": "system", "content": result})

            # Generate a new response incorporating the function results
            response_message = await generate_response(client, message_history, gen_kwargs)            
    except json.JSONDecodeError:
        # If it's not a valid JSON, it's not a function call, so we do nothing
        pass
    
    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)

if __name__ == "__main__":
    cl.main()
