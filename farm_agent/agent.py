import asyncio
import json
import os
import urllib.request

from agents import Agent, Runner, function_tool


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

    with urllib.request.urlopen(request, timeout=5) as response:
        data = json.loads(response.read())

    return json.dumps({
        "entity_id": data["entity_id"],
        "state": data["state"],
        "attributes": data.get("attributes", {}),
    })


@function_tool
def get_battery_status() -> str:
    """Get the current battery status from Home Assistant."""

    entity_ids = [
        "sensor.eco_worthy_0b_89a2_battery",
        "sensor.eco_worthy_0b_89a2_current",
        "sensor.eco_worthy_0b_89a2_temperature",
        "sensor.eco_worthy_0b_89a2_voltage",
    ]

    results = {}

    for entity_id in entity_ids:
        url = f"http://supervisor/core/api/states/{entity_id}"

        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {os.environ['SUPERVISOR_TOKEN']}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(request, timeout=5) as response:
            data = json.loads(response.read())

        results[entity_id] = {
            "state": data["state"],
            "unit": data["attributes"].get("unit_of_measurement"),
        }

    return json.dumps(results)


agent = Agent(
    name="Farm Assistant",
    instructions="""
    You are an assistant monitoring a remote farm.

    When answering questions about Home Assistant data:
    1. Use discover_entities() to find relevant entities.
    2. Use get_entity_state() to retrieve the actual value.
    3. Do not guess values.

    Keep answers short and practical.
    """
    tools=[
        discover_entities,
        get_entity_state,
    ],
)


async def main():
    result = await Runner.run(
        agent,
        "Which battery voltage sensors are available, and what are their current values?"
    )

    print("=== AGENT RESPONSE ===")
    print(result.final_output)

    usage = result.context_wrapper.usage

    print("=== USAGE ===")
    print(f"API requests: {usage.requests}")
    print(f"Input tokens: {usage.input_tokens}")
    print(f"Output tokens: {usage.output_tokens}")
    print(f"Total tokens: {usage.total_tokens}")


if __name__ == "__main__":
    asyncio.run(main())