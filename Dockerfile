FROM python:3.13.5-slim as python-base

ARG SERVICE_ENV=deploy

RUN apt-get update --fix-missing && apt-get upgrade -qy

RUN apt-get install -y --no-install-recommends build-essential gcc libpq-dev libcurl4-openssl-dev libssl-dev git
ENV LANGUAGE en_US

COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false
RUN if [ "$SERVICE_ENV" = "deploy" ]; then \
        poetry install --only main --no-interaction --no-ansi; \
    else \
        poetry install --no-interaction --no-ansi; \
    fi

FROM python-base as service

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get install -y --no-install-recommends curl libpq-dev postgresql-client && apt-get clean autoclean && apt-get autoremove --yes \
   && rm -rf /var/lib/{apt,dpkg,cache,log}/

RUN addgroup --gid 1001 appuser && adduser --uid 1001 --gid 1001 --shell /bin/bash --disabled-password appuser

ENV PYTHONPATH=/home/appuser/python
ENV PATH="${PYTHONPATH}/bin:${PATH}"

RUN mkdir /home/appuser/app && chown -R appuser:appuser /home/appuser/app && chmod 755 /home/appuser/app

COPY . /home/appuser/app
WORKDIR /home/appuser/app

RUN chmod +x docker/runserver.sh docker/wait-for-command.sh docker/docker-entrypoint.sh
USER appuser

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "/home/appuser/app/docker/docker-entrypoint.sh"]
CMD ["/bin/bash", "/home/appuser/app/docker/runserver.sh"]
