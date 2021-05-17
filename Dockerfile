# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements / layers that should be static enough
WORKDIR /app
ADD requirements.txt .
ADD teslamte_telegram_bot.py /app/
RUN ln -sf /usr/share/zoneinfo/Europe/Paris /etc/timezone && \
    ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime

# install the OS build deps & timezone (all in one pretty dynamic layer)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python-dev \
    openssl \
 && apt-get clean \
 && apt-get autoremove --yes \
 && rm -rf /var/lib/apt/lists/*

# Split Python layer from APT-GET layer
RUN python -m pip install -r requirements.txt

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app
USER appuser

# Entrypoint
CMD ["python", "./teslamte_telegram_bot.py"]
