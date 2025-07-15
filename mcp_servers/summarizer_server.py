# mcp_servers/summarizer_server.py
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re, os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY"), model="llama3-8b-8192")
analyzer = SentimentIntensityAnalyzer()

# Renamed to be more generic
class ContentSummary(BaseModel):
    summary_text: str
    action_items: str
    overall_sentiment: str
    sentiment_score: float

# Renamed to be more generic
def analyze_and_summarize_transcript(transcript_text: str) -> ContentSummary:
    """Summarizes a meeting or video transcript..."""
    summary_prompt = f"Summarize the key points of the following transcript...\n\n---\n{transcript_text}\n---"
    summary = llm.invoke(summary_prompt).content
    action_items = "\n".join(re.findall(r'.*?(?:(?:will|can|please|need to)\s(?:you|I|we|he|she|they|[A-Z][a-z]+)\s.*?\w+).*', transcript_text, re.IGNORECASE))
    action_items_str = f"**Action Items:**\n{action_items}" if action_items else "**Action Items:**\nNo specific action items were identified."
    sentiment = analyzer.polarity_scores(transcript_text)
    score = sentiment['compound']
    label = "Positive" if score >= 0.05 else "Negative" if score <= -0.05 else "Neutral"
    return ContentSummary(summary_text=f"**Key Points:**\n{summary}", action_items=action_items_str, overall_sentiment=label, sentiment_score=score)