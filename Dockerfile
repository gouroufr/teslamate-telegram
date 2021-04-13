# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements
WORKDIR /app
ADD requirements.txt .
ADD teslamte_telegram_bot.py /app/

# install the OS build deps & timezone (all in one layer)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python-dev \
    openssl \
 && rm -rf /var/lib/apt/lists/* \
 && ln -sf /usr/share/zoneinfo/Europe/Paris /etc/timezone && \
ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime && \
python -m pip install -r requirements.txt
# TODO : make timezone dynamic


# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app
USER appuser

# Entrypoint
CMD ["python", "./teslamte_telegram_bot.py"]
