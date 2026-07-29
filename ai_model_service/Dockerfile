FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from transformers import MobileBertForSequenceClassification, MobileBertTokenizer; MobileBertTokenizer.from_pretrained('google/mobilebert-uncased'); MobileBertForSequenceClassification.from_pretrained('cssupport/mobilebert-sql-injection-detect')"
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
