FROM python:3.10-slim

ARG USER=fauxmo
ARG HOME=/home/${USER}
ARG VENV=${HOME}/.venv
ARG PYTHON=${VENV}/bin/python3
ARG UID=10000
ARG GID=10000

RUN apt-get update \
    && apt-get install -y python3-uvloop \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid "${GID}" "${USER}" \
    && adduser \
        --shell /usr/sbin/nologin \
        --uid "${UID}" \
        --ingroup "${USER}" \
        --disabled-password \
        "${USER}"

COPY --chown=${USER} pyproject.toml setup.cfg README.md CHANGELOG.md /app/
COPY --chown=${USER} src/ /app/src
COPY --chown=${USER} tests/ /app/tests
COPY --chown=${USER} config-sample.json /home/${USER}/.fauxmo/config-sample.json

USER ${USER}
WORKDIR ${HOME}

RUN python3 -m venv --system-site-packages "${VENV}" \
    && "${PYTHON}" -m pip install --upgrade pip \
    && "${PYTHON}" -m pip install /app[test] \
    && cd /app; "${PYTHON}" -m pytest /app/tests

ENV FAUXMO_PYTHON ${PYTHON}
CMD ${FAUXMO_PYTHON} -m fauxmo.cli -vvv
