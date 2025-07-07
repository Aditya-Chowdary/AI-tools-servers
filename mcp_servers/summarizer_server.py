# mcp_servers/summarizer_server.py (Upgraded)
from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

mcp = FastMCP("MeetingSummarizerServer")

@dataclass
class AnalyzedSummary:
    summary_text: str
    overall_sentiment: str
    sentiment_score: float

analyzer = SentimentIntensityAnalyzer()

@mcp.tool()
def analyze_and_summarize_transcript(transcript_text: str) -> AnalyzedSummary:
    """Summarizes a meeting transcript and analyzes its overall sentiment."""
    
    # 1. Summarization (dummy logic)
    key_points = "1. Discussed Q3 financial results.\n2. Agreed on new marketing strategy."
    action_items = "- [ ] Alex to finalize budget.\n- [ ] Sarah to draft client email."
    summary = f"**Key Points:**\n{key_points}\n\n**Action Items:**\n{action_items}"
    
    # 2. Sentiment Analysis
    sentiment = analyzer.polarity_scores(transcript_text)
    compound_score = sentiment['compound']
    
    # 3. Categorize sentiment
    if compound_score >= 0.05:
        sentiment_label = "Positive"
    elif compound_score <= -0.05:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"
        
    return AnalyzedSummary(
        summary_text=summary,
        overall_sentiment=sentiment_label,
        sentiment_score=compound_score
    )