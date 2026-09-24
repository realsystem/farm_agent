import asyncio
from agents import Agent, Runner


agent = Agent(
    name="Farm Assistant",
    instructions="""
    You are a simple assistant running on a remote farm.
    Keep your answers short and practical.
    """
)


async def main():
    result = await Runner.run(
        agent,
        "Say hello and confirm that you are running on the remote Raspberry Pi."
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