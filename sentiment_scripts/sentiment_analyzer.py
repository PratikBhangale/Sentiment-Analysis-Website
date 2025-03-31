import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import re
import nltk
from nltk.tokenize import sent_tokenize
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Download NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def is_url(text):
    """Check if the given text is a URL."""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(text))

def clean_text(text):
    """Clean the text by removing extra whitespace, newlines, etc."""
    # Remove HTML tags
    text = re.sub(r'<.*?>', ' ', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', ' ', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_sentences(text, max_sentences=10):
    """Extract a limited number of sentences from the text."""
    try:
        sentences = sent_tokenize(text)
        return sentences[:max_sentences]
    except Exception as e:
        logger.error(f"Error extracting sentences: {e}")
        # If sentence tokenization fails, return a chunk of text
        return [text[:500]] if text else []

def scrape_tweet(url):
    """
    Scrape tweet content from a Twitter URL.
    This is a simplified implementation that works with public tweets.
    
    Note: Twitter (X) has strong anti-scraping measures. This function
    provides a fallback mechanism when direct scraping fails.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Check if we got the "JavaScript is disabled" page
        if "We've detected that JavaScript is disabled" in response.text:
            logger.warning("Twitter returned the 'JavaScript is disabled' page")
            
            # Extract tweet ID from URL
            tweet_id = None
            match = re.search(r'twitter\.com/\w+/status/(\d+)', url) or re.search(r'x\.com/\w+/status/(\d+)', url)
            if match:
                tweet_id = match.group(1)
            
            if tweet_id:
                # Use the tweet ID in our response
                return f"Tweet ID: {tweet_id}. Unable to retrieve content due to Twitter's anti-scraping measures. For accurate analysis, please copy and paste the tweet text directly.", url
            else:
                return "Unable to retrieve tweet content due to Twitter's anti-scraping measures. For accurate analysis, please copy and paste the tweet text directly.", url
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find tweet content
        tweet_text = ""
        
        # Look for common tweet content containers
        tweet_containers = soup.select('div[data-testid="tweetText"]') or \
                          soup.select('p.tweet-text') or \
                          soup.select('div.js-tweet-text-container p')
        
        if tweet_containers:
            for container in tweet_containers:
                tweet_text += container.get_text() + " "
        else:
            # Fallback: try to extract any text that might be the tweet
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                p_text = p.get_text().strip()
                # Skip very short paragraphs and known Twitter UI text
                if (len(p_text) > 20 and len(p_text) < 280 and 
                    "JavaScript is disabled" not in p_text and
                    "Terms of Service" not in p_text and
                    "Privacy Policy" not in p_text):
                    tweet_text += p_text + " "
        
        # Clean up the text
        tweet_text = clean_text(tweet_text)
        
        # If we couldn't find meaningful content
        if not tweet_text or len(tweet_text) < 20 or "JavaScript is disabled" in tweet_text:
            return "Unable to retrieve tweet content due to Twitter's anti-scraping measures. For accurate analysis, please copy and paste the tweet text directly.", url
        
        return tweet_text, url
    
    except Exception as e:
        logger.error(f"Error scraping tweet: {e}")
        return f"Could not retrieve tweet content. Error: {str(e)}", url

def scrape_news_article(url):
    """
    Scrape content from a news article URL.
    This is a simplified implementation that works with many news sites.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()
        
        # Try to find article content
        article_text = ""
        
        # Look for article content in common containers
        article = soup.find('article') or \
                 soup.find('div', class_=re.compile(r'article|content|story')) or \
                 soup.find('div', id=re.compile(r'article|content|story'))
        
        if article:
            # Get all paragraphs within the article
            paragraphs = article.find_all('p')
            for p in paragraphs:
                article_text += p.get_text() + " "
        else:
            # Fallback: get all paragraphs
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                # Skip very short paragraphs which are likely not part of the main content
                if len(p.get_text()) > 20:
                    article_text += p.get_text() + " "
        
        # If we still don't have much text, try getting all text
        if len(article_text) < 100:
            article_text = soup.get_text()
        
        return clean_text(article_text), url
    
    except Exception as e:
        logger.error(f"Error scraping news article: {e}")
        return f"Could not retrieve article content. Error: {str(e)}", url

def analyze_sentiment(input_text, input_type="text", url=None):
    """
    Analyze sentiment of text, tweet, or news article.
    
    Args:
        input_text: The text to analyze or URL if input_type is 'tweet' or 'news'
        input_type: 'text', 'tweet', or 'news'
        url: Optional URL for the source
    
    Returns:
        A dictionary of results
    """
    try:
        text_to_analyze = input_text
        source_url = url
        source_type = input_type.capitalize()
        
        # Handle different input types
        if input_type == "tweet" and is_url(input_text):
            text_to_analyze, source_url = scrape_tweet(input_text)
            source_type = "Tweet"
        elif input_type == "news" and is_url(input_text):
            text_to_analyze, source_url = scrape_news_article(input_text)
            source_type = "News Article"
        
        # Perform sentiment analysis
        blob = TextBlob(text_to_analyze)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine overall sentiment
        if polarity > 0.05:
            overall_sentiment = "positive"
        elif polarity < -0.05:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        # Extract sentences for excerpts
        sentences = extract_sentences(text_to_analyze)
        
        # Create chart data
        chart_data = {
            "positive": max(0, polarity) * 100 if polarity > 0 else 0,
            "neutral": (1 - abs(polarity)) * 100 if abs(polarity) < 0.1 else 10,
            "negative": abs(min(0, polarity)) * 100 if polarity < 0 else 0
        }
        
        # Ensure chart data adds up to 100%
        total = sum(chart_data.values())
        if total > 0:
            for key in chart_data:
                chart_data[key] = round((chart_data[key] / total) * 100)
        
        return {
            "status": "success",
            "overall_sentiment": overall_sentiment,
            "polarity": polarity,
            "subjectivity": subjectivity,
            "excerpts": sentences,
            "source_type": source_type,
            "source_url": source_url,
            "chart_data": chart_data
        }
    
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return {
            "status": "error",
            "overall_sentiment": "neutral",
            "polarity": 0,
            "subjectivity": 0,
            "excerpts": [f"Error analyzing content: {str(e)}"],
            "source_type": input_type.capitalize(),
            "source_url": url
        }
