import asyncio
from agents.lesson_plan_agent import LessonPlanAgent

async def test_agent():
    agent = LessonPlanAgent()
    # Simulate a user message for semantic search
    result = await agent.execute("Describe a hands-on activity for students to build bridges using craft sticks and learn about engineering concepts.", {}, None)
    print(result["message"])
    # Print each metadata dict in result["data"]
    for meta in result["data"]:
        print(meta)

asyncio.run(test_agent())