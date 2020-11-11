FROM python:3
COPY . /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /app/scrapython
CMD scrapy crawl main_spider -o output.json -L WARNING