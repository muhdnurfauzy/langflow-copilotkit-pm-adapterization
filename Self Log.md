Here is a comprehensive, production-ready setup and installation section you can copy directly into your `Self Log.md` (or `README.md`).

---

# Langflow + CopilotKit Adapterization: System Setup & Installation Guide

## Architecture Overview

This application decouples the user interface, protocol translation, workflow orchestration, and model inference into four independent layers:

* **Frontend:** React + Vite + TypeScript powered by CopilotKit AG-UI runtime.
* **Adapter Bridge:** FastAPI (`main.py`) translating CopilotKit SSE events to Langflow execution payloads.
* **Orchestration Layer:** Langflow canvas managing the prompt pipeline and graph execution.
* **Inference Engine:** Groq Cloud LPU running high-performance models (e.g., `openai/gpt-oss-20b` or `llama-3.1-8b-instant`).

---

## Prerequisites

Ensure the following tools are installed on your system:

* **Python 3.10+** (tested on Python 3.11 / 3.12 / 3.14)
* **Node.js 18+** and `npm`
* **Groq Cloud API Key** (from [console.groq.com/keys](https://console.groq.com/keys?utm_source=gemini))

---

## 1. Repository & Backend Setup

### Clone the Repository

```powershell
git clone <repository_url>
cd langflow-copilotkit-pm-adapterization

```

### Python Virtual Environment Setup

Create and activate a Python virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate

```

### Install Backend Dependencies

```powershell
pip install fastapi uvicorn httpx python-dotenv openai langflow

```

### Configure Environment Variables

Copy the template configuration file:

```powershell
copy .env.example .env

```

Open `.env` and fill in your values:

```env
LANGFLOW_BASE_URL=http://127.0.0.1:7860
LANGFLOW_FLOW_ID=your_langflow_flow_id_here
LANGFLOW_API_KEY=your_langflow_api_key_here

```

> **Note:** Never commit the `.env` file to Git. Keep credentials confidential.

---

## 2. Langflow Flow Configuration

### Start Langflow

Open a dedicated terminal and run:

```powershell
langflow run

```

Langflow will be accessible at `http://localhost:7860`.

### Canvas Setup

1. Create a new flow (e.g., `langflow-copilotkit-pm`).


2. Add three nodes to the canvas:
* **Chat Input**
* **Custom Component: Groq Cloud Model**
* **Chat Output**


3. Create a **`+ New Custom Component`**, click **`</> Code`**, and paste:



```python
from langflow.custom import Component
from langflow.io import MessageTextInput, SecretStrInput, StrInput, FloatInput, Output
from langflow.schema.message import Message
from openai import OpenAI


class GroqCloudModel(Component):
    display_name = "Groq Cloud Model"
    description = "Ultra-fast Groq Cloud Inference."
    icon = "zap"
    name = "GroqCloudModel"

    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Input",
            info="The incoming user prompt or message.",
        ),
        MessageTextInput(
            name="system_message",
            display_name="System Message",
            info="System instructions.",
            value="You are an intelligent, helpful AI assistant.",
        ),
        StrInput(
            name="model_name",
            display_name="Model Name",
            info="Groq model ID.",
            value="openai/gpt-oss-20b",
        ),
        SecretStrInput(
            name="api_key",
            display_name="Groq API Key",
            info="Groq API key (starts with gsk_...).",
            value="",
        ),
        FloatInput(
            name="temperature",
            display_name="Temperature",
            value=0.7,
        ),
    ]

    outputs = [
        Output(display_name="Model Response", name="response", method="generate_response"),
    ]

    def generate_response(self) -> Message:
        user_text = ""
        if hasattr(self.input_value, "text"):
            user_text = self.input_value.text
        else:
            user_text = str(self.input_value or "")

        messages = []
        if self.system_message:
            sys_text = self.system_message.text if hasattr(self.system_message, "text") else str(self.system_message)
            if sys_text.strip():
                messages.append({"role": "system", "content": sys_text})

        messages.append({"role": "user", "content": user_text})

        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_key.strip() if self.api_key else "",
            timeout=30.0,
        )

        response = client.chat.completions.create(
            model=self.model_name.strip(),
            messages=messages,
            temperature=self.temperature,
        )

        reply = response.choices[0].message.content or ""
        return Message(text=reply)

```

4. Click **Check & Save**.
5. On the component node:
* **Model Name:** `openai/gpt-oss-20b` (or `llama-3.1-8b-instant`)
* **Groq API Key:** Paste your Groq API key (`gsk_...`)


6. Connect the nodes:
* `Chat Input` (`Chat Message`) $\longrightarrow$ `Groq Cloud Model` (`Input`)
* `Groq Cloud Model` (`Model Response`) $\longrightarrow$ `Chat Output` (`Inputs*`)


7. Generate a Langflow API Key:
* Top-right profile avatar $\rightarrow$ **Settings** $\rightarrow$ **Langflow API Keys** $\rightarrow$ **Add New Key**.
* Copy the key and add it to your `.env` file as `LANGFLOW_API_KEY`.


8. Copy your Flow ID from the browser URL (`http://localhost:7860/flow/<FLOW_ID>`) and set `LANGFLOW_FLOW_ID` in `.env`.

---

## 3. Frontend Setup (CopilotKit)

Open a separate terminal:

```powershell
cd frontend
npm install

```

---

## 4. Running the Complete System

To run the full stack, keep 3 terminals running:

| Service | Terminal Command | Endpoint |
| --- | --- | --- |
| **1. Langflow** | `langflow run` | `http://localhost:7860`<br> |
| **2. FastAPI Adapter** | `python main.py` | `[http://127.0.0.1:8000](http://127.0.0.1:8000)`<br> |
| **3. React UI** | `cd frontend; npm run dev` | `http://localhost:5173`<br> |

---

## 5. Verification

1. Open `http://localhost:5173/` in your browser.


2. Send `hi` into the chat input.


3. The CopilotKit chat bubble will display the response generated from the Groq cloud model, while the FastAPI terminal logs the token payload with valid authentication.