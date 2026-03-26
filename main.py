import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import tweepy
from openai import OpenAI


MODEL = "gpt-4o-mini"
TARGET_MIN = 220
TARGET_MAX = 265

SERIES_NAME = "Parisa's Crypto Fact Series"

CATEGORY_ORDER = [
    "Crypto Foundations",
    "Bitcoin",
    "Ethereum & Smart Contracts",
    "L1 Blockchains",
    "L2 Scaling",
    "DeFi",
    "NFTs & Digital Ownership",
    "ZK Proofs & Privacy",
]

POST_TYPE_SCHEDULE = {
    1: {"morning": "fact_hook", "evening": "context"},
    2: {"morning": "fact_hook", "evening": "context"},
    3: {"morning": "explainer", "evening": "context"},
    4: {"morning": "fact_hook", "evening": "context"},
    5: {"morning": "explainer", "evening": "context"},
    6: {"morning": "fact_hook", "evening": "cta_engage"},
    7: {"morning": "week_summary", "evening": "week_close"},
}

DAY_LABELS = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}

CATEGORY_TOPIC_PLAN: Dict[str, Dict[int, Dict[str, str]]] = {
    "Crypto Foundations": {
        1: {
            "morning": "What crypto is and what a blockchain does",
            "evening": "Why shared ledgers matter in the real world",
        },
        2: {
            "morning": "What decentralization means",
            "evening": "Tradeoffs between decentralization and central control",
        },
        3: {
            "morning": "How consensus works at a high level",
            "evening": "Why agreement between nodes matters",
        },
        4: {
            "morning": "What wallets and keys actually do",
            "evening": "Why self-custody changes responsibility",
        },
        5: {
            "morning": "What tokens are versus what blockchains are",
            "evening": "How tokens get used in ecosystems",
        },
        6: {
            "morning": "Public versus private blockchains",
            "evening": "Ask what part of crypto confuses people most",
        },
        7: {
            "morning": "Weekly recap of core crypto foundations",
            "evening": "Close the week and tease Bitcoin next",
        },
    },
    "Bitcoin": {
        1: {
            "morning": "What Bitcoin is and why it was created",
            "evening": "Bitcoin's role in digital scarcity",
        },
        2: {
            "morning": "How Bitcoin transactions work",
            "evening": "Why final settlement matters",
        },
        3: {
            "morning": "What mining does in Bitcoin",
            "evening": "How Proof of Work secures the network",
        },
        4: {
            "morning": "Why Bitcoin supply is capped",
            "evening": "Why fixed supply is part of the narrative",
        },
        5: {
            "morning": "What halvings are",
            "evening": "How halvings shape the issuance schedule",
        },
        6: {
            "morning": "Bitcoin as a network versus bitcoin as an asset",
            "evening": "Ask what people still misunderstand about Bitcoin",
        },
        7: {
            "morning": "Weekly recap of Bitcoin basics",
            "evening": "Close the week and tease Ethereum next",
        },
    },
    "Ethereum & Smart Contracts": {
        1: {
            "morning": "What Ethereum does beyond payments",
            "evening": "Why programmability changed crypto",
        },
        2: {
            "morning": "What smart contracts are",
            "evening": "How smart contracts replace manual execution",
        },
        3: {
            "morning": "What gas fees are",
            "evening": "Why network demand affects fees",
        },
        4: {
            "morning": "What the EVM is at a beginner level",
            "evening": "Why shared standards matter for developers",
        },
        5: {
            "morning": "How tokens and apps are built on Ethereum",
            "evening": "Why Ethereum became the main app layer early on",
        },
        6: {
            "morning": "Why Ethereum users care about scaling",
            "evening": "Ask which Ethereum concept people want broken down next",
        },
        7: {
            "morning": "Weekly recap of Ethereum and smart contracts",
            "evening": "Close the week and tease L1s next",
        },
    },
    "L1 Blockchains": {
        1: {
            "morning": "What a Layer 1 blockchain is",
            "evening": "Examples of major L1s and why they differ",
        },
        2: {
            "morning": "How L1s handle consensus and security",
            "evening": "Tradeoffs between speed, cost, and decentralization",
        },
        3: {
            "morning": "Native tokens on L1s",
            "evening": "Why fees and staking often use native assets",
        },
        4: {
            "morning": "Why different L1s optimize for different things",
            "evening": "Why one chain does not fit every use case",
        },
        5: {
            "morning": "What finality means on an L1",
            "evening": "Why finality matters for users and apps",
        },
        6: {
            "morning": "L1 competition versus interoperability",
            "evening": "Ask which L1 people actually use and why",
        },
        7: {
            "morning": "Weekly recap of L1 blockchains",
            "evening": "Close the week and tease L2 scaling next",
        },
    },
    "L2 Scaling": {
        1: {
            "morning": "What a Layer 2 is",
            "evening": "Why L2s exist in the first place",
        },
        2: {
            "morning": "How L2s inherit security from a base chain",
            "evening": "Why settlement on the base layer still matters",
        },
        3: {
            "morning": "What rollups do at a high level",
            "evening": "How batching reduces cost per transaction",
        },
        4: {
            "morning": "Optimistic versus zero-knowledge approaches",
            "evening": "Why different L2 models exist",
        },
        5: {
            "morning": "Bridging to and from L2s",
            "evening": "Where user friction still shows up today",
        },
        6: {
            "morning": "Why L2 adoption changes user experience",
            "evening": "Ask whether people want a deeper bridge explainer",
        },
        7: {
            "morning": "Weekly recap of L2 scaling",
            "evening": "Close the week and tease DeFi next",
        },
    },
    "DeFi": {
        1: {
            "morning": "What DeFi means",
            "evening": "Why open financial rails matter",
        },
        2: {
            "morning": "How decentralized exchanges work at a high level",
            "evening": "Why liquidity matters",
        },
        3: {
            "morning": "What lending protocols do",
            "evening": "Why collateral is central in on-chain lending",
        },
        4: {
            "morning": "How stablecoins fit inside DeFi",
            "evening": "Why stable assets became core infrastructure",
        },
        5: {
            "morning": "Smart contract risk in DeFi",
            "evening": "Why audits help but do not remove all risk",
        },
        6: {
            "morning": "What composability means in DeFi",
            "evening": "Ask which DeFi mechanism deserves its own series",
        },
        7: {
            "morning": "Weekly recap of DeFi",
            "evening": "Close the week and tease NFTs next",
        },
    },
    "NFTs & Digital Ownership": {
        1: {
            "morning": "What an NFT actually is",
            "evening": "Why NFTs are about ownership records, not just art",
        },
        2: {
            "morning": "How NFTs differ from fungible tokens",
            "evening": "Why uniqueness changes use cases",
        },
        3: {
            "morning": "What metadata does",
            "evening": "Why on-chain versus off-chain media matters",
        },
        4: {
            "morning": "NFTs in gaming, tickets, and identity",
            "evening": "Why digital ownership extends beyond collectibles",
        },
        5: {
            "morning": "Royalties and creator economics",
            "evening": "Why royalty enforcement became a real debate",
        },
        6: {
            "morning": "Common misconceptions about NFTs",
            "evening": "Ask what use case people think is actually durable",
        },
        7: {
            "morning": "Weekly recap of NFTs and digital ownership",
            "evening": "Close the week and tease ZK next",
        },
    },
    "ZK Proofs & Privacy": {
        1: {
            "morning": "What a zero-knowledge proof is at a beginner level",
            "evening": "Why proving without revealing is powerful",
        },
        2: {
            "morning": "How ZK helps scaling as well as privacy",
            "evening": "Why the same idea appears in multiple parts of crypto",
        },
        3: {
            "morning": "What validity proofs are in simple terms",
            "evening": "Why proving correctness matters",
        },
        4: {
            "morning": "Privacy versus transparency in blockchains",
            "evening": "Why this tradeoff keeps coming back",
        },
        5: {
            "morning": "Where users already touch ZK indirectly",
            "evening": "Why users do not always see the math underneath",
        },
        6: {
            "morning": "Why ZK is hard to explain but worth understanding",
            "evening": "Ask whether people want a deeper ZK breakdown",
        },
        7: {
            "morning": "Weekly recap of ZK and privacy",
            "evening": "Close the week and tease the next cycle",
        },
    },
}


@dataclass
class Progress:
    category_index: int
    day: int


def get_db_path() -> Path:
    base_dir = os.getenv("DB_DIR", "/data")
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / "content_progress.db"


def get_slot() -> str:
    if len(sys.argv) > 1:
        slot = sys.argv[1].strip().lower()
    else:
        slot = os.getenv("SLOT", "").strip().lower()

    if slot not in {"morning", "evening"}:
        raise ValueError("Usage: python main.py morning|evening or set SLOT=morning|evening")
    return slot


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def get_twitter_client() -> tweepy.Client:
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")

    missing = [
        name for name, value in {
            "TWITTER_API_KEY": api_key,
            "TWITTER_API_SECRET": api_secret,
            "TWITTER_ACCESS_TOKEN": access_token,
            "TWITTER_ACCESS_SECRET": access_secret,
        }.items() if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Twitter credentials: {', '.join(missing)}")

    return tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            category_index INTEGER NOT NULL,
            day INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            day INTEGER NOT NULL,
            slot TEXT NOT NULL,
            topic TEXT NOT NULL,
            post_type TEXT NOT NULL,
            tweet TEXT NOT NULL,
            char_count INTEGER NOT NULL,
            twitter_post_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, day, slot)
        )
    """)
    conn.execute("""
        INSERT OR IGNORE INTO progress (id, category_index, day)
        VALUES (1, 0, 1)
    """)
    conn.commit()


def load_progress(conn: sqlite3.Connection) -> Progress:
    row = conn.execute(
        "SELECT category_index, day FROM progress WHERE id = 1"
    ).fetchone()
    if row is None:
        raise RuntimeError("Progress row missing")
    return Progress(category_index=row[0], day=row[1])


def save_progress(conn: sqlite3.Connection, progress: Progress) -> None:
    conn.execute(
        "UPDATE progress SET category_index = ?, day = ? WHERE id = 1",
        (progress.category_index, progress.day),
    )
    conn.commit()


def get_current_category_and_topic(progress: Progress, slot: str) -> Tuple[str, int, str, str]:
    category = CATEGORY_ORDER[progress.category_index]
    day = progress.day
    topic = CATEGORY_TOPIC_PLAN[category][day][slot]
    post_type = POST_TYPE_SCHEDULE[day][slot]
    return category, day, topic, post_type


def maybe_get_existing_post(
    conn: sqlite3.Connection,
    category: str,
    day: int,
    slot: str,
) -> Dict | None:
    row = conn.execute("""
        SELECT tweet, char_count, post_type, topic, category, day
        FROM posts
        WHERE category = ? AND day = ? AND slot = ?
    """, (category, day, slot)).fetchone()

    if row is None:
        return None

    return {
        "tweet": row[0],
        "char_count": row[1],
        "post_type": row[2],
        "slot": slot,
        "topic": row[3],
        "category": row[4],
        "day": row[5],
    }


def build_prompt(
    slot: str,
    category: str,
    day: int,
    topic: str,
    post_type: str,
    next_category: str | None,
) -> str:
    slot_goal = (
        "Morning post teaches the mechanism: what it is, how it works, or the core concept."
        if slot == "morning"
        else "Evening post gives real-world context, a clear practical implication, or ends with a CTA."
    )

    week_close_instruction = ""
    if post_type == "week_close" and next_category:
        week_close_instruction = (
            f"Tease the next category naturally at the end. The next category is: {next_category}."
        )

    return f"""
You are writing one post for X as part of "{SERIES_NAME}".

Audience:
Smart beginners who want crypto explained clearly without hype.

Voice and tone:
- Friendly and approachable
- Sound like a knowledgeable friend
- Clear, precise, and human
- Facts only
- No hype
- No price predictions
- No unsupported claims
- Do not state uncertain statistics as facts
- If you are not highly certain about a stat, do not use one

Series rules:
- Category: {category}
- Day: {day} ({DAY_LABELS[day]})
- Slot: {slot}
- Topic: {topic}
- Post type: {post_type}
- {slot_goal}

Formatting rules:
- Output must be valid JSON only
- Tweet length must be between {TARGET_MIN} and {TARGET_MAX} characters inclusive, including hashtags
- Use 1 or 2 relevant hashtags max
- No emojis
- No markdown
- Keep it standalone and readable

Post-type guidance:
- fact_hook: start with a sharp factual hook, then explain
- explainer: teach the mechanism clearly
- context: connect the concept to real-world use, impact, or why it matters
- cta_engage: factual post that ends with a strong reply, follow, or save CTA
- week_summary: summarize the week's key lessons clearly
- week_close: wrap the week and point forward
- {week_close_instruction}

Return exactly this JSON schema:
{{
  "tweet": "...",
  "char_count": 247,
  "post_type": "{post_type}",
  "slot": "{slot}",
  "topic": "{topic}",
  "category": "{category}",
  "day": {day}
}}
"""


def generate_post(
    client: OpenAI,
    slot: str,
    category: str,
    day: int,
    topic: str,
    post_type: str,
    next_category: str | None,
) -> Dict:
    prompt = build_prompt(
        slot=slot,
        category=category,
        day=day,
        topic=topic,
        post_type=post_type,
        next_category=next_category,
    )

    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You write concise, factual, engaging X posts about crypto for beginners. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    data = json.loads(response.choices[0].message.content)
    tweet = data["tweet"].strip()
    char_count = len(tweet)

    if char_count < TARGET_MIN or char_count > TARGET_MAX:
        raise ValueError(
            f"Tweet length out of range: {char_count} chars. Expected {TARGET_MIN}-{TARGET_MAX}."
        )

    data["char_count"] = char_count
    return data


def post_to_x(tweet: str) -> str:
    client = get_twitter_client()
    response = client.create_tweet(text=tweet)
    return str(response.data["id"])


def save_post_record(
    conn: sqlite3.Connection,
    payload: Dict,
    twitter_post_id: str | None,
) -> None:
    conn.execute("""
        INSERT OR REPLACE INTO posts (
            category, day, slot, topic, post_type, tweet, char_count, twitter_post_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload["category"],
        payload["day"],
        payload["slot"],
        payload["topic"],
        payload["post_type"],
        payload["tweet"],
        payload["char_count"],
        twitter_post_id,
    ))
    conn.commit()


def advance_progress(progress: Progress) -> Progress:
    next_day = progress.day + 1
    next_category_index = progress.category_index

    if next_day > 7:
        next_day = 1
        next_category_index = (progress.category_index + 1) % len(CATEGORY_ORDER)

    return Progress(category_index=next_category_index, day=next_day)


def main() -> None:
    slot = get_slot()
    db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    init_db(conn)

    progress = load_progress(conn)
    category, day, topic, post_type = get_current_category_and_topic(progress, slot)
    next_category = CATEGORY_ORDER[(progress.category_index + 1) % len(CATEGORY_ORDER)]

    existing = maybe_get_existing_post(conn, category, day, slot)
    if existing:
        print(json.dumps(existing, ensure_ascii=False))
        return

    openai_client = get_openai_client()
    payload = generate_post(
        client=openai_client,
        slot=slot,
        category=category,
        day=day,
        topic=topic,
        post_type=post_type,
        next_category=next_category,
    )

    should_post = os.getenv("POST_TO_X", "false").lower() == "true"
    twitter_post_id = None

    if should_post:
        twitter_post_id = post_to_x(payload["tweet"])

    save_post_record(conn, payload, twitter_post_id)

    if slot == "evening":
        progress = advance_progress(progress)
        save_progress(conn, progress)

    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
