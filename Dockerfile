FROM python:3.8.13-slim-buster

# python
ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # poetry
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named '.venv'
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry
# https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential \
    curl \
    && curl -sSL https://install.python-poetry.org | python3 -\
    && apt-get purge --auto-remove -y

WORKDIR /app
COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock
RUN poetry install --only main
ENV PATH="/app/.venv/bin:$PATH"

COPY ./src/ /app/

CMD ["python", "bot.py"]