import os
import json
import uuid
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Load environment variables from .env
load_dotenv()

app = FastAPI(title="Langflow CopilotKit Adapter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LANGFLOW_BASE_URL = os.getenv("LANGFLOW_BASE_URL", "http://127.0.0.1:7860")
LANGFLOW_FLOW_ID = os.getenv("LANGFLOW_FLOW_ID", "3ac06eaa-2f73-4c2d-b343-8c1881cf0cfc")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY", "")


def format_agui_event(event_type: str, data: dict) -> str:
    """Format an AG-UI Server-Sent Event for CopilotKit."""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload)}\n\n"


@app.get("/copilotkit/info")
@app.get("/info")
async def copilotkit_info():
    """Agent discovery endpoint compatible with CopilotKit runtime sync."""
    agent_spec = {
        "name": "default",
        "description": "Langflow assistant via CopilotKit",
    }
    return {
        "agents": {
            "default": agent_spec
        },
        "agentList": [
            {"id": "default", **agent_spec}
        ],
    }


@app.post("/copilotkit/agent/{agent_id}/connect")
@app.post("/agent/{agent_id}/connect")
async def copilotkit_connect(agent_id: str):
    return {"status": "connected", "agent_id": agent_id}


@app.post("/copilotkit/agent/{agent_id}/run")
@app.post("/agent/{agent_id}/run")
async def copilotkit_run(agent_id: str, request: Request):
    body = await request.json()
    thread_id = body.get("threadId", str(uuid.uuid4()))
    run_id = body.get("runId", str(uuid.uuid4()))
    message_id = str(uuid.uuid4())

    user_prompt = ""
    messages = body.get("messages", [])
    if messages:
        last_msg = messages[-1]
        content = last_msg.get("content", "")
        if isinstance(content, str):
            user_prompt = content
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    user_prompt += part.get("text", "")

    if not user_prompt:
        user_prompt = body.get("input", "hi")

    print(f"[DEBUG] Running agent '{agent_id}' for prompt: '{user_prompt}'")

    langflow_url = f"{LANGFLOW_BASE_URL}/api/v1/run/{LANGFLOW_FLOW_ID}?stream=false"
    langflow_payload = {
        "input_value": user_prompt,
        "input_type": "chat",
        "output_type": "chat",
    }

    # Prepare headers including authentication
    headers = {
        "Content-Type": "application/json",
    }
    if LANGFLOW_API_KEY:
        headers["x-api-key"] = LANGFLOW_API_KEY

    async def event_generator():
        # 1. Lifecycle start
        yield format_agui_event("RUN_STARTED", {"threadId": thread_id, "runId": run_id})
        yield format_agui_event(
            "TEXT_MESSAGE_START",
            {"messageId": message_id, "role": "assistant"},
        )

        extracted_text = ""

        try:
            print(f"[DEBUG] Calling Langflow at: {langflow_url} (Auth: {'Yes' if LANGFLOW_API_KEY else 'No'})")
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(langflow_url, json=langflow_payload, headers=headers)
                if res.status_code == 200:
                    payload = res.json()
                    try:
                        flow_output = payload["outputs"][0]["outputs"][0]
                        artifacts = flow_output.get("artifacts", {})
                        extracted_text = artifacts.get("message") or artifacts.get("text") or ""
                        if not extracted_text and "results" in flow_output:
                            res_msg = flow_output["results"].get("message", {})
                            extracted_text = res_msg.get("text") or res_msg.get("data", {}).get("text") or ""
                    except Exception as parse_err:
                        print(f"[DEBUG] Parse error: {parse_err}")
                else:
                    extracted_text = f"Langflow error (HTTP {res.status_code}): {res.text}"
        except Exception as e:
            print(f"[DEBUG] Bridge Exception: {e}")
            extracted_text = f"Error: {e}"

        if not extracted_text:
            extracted_text = "I received your message, but no content was returned by the model."

        # Emit text response
        yield format_agui_event(
            "TEXT_MESSAGE_CONTENT",
            {"messageId": message_id, "delta": str(extracted_text)},
        )

        print(f"[DEBUG] Sent full response ({len(str(extracted_text))} chars) to client.")

        # 2. Lifecycle end
        yield format_agui_event("TEXT_MESSAGE_END", {"messageId": message_id})
        yield format_agui_event("RUN_FINISHED", {"threadId": thread_id, "runId": run_id})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)