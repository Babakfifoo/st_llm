FROM ghcr.io/osgeo/gdal:ubuntu-small-latest

RUN apt-get update && \
    apt-get install -y python3-pip python3-venv software-properties-common && \
    add-apt-repository ppa:git-core/ppa && \
    apt-get -y install git

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY requirements.txt .
RUN python3 -m venv .venv && \
    ./.venv/bin/pip install --upgrade pip && \
    ./.venv/bin/pip install -r requirements.txt && \
    ./.venv/bin/pip install ipykernel

ENV PATH="/.venv/bin:$PATH"

EXPOSE 8888
CMD ["bash", "-c", ". .venv/bin/activate && jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root"]
