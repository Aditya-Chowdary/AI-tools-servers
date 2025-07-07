# mcp_servers/news_analyzer_server.py (NEW FILE)
from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass
from typing import List, Optional
import requests
import os

mcp = FastMCP("CompanyNewsServer")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

@dataclass
class Article:
    title: str
    source: str
    url: str

@dataclass
class NewsReport:
    company: str
    article_count: int
    top_articles: List[Article]

@mcp.tool()
def get_company_news(company_name: str) -> Optional[NewsReport]:
    """Fetches the top 3 recent news articles about a specified public company."""
    if not NEWS_API_KEY:
        print("ERROR: NEWS_API_KEY not set in environment.")
        return None
    
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': company_name,
        'sortBy': 'relevancy',
        'pageSize': 3,
        'apiKey': NEWS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # Raises an exception for bad status codes
        data = response.json()
        
        articles = [
            Article(
                title=article['title'],
                source=article['source']['name'],
                url=article['url']
            ) for article in data['articles']
        ]
        
        return NewsReport(
            company=company_name,
            article_count=len(articles),
            top_articles=articles
        )
    except requests.RequestException as e:
        print(f"ERROR: Could not fetch news for {company_name}. Error: {e}")
        return None