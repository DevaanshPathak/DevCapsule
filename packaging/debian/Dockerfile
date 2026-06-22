FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY . /work

ENV DEVCAPSULE_DIST_DIR=/out

CMD ["bash", "packaging/debian/build-deb.sh"]
