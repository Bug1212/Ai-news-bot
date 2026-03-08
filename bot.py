from dotenv import load_dotenv
load_dotenv()
import feedparser
from telegram import Bot
import asyncio
import os
import json
from groq import Groq

# ============================================================
# CONFIG — replace these or set as environment variables
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID        = os.environ.get("CHAT_ID", "@aipulsedailyontime")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")

RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/"
]

POSTED_FILE = "posted_links.json"

# ============================================================
# HELPERS
# ============================================================
def get_posted_links():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return json.load(f)
    return []

def save_posted_links(links):
    with open(POSTED_FILE, "w") as f:
        json.dump(links, f)

def summarize_with_groq(description: str) -> str:
    """Call Groq API (free) to summarize the article."""
    client = Groq(api_key=GROQ_API_KEY)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional AI news summarizer. "
                    "Always respond in exactly 4 short, engaging, professional lines. "
                    "No bullet points. No markdown symbols like * or _."
                )
            },
            {
                "role": "user",
                "content": f"Summarize this AI news in 4 short lines:\n\n{description}"
            }
        ],
        model="llama3-8b-8192",   # Free model on Groq — fast & accurate
        temperature=0.7,
        max_tokens=200,
    )

    return chat_completion.choices[0].message.content.strip()

# ============================================================
# MAIN BOT LOGIC
# ============================================================
async def send_ai_news():
    bot = Bot(token=TELEGRAM_TOKEN)
    print("📡 Fetching AI news from multiple sources...")

    posted_links = get_posted_links()
    new_articles = []

    # Collect newest unseen articles (1 per source)
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                if entry.link not in posted_links:
                    new_articles.append(entry)
                    break
        except Exception as e:
            print(f"⚠️ Error fetching {feed_url}: {e}")

    if not new_articles:
        print("🟡 No new articles found.")
        return

    # Send max 2 posts per run to avoid spam
    for article in new_articles[:2]:
        title       = article.title
        link        = article.link
        description = getattr(article, "summary", title)  # fallback to title

        print(f"🤖 Generating summary for: {title}")

        try:
            ai_summary = summarize_with_groq(description)
        except Exception as e:
            print(f"⚠️ Groq API error: {e}")
            ai_summary = "Summary unavailable at this time."

        # Clean any leftover markdown symbols
        title      = title.replace("*", "").replace("_", "").replace("`", "")
        ai_summary = ai_summary.replace("*", "").replace("_", "").replace("`", "")

        message = (
            "🚀 *AI News Update*\n\n"
            f"📌 *{title}*\n\n"
            "🧠 *AI Summary:*\n"
            f"{ai_summary}\n\n"
            f"🔗 [Read Full Article]({link})\n\n"
            "✨ _Stay updated with the latest AI innovations\\._"
        )

        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )
            posted_links.append(link)
            print(f"✅ Posted: {title}")
        except Exception as e:
            print(f"⚠️ Telegram send error: {e}")

    # Keep memory small (last 50 links only)
    posted_links = posted_links[-50:]
    save_posted_links(posted_links)
    print("✅ Done! News sent successfully.")

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    asyncio.run(send_ai_news())
