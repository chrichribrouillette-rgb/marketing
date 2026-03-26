"""
Marketing Content Agents — Entry Point

Usage:
    python main.py              # interactive mode (choose industry)
    python main.py --demo       # run preset examples

Set your API key before running:
    export ANTHROPIC_API_KEY="your-key-here"

Or create a .env file with:
    ANTHROPIC_API_KEY=your-key-here
"""

import os
import sys
from dotenv import load_dotenv
from agents import INDUSTRY_AGENTS

load_dotenv()

INDUSTRY_MENU = """
Select your industry:

  1.  Fashion B2C
  2.  Beauty B2C
  3.  Self-Development & Coaching
  4.  B2B Manufacturing
  5.  Food & Beverage
  6.  Health & Wellness
  7.  Travel & Hospitality
  8.  Real Estate
  9.  Finance & Fintech
  10. Education & EdTech
"""

DEMO_REQUESTS: dict[str, list[str]] = {
    "1": [
        "Write an Instagram caption for our new autumn/winter collection drop.",
        "Write a re-engagement email for customers who haven't purchased in 60 days.",
    ],
    "2": [
        "Write a TikTok caption for our new SPF 50 tinted moisturiser launch.",
        "Write a Google Search ad for our anti-aging vitamin C serum.",
    ],
    "3": [
        "Write a LinkedIn post promoting our new 6-week productivity masterclass.",
        "Write a webinar invite email for a free session on building morning routines.",
    ],
    "4": [
        "Write a LinkedIn post about our new ISO 9001:2015 certification.",
        "Write a cold outreach email to engineering managers at medical device companies.",
    ],
    "5": [
        "Write Instagram and TikTok captions for our new oat milk cold brew launch.",
        "Write a product launch email for our new craft hot sauce subscription box.",
    ],
    "6": [
        "Write an Instagram post for our new ashwagandha stress support supplement.",
        "Write a welcome email for someone who just purchased our 30-day gut health programme.",
    ],
    "7": [
        "Write an Instagram caption for a boutique eco-lodge in Costa Rica.",
        "Write a promotional email for our early bird summer packages.",
    ],
    "8": [
        "Write a listing description for a 2-bed luxury apartment in Miami Beach.",
        "Write a Facebook ad targeting homeowners thinking about selling.",
    ],
    "9": [
        "Write an Instagram post for our new cashback rewards feature.",
        "Write an onboarding email for a new user who just opened a savings account.",
    ],
    "10": [
        "Write a LinkedIn ad for our 12-week UX design bootcamp.",
        "Write a nurture email for someone who downloaded our free career-change guide.",
    ],
}


def pick_industry() -> tuple[str, type]:
    """Prompt user to pick an industry and return (key, agent_class)."""
    print(INDUSTRY_MENU)
    while True:
        choice = input("Enter number (1-10): ").strip()
        if choice in INDUSTRY_AGENTS:
            agent_class = INDUSTRY_AGENTS[choice]
            print(f"\nSelected: {agent_class.INDUSTRY}\n")
            return choice, agent_class
        print("Invalid choice. Please enter a number between 1 and 10.")


def run_interactive():
    """Run the agent in interactive chat mode."""
    print("Marketing Content Agents")
    print("=" * 40)

    industry_key, agent_class = pick_industry()

    brand_context = input("Enter brand context (press Enter to skip): ").strip()
    agent = agent_class(brand_context=brand_context)

    print(f"\n{agent_class.INDUSTRY} agent ready.")
    print("Type your content request, 'reset' to start a new conversation, or 'quit' to exit.\n")

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

        print(f"\n[{agent_class.INDUSTRY}] Generating content...\n")
        result = agent.run(user_input)
        print(result)
        print()


def run_demo():
    """Run preset example requests for all industries."""
    print("Marketing Content Agents — Demo Mode")
    print("=" * 40)

    industry_key, agent_class = pick_industry()
    requests = DEMO_REQUESTS.get(industry_key, [])

    brand_context = f"Demo brand for {agent_class.INDUSTRY} industry."
    agent = agent_class(brand_context=brand_context)

    for i, request in enumerate(requests, 1):
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
        sys.exit(1)

    if "--demo" in sys.argv:
        run_demo()
    else:
        run_interactive()
