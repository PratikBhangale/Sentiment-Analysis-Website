# Sentiment Analysis Web Application

A web application that analyzes the sentiment of text, tweets, or news articles.

## Features

- Analyze sentiment of plain text
- Analyze sentiment of tweets (via URL)
- Analyze sentiment of news articles (via URL)
- View sentiment polarity and subjectivity scores
- See excerpts from the analyzed content

## Deployment Instructions

### Deploying to Render (Free Tier)

1. Create a free account on [Render](https://render.com/) if you don't have one already.

2. Click on the "New +" button and select "Web Service".

3. Connect your GitHub repository or use the "Public Git repository" option with your repository URL.

4. Configure the following settings:
   - **Name**: Choose a name for your service (e.g., sentiment-analysis-app)
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt && python nltk_setup.py`
   - **Start Command**: `python app.py`

5. Click "Create Web Service".

6. Your application will be deployed and available at the URL provided by Render (typically https://your-service-name.onrender.com).

### Deploying to Railway (Free Tier)

1. Create a free account on [Railway](https://railway.app/) if you don't have one already.

2. Create a new project and select "Deploy from GitHub repo".

3. Connect your GitHub repository.

4. Add the following environment variables if needed:
   - `PORT`: 5000
   - `FLASK_ENV`: production

5. Deploy your application.

6. Your application will be available at the URL provided by Railway.

### Deploying to PythonAnywhere (Free Tier)

1. Create a free account on [PythonAnywhere](https://www.pythonanywhere.com/) if you don't have one already.

2. Go to the "Web" tab and click "Add a new web app".

3. Choose "Flask" as your web framework and the appropriate Python version.

4. Set the source code directory to your project directory.

5. Update the WSGI configuration file to point to your Flask application.

6. Install the required packages using the PythonAnywhere console:
   ```
   pip install -r requirements.txt
   python nltk_setup.py
   ```

7. Reload your web app.

8. Your application will be available at yourusername.pythonanywhere.com.

## Local Development

1. Clone the repository.

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the NLTK setup script:
   ```
   python nltk_setup.py
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and navigate to http://localhost:5000.
