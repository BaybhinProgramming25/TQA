FROM python:3.11-slim

WORKDIR /app 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt 

COPY . . 

EXPOSE 3000 

# Be sure to remove reload when pushing this into production
CMD [ "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]