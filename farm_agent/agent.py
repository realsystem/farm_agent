import asyncio
import json
import os
import urllib.request

from agents import Agent, Runner, function_tool


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

    When the user asks about the battery, use the get_battery_status tool.

    Explain the result briefly and practically.
    Do not invent values that are not provided by the tool.
    """,
    tools=[get_battery_status],
)


async def main():
    result = await Runner.run(
        agent,
        "How is the farm battery doing right now?"
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