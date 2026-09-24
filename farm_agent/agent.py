import asyncio
import json
import os
import urllib.request

from agents import Agent, Runner, function_tool
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

@function_tool
def discover_entities() -> str:
    """Discover useful farm entities available in Home Assistant."""

    url = "http://supervisor/core/api/states"

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {os.environ['SUPERVISOR_TOKEN']}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            states = json.loads(response.read())

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


@function_tool
def get_entity_state(entity_id: str) -> str:
    """Get the current state of a specific Home Assistant entity."""

    allowed = (
        entity_id.startswith("sensor.eco_worthy_")
        or entity_id.startswith("sensor.smartshunt_")
        or entity_id == "sun.sun"
    )

    if not allowed:
        return "Entity is not available through this tool."

    url = f"http://supervisor/core/api/states/{entity_id}"

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {os.environ['SUPERVISOR_TOKEN']}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            data = json.loads(response.read())

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


agent = Agent(
    name="Farm Assistant",
    instructions="""
    You are an assistant monitoring a remote farm.

    When answering questions about Home Assistant data:
    1. Use discover_entities() to find relevant entities.
    2. Use get_entity_state() to retrieve the actual value.
    3. Do not guess values.

    Keep answers short and practical.
    """,
    tools=[
        discover_entities,
        get_entity_state,
    ],
)


async def ask_agent(question):
    result = await Runner.run(
        agent,
        question
    )

    return result.final_output


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
            response = json.dumps({
                "error": str(e)
            }).encode("utf-8")

            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)


def main():
    server = HTTPServer(("127.0.0.1", 8080), RequestHandler)

    print("=== FARM AGENT HTTP SERVER ===")
    print("Listening on 127.0.0.1:8080 (localhost only)")

    server.serve_forever()


if __name__ == "__main__":
    main()