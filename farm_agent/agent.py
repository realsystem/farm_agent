# import asyncio
# from agents import Agent, Runner


# agent = Agent(
#     name="Farm Assistant",
#     instructions="""
#     You are a simple assistant running on a remote farm.
#     Keep your answers short and practical.
#     """
# )


# async def main():
#     result = await Runner.run(
#         agent,
#         "Say hello and confirm that you are running on the remote Raspberry Pi."
#     )

#     print("=== AGENT RESPONSE ===")
#     print(result.final_output)

#     usage = result.context_wrapper.usage

#     print("=== USAGE ===")
#     print(f"API requests: {usage.requests}")
#     print(f"Input tokens: {usage.input_tokens}")
#     print(f"Output tokens: {usage.output_tokens}")
#     print(f"Total tokens: {usage.total_tokens}")


# if __name__ == "__main__":
#     asyncio.run(main())
import os
import urllib.request
import json

ENTITY_ID = "sensor.eco_worthy_0b_89a2_battery"

url = f"http://supervisor/core/api/states/{ENTITY_ID}"

request = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {os.environ['SUPERVISOR_TOKEN']}",
        "Content-Type": "application/json",
    },
)

with urllib.request.urlopen(request, timeout=5) as response:
    data = json.loads(response.read())

print("=== HOME ASSISTANT RESPONSE ===")
print(json.dumps(data, indent=2))