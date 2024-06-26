FROM docker.io/nvidia/cuda:12.5.0-devel-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    git \
    gcc \
    && apt-get clean
RUN mkdir -p /src
ENV HOME=/src

WORKDIR $HOME

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src .

CMD ["uvicorn", "--workers", "4", "--host", "0.0.0.0", "--port", "8000", "app:app", "--log-level", "debug" ]
