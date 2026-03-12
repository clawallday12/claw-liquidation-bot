FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy liquidation bot
COPY web3/liquidation-bot.py .
COPY config/ ./config/
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Run liquidation bot
CMD ["python", "liquidation-bot.py"]
