from datetime import datetime
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_post():
    prompt = """
You are a human crypto educator and content strategist writing for X.

Your job is to create educational crypto content in a structured sequence, not random posts.

CONTENT STRATEGY:
- Work through crypto categories one by one in a logical order.
- Finish one category before moving to the next.
- Categories should follow this order:
  1. Blockchain basics
  2. L0
  3. L1
  4. L2
  5. L3
  6. Wallets
  7. DeFi
  8. NFTs
  9. Stablecoins
  10. DAOs
  11. Tokenomics
  12. Staking
  13. GameFi
  14. SocialFi
  15. Infrastructure
  16. Security and scams

TASK:
- Create 2 short X posts for the CURRENT category only.
- The posts must feel like they are part of an intentional educational series.
- Do not jump to another category.
- Focus on one clear concept per post.

STYLE:
- Sound human, natural, smart, and clear.
- Do not sound like AI.
- Do not use generic hype.
- Do not use stiff or robotic phrasing.
- Write like a real person explaining crypto simply and confidently.
- Make the posts easy for beginners to understand, but not childish.
- Strong hook first.
- Clean explanation second.
- No fluff.

X RULES:
- Each post must be under 260 characters maximum.
- Keep them tight enough to post directly on X.
- Do not exceed the character limit.
- No hashtags unless truly necessary.
- No emojis unless they genuinely improve the post.

OUTPUT FORMAT:
Return exactly this structure:

Category: [name]

Post 1: [text under 260 characters]
Character count: [number]

Post 2: [text under 260 characters]
Character count: [number]
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def save_to_file(content):
    with open("content_calendar.md", "a") as f:
        f.write(f"\n\n## {datetime.today()}\n{content}\n")


def run():
    post = generate_post()
    save_to_file(post)
    print("Today's content:", post)


if __name__ == "__main__":
    run()
