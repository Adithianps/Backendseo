from flask import Flask, render_template, request
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Previous code for SEO analysis functions
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
import json
import openai

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_sentence(analysis_results):
    prompt = f"SEO analysis for {analysis_results['title']} with keyword '{analysis_results['keyword']}'. "
    prompt += f"The website has a SEO score of {analysis_results['seo_score']}."

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
    )

    return response.choices[0].text.strip()

def calculate_keyword_density(content, keyword):
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    word_count = len(content.lower().split())
    keyword_count = content.lower().count(keyword.lower())
    density = (keyword_count / word_count) * 100
    return density

def seo_analysis(url, keyword):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Unable to fetch {url}. Status code: {response.status_code}")
        return

    content = response.content
    soup = BeautifulSoup(content, "lxml")

    status_code = response.status_code
    title_tag = soup.title
    title = title_tag.string if title_tag else None
    meta_description = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_description['content'] if meta_description else None
    robots_meta = soup.find("meta", attrs={"name": "robots"})
    robots_content = robots_meta['content'] if robots_meta else None
    content_size = len(content)
    response_time = response.elapsed.total_seconds()

    headings = {f"h{i}": len(soup.findAll(f"h{i}")) for i in range(1, 7)}
    keyword_density = calculate_keyword_density(content, keyword)

    internal_links = []
    external_links = []
    for link in soup.findAll("a"):
        href = link.get("href")
        if href:
            absolute_url = urljoin(url, href)
            if urlparse(absolute_url).netloc == urlparse(url).netloc:
                internal_links.append(absolute_url)
            else:
                external_links.append(absolute_url)

    viewport_tag = soup.find("meta", attrs={"name": "viewport"})
    mobile_friendly = True if viewport_tag else False

    structured_data = []
    for script_tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script_tag.string)
            structured_data.append(data)
        except json.JSONDecodeError:
            pass

    seo_score = 100
    if not title or len(title) < 10:
        seo_score -= 10

    if not meta_description:
        seo_score -= 10

    if robots_content and "noindex" in robots_content:
        seo_score -= 20

    if content_size > 50000:
        seo_score -= 10

    if response_time > 5.0:
        seo_score -= 20

    results = {
        "status_code": status_code,
        "title": title,
        "meta_description": meta_description,
        "robots_content": robots_content,
        "content_size": content_size,
        "response_time": response_time,
        "headings": headings,
        "keyword": keyword,
        "keyword_density": keyword_density,
        "internal_links": internal_links,
        "external_links": external_links,
        "mobile_friendly": mobile_friendly,
        "structured_data": structured_data,
        "seo_score": max(seo_score, 0),
    }

    results["chatgpt_sentence"] = generate_sentence(results)

    return results

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form['url']
    keyword = request.form['keyword']

    if not url or not keyword:
        return render_template('index.html', error='Both URL and keyword are required.')

    try:
        analysis_results = seo_analysis(url, keyword)
        return render_template('results.html', results=analysis_results)
    except Exception as e:
        return render_template('index.html', error=f"Error analyzing the website: {str(e)}")

if __name__ == '__main__':
    app.run(debug=False)
  
