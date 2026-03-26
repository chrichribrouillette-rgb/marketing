"""
Marketing Content Agent — Entry Point

Usage:
    python main.py

Set your API key before running:
    export ANTHROPIC_API_KEY="your-key-here"

Or create a .env file with:
    ANTHROPIC_API_KEY=your-key-here
"""

import os
from dotenv import load_dotenv
from agents import ContentAgent

load_dotenv()

EXAMPLE_REQUESTS = [
    (
        "Write a social media campaign for our new product launch",
        {
            "brand_name": "Lumio",
            "topic": "Launch of our AI-powered scheduling app",
            "platforms": "LinkedIn, Instagram, Twitter",
            "tone": "professional yet exciting",
        },
    ),
    (
        "Create an email campaign to re-engage inactive customers",
        {
            "brand_name": "Lumio",
            "subject": "We miss you — here's something special",
            "target_audience": "customers who haven't logged in for 60+ days",
            "key_message": "We've added 10 new features since you last visited",
            "call_to_action": "Come back and explore what's new",
        },
    ),
    (
        "Write Google Search ad copy for our premium plan",
        {
            "brand_name": "Lumio",
            "product_or_service": "Lumio Pro — AI scheduling for teams",
            "unique_selling_point": "Saves teams 5 hours per week on scheduling",
            "ad_format": "Google Search",
            "target_audience": "project managers at mid-size companies",
        },
    ),
]


def run_interactive():
    """Run the agent in interactive chat mode."""
    print("Marketing Content Agent")
    print("=" * 40)
    print("Type your content request, or 'quit' to exit.")
    print("Type 'reset' to start a new conversation.\n")

    brand_context = input("Enter brand context (press Enter to skip): ").strip()
    agent = ContentAgent(brand_context=brand_context)
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("Conversation reset.\n")
            continue

        print("\nAgent: Generating content...\n")
        result = agent.run(user_input)
        print(result)
        print()


def run_examples():
    """Run preset example requests to demonstrate the agent."""
    print("Marketing Content Agent — Example Demo")
    print("=" * 40)

    brand_context = (
        "Lumio is a B2B SaaS company offering AI-powered scheduling tools for teams. "
        "Brand voice: professional, clear, and forward-thinking."
    )
    agent = ContentAgent(brand_context=brand_context)

    for i, (request, _) in enumerate(EXAMPLE_REQUESTS, 1):
        print(f"\n[Example {i}] {request}")
        print("-" * 40)
        result = agent.run(request)
        print(result)
        print()
        agent.reset()


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY is not set.")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        exit(1)

    import sys
    if "--demo" in sys.argv:
        run_examples()
    else:
        run_interactive()
