
FROM python:3.11-slim

WORKDIR /app

COPY spam_complaint_bot.py .
COPY pdf_utils.py .
COPY mailto_link.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV BOT_TOKEN=your_token_here

CMD ["python", "spam_complaint_bot.py"]
