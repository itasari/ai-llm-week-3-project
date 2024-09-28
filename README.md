# Max Academy Week 3 Project - Function Calling

This is the repo for Max Academy's [Week 3 project](https://hackmd.io/9GbIUAAxSgqXzYyJDbwzVg?view#Practical-LLM-Bootcamp-for-Devs), 
where we're exploring function calling in LLMs.

## Week 3 Project Milestones

- [x] Milestone 1: Create Chainlit starter
- [x] Milestone 2: Calling a function – fetch now playing movies
- [x] Milestone 3: Calling multiple functions – fetch showtimes
- [x] Milestone 4: Chaining functions
- [x] Milestone 5: Calling functions with user confirmation – Buying tickets
- [ ] Milestone 6 (optional): Integrating with RAG
- [ ] Milestone 7 (optional): Using OpenAI function calling

## Getting Started

### 1. Create a virtual environment

First, create a virtual environment to isolate the project dependencies:
```bash
python -m venv .venv
```

### 2. Activate the virtual environment:

- On Windows:
  ```bash
  .venv\Scripts\activate
  ```
- On macOS and Linux:
  ```bash
  source .venv/bin/activate
  ```

### 3. Install dependencies

Install the project dependencies from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

- Copy the `.env.sample` file to a new file named `.env`
- Fill in the `.env` file with your API keys

## Running the app

To run the app, use the following command:

```bash
chainlit run app.py -w
``` 

## Updating dependencies

If you need to update the project dependencies, follow these steps:

1. Update the `requirements.in` file with the new package or version.

2. Install `pip-tools` if you haven't already:
   ```bash
   pip install pip-tools
   ```

3. Compile the new `requirements.txt` file:
   ```bash
   pip-compile requirements.in
   ```

4. Install the updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

This process ensures that all dependencies are properly resolved and pinned to specific versions for reproducibility.
