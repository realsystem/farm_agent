import asyncio
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from openai import OpenAI


def _get_ha_config():
    """Get Home Assistant configuration from environment variables."""
    ha_api_url = os.environ.get("HA_API_URL")
    ha_token = os.environ.get("HA_TOKEN")
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN")

    if ha_api_url:
        if not ha_token:
            raise ValueError("HA_TOKEN must be set when HA_API_URL is configured")
        return ha_api_url, ha_token

    ha_api_url = "http://supervisor/core/api"
    if not supervisor_token:
        raise ValueError(
            "SUPERVISOR_TOKEN not set and HA_API_URL not configured. "
            "Set one of: (HA_API_URL + HA_TOKEN) or SUPERVISOR_TOKEN"
        )
    return ha_api_url, supervisor_token


def _make_ha_request(endpoint: str) -> dict:
    """Make an authenticated request to Home Assistant API."""
    ha_api_url, token = _get_ha_config()
    url = f"{ha_api_url}{endpoint}"

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception as e:
        raise


def discover_entities() -> str:
    """Discover useful farm entities available in Home Assistant."""
    try:
        states = _make_ha_request("/states")
        entities = []

        for data in states:
            entity_id = data["entity_id"]

            if not (
                entity_id.startswith("sensor.eco_worthy_")
                or entity_id.startswith("sensor.smartshunt_")
                or entity_id == "sun.sun"
            ):
                continue

            attributes = data.get("attributes", {})

            entities.append({
                "entity_id": entity_id,
                "name": attributes.get("friendly_name", entity_id),
                "state": data.get("state"),
                "unit": attributes.get("unit_of_measurement"),
                "device_class": attributes.get("device_class"),
            })

        return json.dumps(entities)
    except urllib.error.URLError:
        return "Home Assistant unavailable"
    except Exception as e:
        return f"Error discovering entities: {str(e)}"


def get_entity_state(entity_id: str) -> str:
    """Get the current state of a specific Home Assistant entity."""
    allowed = (
        entity_id.startswith("sensor.eco_worthy_")
        or entity_id.startswith("sensor.smartshunt_")
        or entity_id == "sun.sun"
    )

    if not allowed:
        return "Entity is not available through this tool."

    try:
        data = _make_ha_request(f"/states/{entity_id}")

        if data is None:
            return f"Entity {entity_id} not found in Home Assistant"

        return json.dumps({
            "entity_id": data["entity_id"],
            "state": data["state"],
            "attributes": data.get("attributes", {}),
        })
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"Entity {entity_id} not found in Home Assistant"
        return f"Home Assistant API error: {e.code}"
    except urllib.error.URLError:
        return "Home Assistant unavailable"
    except Exception as e:
        return f"Error retrieving entity state: {str(e)}"


# Tool definitions for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "discover_entities",
            "description": "Discover useful farm entities available in Home Assistant.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_entity_state",
            "description": "Get the current state of a specific Home Assistant entity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID (e.g., sensor.eco_worthy_0b_89a2_voltage)",
                    }
                },
                "required": ["entity_id"],
            }
        }
    }
]


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return its result."""
    if tool_name == "discover_entities":
        return discover_entities()
    elif tool_name == "get_entity_state":
        return get_entity_state(tool_input.get("entity_id", ""))
    else:
        return f"Unknown tool: {tool_name}"


async def ask_agent(question: str) -> str:
    """Ask the agent a question and return the response."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY not set"

    client = OpenAI(api_key=api_key)

    system_prompt = """You are an assistant monitoring a remote farm.

When answering questions about Home Assistant data:
1. Use discover_entities() to find relevant entities if needed.
2. Use get_entity_state() to retrieve the actual value.
3. Do not guess values.

Keep answers short and practical."""

    messages = [
        {"role": "user", "content": question}
    ]

    # Agentic loop: keep calling tools until we get a final response
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            # If OpenAI API fails, try to at least discover entities locally
            error_msg = str(e)
            if "Connection" in error_msg or "connection" in error_msg:
                # Try to help by discovering entities at least
                try:
                    entities_json = discover_entities()
                    entities = json.loads(entities_json)
                    if entities and not entities_json.startswith("Error"):
                        entity_list = ", ".join([e["entity_id"] for e in entities])
                        return f"Available sensors: {entity_list}"
                except:
                    pass
            raise

        # Check if we're done (no tool calls)
        if response.stop_reason == "end_turn":
            return response.choices[0].message.content

        # Process tool calls
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            return response.choices[0].message.content

        # Add assistant's response to messages
        messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in tool_calls
            ]
        })

        # Execute tools and add results to messages
        tool_results = []
        for tool_call in tool_calls:
            tool_input = json.loads(tool_call.function.arguments)
            tool_result = _execute_tool(tool_call.function.name, tool_input)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": tool_result,
            })

        # Add tool results as user message
        messages.append({
            "role": "user",
            "content": tool_results
        })

    # Max iterations reached
    return "I was unable to complete the request."


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            return

        if parsed.path != "/ask":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        question = params.get("q", [None])[0]

        if not question:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing q parameter")
            return

        self.handle_question(question)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/ask":
            self.send_response(404)
            self.end_headers()
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            data = json.loads(body)
            question = data.get("question")

            if not question:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing question")
                return

            self.handle_question(question)

        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def handle_question(self, question):
        try:
            answer = asyncio.run(ask_agent(question))

            response = json.dumps({
                "answer": answer
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        except Exception as e:
            error_msg = str(e)
            print(f"Error processing question: {error_msg}", file=__import__('sys').stderr)
            import traceback
            traceback.print_exc(file=__import__('sys').stderr)

            response = json.dumps({
                "error": error_msg
            }).encode("utf-8")

            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)


def main():
    host = os.environ.get("AGENT_HOST", "127.0.0.1")
    port = int(os.environ.get("AGENT_PORT", "8080"))
    server = HTTPServer((host, port), RequestHandler)

    print("=== FARM AGENT HTTP SERVER ===")
    print(f"Listening on {host}:{port}")

    server.serve_forever()


if __name__ == "__main__":
    main()