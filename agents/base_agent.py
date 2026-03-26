"""
Base Marketing Agent.

All industry-specific agents inherit from BaseMarketingAgent.
Few-shot examples are prepended to every conversation so Claude
learns the expected content structure and tone for the industry.
"""

import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"

BASE_SYSTEM_PROMPT = """You are an expert marketing copywriter working inside a specialized marketing agency.
You produce compelling, on-brand content across multiple channels.
Always match the industry tone, vocabulary, and content structure shown in the examples.
When brand voice, target audience, or key message are missing, infer sensible defaults from the industry context."""


@beta_tool
def write_email_campaign(
    subject: str,
    brand_name: str,
    target_audience: str,
    key_message: str,
    call_to_action: str,
) -> str:
    """Write a full marketing email campaign including subject line, body, and CTA.

    Args:
        subject: The email subject line.
        brand_name: Name of the brand or company.
        target_audience: Who the email is targeting (e.g. "small business owners").
        key_message: The core value proposition or message to convey.
        call_to_action: The desired action for the reader (e.g. "Book a free demo").
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=BASE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write a marketing email for {brand_name}.\n"
                    f"Subject: {subject}\n"
                    f"Audience: {target_audience}\n"
                    f"Key message: {key_message}\n"
                    f"CTA: {call_to_action}\n\n"
                    "Format: Subject line, preview text, greeting, body (2-3 paragraphs), CTA button text, sign-off."
                ),
            }
        ],
    )
    return response.content[0].text


@beta_tool
def write_social_posts(
    brand_name: str,
    topic: str,
    platforms: str,
    tone: str,
) -> str:
    """Write social media posts optimized for specified platforms.

    Args:
        brand_name: Name of the brand or company.
        topic: The topic or campaign theme for the posts.
        platforms: Comma-separated list of platforms (e.g. "LinkedIn, Instagram, TikTok").
        tone: The desired tone (e.g. "professional", "playful", "inspirational").
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=BASE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write social media posts for {brand_name} about: {topic}\n"
                    f"Platforms: {platforms}\n"
                    f"Tone: {tone}\n\n"
                    "Write one optimized post per platform, respecting character limits and best practices. "
                    "Include relevant hashtags."
                ),
            }
        ],
    )
    return response.content[0].text


@beta_tool
def write_ad_copy(
    brand_name: str,
    product_or_service: str,
    unique_selling_point: str,
    ad_format: str,
    target_audience: str,
) -> str:
    """Write advertising copy for digital or print ads.

    Args:
        brand_name: Name of the brand or company.
        product_or_service: What is being advertised.
        unique_selling_point: The main differentiator or benefit.
        ad_format: Type of ad (e.g. "Google Search", "Facebook Banner", "Meta Reel").
        target_audience: Who the ad is targeting.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=BASE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write {ad_format} ad copy for {brand_name}.\n"
                    f"Product/Service: {product_or_service}\n"
                    f"USP: {unique_selling_point}\n"
                    f"Audience: {target_audience}\n\n"
                    "Include headline, body copy, and CTA. Follow platform best practices for length."
                ),
            }
        ],
    )
    return response.content[0].text


@beta_tool
def write_blog_outline(
    brand_name: str,
    topic: str,
    target_keywords: str,
    audience_pain_point: str,
) -> str:
    """Create a detailed SEO-friendly blog post outline.

    Args:
        brand_name: Name of the brand or company.
        topic: The blog post topic or title idea.
        target_keywords: Comma-separated SEO keywords to target.
        audience_pain_point: The reader problem this post solves.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=BASE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Create a detailed blog outline for {brand_name}.\n"
                    f"Topic: {topic}\n"
                    f"Target keywords: {target_keywords}\n"
                    f"Audience pain point: {audience_pain_point}\n\n"
                    "Include: suggested title (with primary keyword), meta description, "
                    "introduction hook, H2/H3 section headers with brief descriptions, "
                    "and a conclusion with CTA."
                ),
            }
        ],
    )
    return response.content[0].text


TOOLS = [write_email_campaign, write_social_posts, write_ad_copy, write_blog_outline]


class BaseMarketingAgent:
    """Base class for all industry-specific marketing agents.

    Subclasses set:
        INDUSTRY           — display name (e.g. "Fashion B2C")
        INDUSTRY_PROMPT    — appended to the system prompt with industry-specific guidance
        FEW_SHOT_EXAMPLES  — list of (user_message, assistant_message) tuples shown
                             before every conversation so Claude learns the expected
                             content structure and tone for the industry
    """

    INDUSTRY: str = "General"
    INDUSTRY_PROMPT: str = ""
    FEW_SHOT_EXAMPLES: list[tuple[str, str]] = []

    def __init__(self, brand_context: str = ""):
        self.brand_context = brand_context
        self.history: list[dict] = []

    def _system(self) -> str:
        parts = [BASE_SYSTEM_PROMPT]
        if self.INDUSTRY_PROMPT:
            parts.append(self.INDUSTRY_PROMPT)
        if self.brand_context:
            parts.append(f"Brand context: {self.brand_context}")
        return "\n\n".join(parts)

    def _messages(self, user_request: str) -> list[dict]:
        """Build message list: few-shot examples → history → current request."""
        messages: list[dict] = []
        for user_ex, assistant_ex in self.FEW_SHOT_EXAMPLES:
            messages.append({"role": "user", "content": user_ex})
            messages.append({"role": "assistant", "content": assistant_ex})
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_request})
        return messages

    def run(self, user_request: str) -> str:
        """Process a content request and return the generated content."""
        self.history.append({"role": "user", "content": user_request})

        runner = client.beta.messages.tool_runner(
            model=MODEL,
            max_tokens=4096,
            system=self._system(),
            tools=TOOLS,
            messages=self._messages(user_request),
        )

        final_message = None
        for message in runner:
            final_message = message

        result = ""
        if final_message:
            for block in final_message.content:
                if hasattr(block, "text"):
                    result = block.text
                    break
            self.history.append({"role": "assistant", "content": final_message.content})

        return result

    def reset(self):
        """Clear conversation history (few-shot examples are always preserved)."""
        self.history = []
