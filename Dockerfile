FROM python:3.11-slim

ARG USER=fauxmo
ARG HOME=/home/${USER}
ARG VENV=${HOME}/.venv
ARG PYTHON=${VENV}/bin/python3
ARG UID=${FAUXMO_UID:-10000}
ARG GID=${FAUXMO_GID:-10000}

RUN apt-get update \
    && apt-get install -y python3-uvloop \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid "${GID}" "${USER}" \
    && useradd \
        --shell /usr/sbin/nologin \
        --uid "${UID}" \
        --gid "${USER}" \
        "${USER}"

COPY --chown=${USER} pyproject.toml README.md CHANGELOG.md /app/
COPY --chown=${USER} src/ /app/src
COPY --chown=${USER} tests/ /app/tests
COPY --chown=${USER} config-sample.json /home/${USER}/.fauxmo/config-sample.json

USER ${USER}
WORKDIR ${HOME}

RUN python3 -m venv --system-site-packages "${VENV}" \
    && "${PYTHON}" -m pip install --upgrade pip \
    && "${PYTHON}" -m pip install /app[test]

ENV FAUXMO_PYTHON ${PYTHON}
CMD ${FAUXMO_PYTHON} -m fauxmo.cli -vvv
