from flask import Flask, render_template, request
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import io
import base64
import re
from collections import Counter
from textblob import TextBlob

app = Flask(__name__)

# Custom dictionaries for word categorization
positive_words = set(['good', 'great', 'excellent', 'positive', 'fortunate', 'correct', 'superior'])
negative_words = set(['bad', 'poor', 'wrong', 'negative', 'unfortunate', 'inferior'])
neutral_words = set(['average', 'normal', 'standard', 'mediocre', 'neutral'])
sexual_words = set(['sex', 'sexual', 'nude', 'porn', 'erotic'])


def categorize_words(text):
    words = re.findall(r'\b\w+\b', text.lower())
    categories = {'positive': 0, 'negative': 0, 'neutral': 0, 'sexual': 0}

    for word in words:
        if word in positive_words:
            categories['positive'] += 1
        elif word in negative_words:
            categories['negative'] += 1
        elif word in neutral_words:
            categories['neutral'] += 1
        elif word in sexual_words:
            categories['sexual'] += 1

    return categories


def generate_word_cloud(text):
    word_counts = Counter(re.findall(r'\b\w+\b', text.lower()))
    most_common_words = word_counts.most_common(10)

    words, counts = zip(*most_common_words)
    plt.figure(figsize=(10, 6))
    plt.bar(words, counts)
    plt.title('Top 10 Words')
    plt.xlabel('Words')
    plt.ylabel('Counts')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return plot_url


def generate_category_plot(categories):
    labels = list(categories.keys())
    values = list(categories.values())

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)
    plt.title('Word Categories')
    plt.xlabel('Category')
    plt.ylabel('Count')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return plot_url


async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                return await response.text()
        except Exception as e:
            return str(e)


@app.route('/', methods=['GET', 'POST'])
async def index():
    title = None
    headings = None
    paragraphs = None
    links = None
    message = None
    paragraph_analysis = None
    title_analysis = None
    headings_analysis = None
    category_plot = None

    if request.method == 'POST':
        url = request.form['url']
        info_type = request.form.getlist('info_type')

        if not url:
            message = 'Please enter a valid URL.'
        elif not info_type:
            message = 'Please select at least one type of information to fetch.'
        else:
            html = await fetch_html(url)
            if "ClientConnectorError" in html:
                message = 'Error fetching data from URL. Please check the URL and try again.'
            else:
                soup = BeautifulSoup(html, 'html.parser')

                all_text = ""

                if 'title' in info_type:
                    title = soup.title.string if soup.title else 'No title found'
                    all_text += title + " "
                    if title:
                        title_analysis = generate_word_cloud(title)

                if 'headings' in info_type:
                    headings = [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
                    all_text += " ".join(headings) + " "
                    if headings:
                        headings_text = ' '.join(headings)
                        headings_analysis = generate_word_cloud(headings_text)

                if 'paragraphs' in info_type:
                    paragraphs = [p.get_text() for p in soup.find_all('p')]
                    all_text += " ".join(paragraphs) + " "
                    if paragraphs:
                        paragraphs_text = ' '.join(paragraphs)
                        paragraph_analysis = generate_word_cloud(paragraphs_text)

                if 'links' in info_type:
                    links = [a['href'] for a in soup.find_all('a', href=True)]

                if all_text:
                    categories = categorize_words(all_text)
                    category_plot = generate_category_plot(categories)

    return render_template('index.html', title=title, headings=headings, paragraphs=paragraphs, links=links,
                           message=message, paragraph_analysis=paragraph_analysis, title_analysis=title_analysis,
                           headings_analysis=headings_analysis, category_plot=category_plot)


if __name__ == '__main__':
    app.run(debug=True)
