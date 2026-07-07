# Blog Generator

A Streamlit app that uses a LangGraph workflow to research, draft, and review blog posts with a human-in-the-loop approval step.

## Overview

The app walks a topic through three stages:

1. Research - gathers key talking points for the topic.
2. Writing - turns the research notes into a full blog draft.
3. Editing - generates critique and waits for human approval or revision feedback.

The UI lets you start a workflow from the sidebar, review the generated draft, send it back for revision, approve it, and download the result as a PDF.

## Features

- Interactive Streamlit interface
- Multi-agent blog generation workflow
- Human approval / revision loop
- Workflow progress tracking
- PDF download for draft and final post
- Local LLM integration through Ollama

## Requirements

- Python 3.10+ recommended
- Ollama installed and running locally
- A model available that matches the value in [agent.py](agent.py) `ChatOllama(model="gemma4:31b-cloud", ...)`

## Installation

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirment.txt
   ```

3. Start Ollama and make sure the configured model is available.

## Running the app

```bash
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal, enter a blog topic, and start the workflow from the sidebar.

## Project Structure

- [app.py](app.py) - Streamlit UI and workflow controls
- [graph.py](graph.py) - LangGraph workflow definition and state management
- [agent.py](agent.py) - Research, writing, and editing nodes
- [state.py](state.py) - Shared TypedDict state definition
- [requirment.txt](requirment.txt) - Python dependencies

## Notes

- The workflow pauses after the editor step so you can approve the draft or send revision instructions.
- If you change the Ollama model, update [agent.py](agent.py).
