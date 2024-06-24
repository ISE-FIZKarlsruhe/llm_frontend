FROM python:3.11


RUN mkdir -p /src
ENV HOME=/src

WORKDIR $HOME

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src .

CMD ["uvicorn", "--workers", "4", "--host", "0.0.0.0", "--port", "8000", "app:app", "--log-level", "debug" ]
