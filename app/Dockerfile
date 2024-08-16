FROM python:3.12-bookworm
WORKDIR /app

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \ 
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update && apt-get -y install google-chrome-stable

RUN apt-get install -yqq unzip

RUN wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/127.0.6533.99/linux64/chromedriver-linux64.zip

RUN unzip /tmp/chromedriver.zip -d /tmp

RUN mv /tmp/chromedriver-linux64 /usr/bin

RUN chmod +x /usr/bin/chromedriver-linux64/chromedriver


COPY requirements.txt ./requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm



EXPOSE 8501
COPY . .


ENTRYPOINT  ["python", "-m", "streamlit", "run", "./app.py"]
CMD ["--server.address", "0.0.0.0", "--server.headless", "True", "--server.port", "8501"]