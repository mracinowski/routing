FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN python -m venv venv
RUN /bin/bash -c "source venv/bin/activate"
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
