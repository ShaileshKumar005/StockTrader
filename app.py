from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import pandas as pd
from textblob import TextBlob
from sklearn.linear_model import LinearRegression
import numpy as np

app = Flask(__name__)
API_KEY = 'R3C5EEUNC4WI33T4'
# News API key for sentiment analysis
NEWS_API_KEY = '8ae2ca7271e34294bf06e9cdd14117a9'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/prediction.html', methods=['GET', 'POST'])
def prediction():
    prediction_data = {}  # Create an empty dictionary to store prediction data

    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol']

        # Function to fetch two years of hourly stock price data and add it to a DataFrame
        def get_two_years_data(symbol):
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)  # 2 years of data

            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=60min&apikey={API_KEY}&outputsize=full&datatype=json&start_date={start_date.strftime('%Y-%m-%d')}&end_date={end_date.strftime('%Y-%m-%d')}"
            response = requests.get(url)
            data = response.json()
            return data

        intraday_data = get_two_years_data(stock_symbol)

        if 'Time Series (60min)' in intraday_data:
            time_series = intraday_data['Time Series (60min)']

            # Create a DataFrame with times and prices
            times = sorted(time_series.keys())  # Sort times in ascending order
            prices = [float(time_series[time]['1. open']) for time in times]
            df = pd.DataFrame({'Time': times, 'Price': prices})

            # Create a Linear Regression model and fit it to the data
            x = np.array(range(1, len(prices) + 1)).reshape(-1, 1)
            y = np.array(prices)
            model = LinearRegression()
            model.fit(x, y)

            # Predicting prices for tomorrow
            tomorrow = len(prices) + 1
            predicted_start_price = model.predict(np.array(tomorrow).reshape(1, -1))[0]

            tomorrow += 1
            predicted_end_price = model.predict(np.array(tomorrow).reshape(1, -1))[0]

            tomorrow += 1
            predicted_peak_price = model.predict(np.array(tomorrow).reshape(1, -1))[0]

            tomorrow += 1
            predicted_lowest_price = model.predict(np.array(tomorrow).reshape(1, -1))[0]

            # Update prediction data with values and times
            prediction_data['Start Price (Tomorrow)'] = predicted_start_price
            prediction_data['End Price (Tomorrow)'] = predicted_end_price
            prediction_data['Peak Price (Tomorrow)'] = predicted_peak_price
            prediction_data['Lowest Price (Tomorrow)'] = predicted_lowest_price

            # Calculate times for tomorrow based on the last recorded time in the DataFrame
            end_time = df['Time'].iloc[-1]
            end_time_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

            # Use linear regression to predict times without incrementing
            time_difference = timedelta(hours=1)  # Adjust as needed
            start_time_tomorrow = end_time_datetime
            end_time_tomorrow = end_time_datetime
            peak_time_tomorrow = end_time_datetime
            lowest_time_tomorrow = end_time_datetime

            # Convert these times to string format
            start_time_tomorrow_str = start_time_tomorrow.strftime("%Y-%m-%d %H:%M:%S")
            end_time_tomorrow_str = end_time_tomorrow.strftime("%Y-%m-%d %H:%M:%S")
            peak_time_tomorrow_str = peak_time_tomorrow.strftime("%Y-%m-%d %H:%M:%S")
            lowest_time_tomorrow_str = lowest_time_tomorrow.strftime("%Y-%m-%d %H:%M:%S")

            # Update prediction data with time values
            prediction_data['Start Time (Tomorrow)'] = start_time_tomorrow_str
            prediction_data['End Time (Tomorrow)'] = end_time_tomorrow_str
            prediction_data['Peak Time (Tomorrow)'] = peak_time_tomorrow_str
            prediction_data['Lowest Time (Tomorrow)'] = lowest_time_tomorrow_str

        else:
            return "Error: Unable to fetch hourly data."

        # Sentiment analysis of news articles for tomorrow's date
        def fetch_and_analyze_news():
            tomorrow_date = datetime.now() + timedelta(days=1)
            tomorrow_date_str = tomorrow_date.strftime("%Y-%m-%d")

            news_url = f'https://newsapi.org/v2/everything?q={stock_symbol}&from={tomorrow_date_str}&to={tomorrow_date_str}&apiKey={NEWS_API_KEY}'
            response = requests.get(news_url)
            news_data = response.json()

            articles = news_data.get('articles', [])
            total_sentiment_score = 0
            num_articles = len(articles)

            for article in articles:
                title = article['title']
                description = article['description']
                content = f"{title}. {description}"

                analysis = TextBlob(content)
                sentiment_score = analysis.sentiment.polarity

                total_sentiment_score += sentiment_score

            if num_articles > 0:
                average_score = total_sentiment_score / num_articles
            else:
                average_score = 0

            if average_score > 0:
                sentiment_label = "Positive"
            elif average_score < 0:
                sentiment_label = "Negative"
            else:
                sentiment_label = "Neutral"

            prediction_data['Sentiment Label (Tomorrow)'] = sentiment_label

        fetch_and_analyze_news()

    return render_template('prediction.html', prediction_data=prediction_data)

NEWS_API_KEY = '8ae2ca7271e34294bf06e9cdd14117a9'

@app.route('/news', methods=['GET', 'POST'])
def news():
    # Initialize variables for three news articles
    title=[]
    description=[]
    url=[]
    image_url=[]
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol']
        print(stock_symbol)
        today_date = datetime.now()
        today_date_str = today_date.strftime("%Y-%m-%d")
        news_url = f'https://newsapi.org/v2/top-headlines?q={stock_symbol}&apiKey={NEWS_API_KEY}'
        response = requests.get(news_url)
        news_data = response.json()

        articles = news_data.get('articles', [])
        print(articles)
        for i, article in enumerate(articles[:3], start=1):
            title.append(article['title'])
            description.append(article['description'])
            url.append(article['url'])
            image_url.append(article['urlToImage'])

    return render_template('news.html', title=title, description=description, url=url, image_url=image_url, total=len(title))
                

if __name__ == '__main__':
    app.run(debug=True)
