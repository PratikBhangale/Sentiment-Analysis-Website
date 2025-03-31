import os
import logging
from flask import Flask, request, render_template, redirect, url_for, jsonify, flash
from sentiment_scripts.sentiment_analyzer import analyze_sentiment, is_url

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_sentiment_analysis')

@app.route("/", methods=["GET"])
def home():
    """Render the home page with the input form."""
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Process the form submission and analyze sentiment based on input type.
    
    The form can submit:
    - Text input directly
    - URL to a tweet
    - URL to a news article
    """
    try:
        # Get form data
        input_type = request.form.get("input_type", "text")
        
        if input_type == "text":
            # For text input
            text = request.form.get("topic", "").strip()
            if not text:
                logger.warning("Empty text input received")
                return render_template("results.html", results={"status": "error", "excerpts": ["No text provided for analysis."]})
            
            logger.info(f"Analyzing text input: {text[:50]}...")
            analysis_results = analyze_sentiment(text, input_type="text")
            
        else:
            # For tweet or news URL
            url = request.form.get("url", "").strip()
            
            if not url:
                logger.warning(f"Empty URL for {input_type} analysis")
                return render_template("results.html", results={"status": "error", "excerpts": [f"No URL provided for {input_type} analysis."]})
            
            if not is_url(url):
                logger.warning(f"Invalid URL format: {url}")
                return render_template("results.html", results={"status": "error", "excerpts": ["Please enter a valid URL."]})
            
            logger.info(f"Analyzing {input_type} from URL: {url}")
            analysis_results = analyze_sentiment(url, input_type=input_type, url=url)
        
        return render_template("results.html", results=analysis_results)
    
    except Exception as e:
        logger.error(f"Error in analyze route: {e}")
        return render_template("results.html", results={
            "status": "error",
            "excerpts": [f"An error occurred during analysis: {str(e)}"]
        })

@app.route("/results", methods=["GET"])
def results():
    """
    A direct route for viewing results. In this implementation, results are generated from
    the /analyze endpoint. This route could be used for charting or additional queries later.
    """
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template("results.html", results={
        "status": "error",
        "excerpts": ["Page not found. Please return to the home page."]
    }), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {e}")
    return render_template("results.html", results={
        "status": "error",
        "excerpts": ["A server error occurred. Please try again later."]
    }), 500

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Debug mode is ideal in development, but should be set to False in production
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
