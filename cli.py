"""
Non-interactive CLI wrapper for marketing agents.

Used by the Claude Code /marketing slash command.

Usage:
    python cli.py <industry_number> "<your content request>"
    python cli.py <industry_number> "<request>" --brand "<brand context>"

Examples:
    python cli.py 1 "Write an Instagram caption for our summer drop"
    python cli.py 2 "Write an email for our new serum" --brand "Glossier, minimalist skincare"
"""

import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

INDUSTRIES = {
    "1": "Fashion B2C",
    "2": "Beauty B2C",
    "3": "Self-Development & Coaching",
    "4": "B2B Manufacturing",
    "5": "Food & Beverage",
    "6": "Health & Wellness",
    "7": "Travel & Hospitality",
    "8": "Real Estate",
    "9": "Finance & Fintech",
    "10": "Education & EdTech",
}


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY is not set.")
        print("Run: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Marketing Content Agent CLI")
    parser.add_argument("industry", help="Industry number (1-10). Run with --list to see options.")
    parser.add_argument("request", nargs="?", default="", help="Your content request")
    parser.add_argument("--brand", default="", help="Brand context (optional)")
    parser.add_argument("--list", action="store_true", help="List all available industries")
    args = parser.parse_args()

    if args.list:
        print("Available industries:")
        for key, name in INDUSTRIES.items():
            print(f"  {key:>2}.  {name}")
        return

    if args.industry not in INDUSTRIES:
        print(f"Error: '{args.industry}' is not a valid industry number.")
        print("Run with --list to see all options.")
        sys.exit(1)

    if not args.request:
        print("Error: please provide a content request.")
        print('Example: python cli.py 1 "Write an Instagram caption for our new drop"')
        sys.exit(1)

    from agents import INDUSTRY_AGENTS
    agent_class = INDUSTRY_AGENTS[args.industry]
    agent = agent_class(brand_context=args.brand)

    print(f"[{agent_class.INDUSTRY}] Generating content...\n")
    result = agent.run(args.request)
    print(result)


if __name__ == "__main__":
    main()
