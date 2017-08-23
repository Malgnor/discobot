FROM gcr.io/google-appengine/python
LABEL python_version=python3.5

RUN wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-64bit-static.tar.xz && \
tar xvf ffmpeg-git-*.tar.xz && \
cd ./ffmpeg-git-* && \
cp ff* qt-faststart /usr/local/bin/

RUN apt-get update && \
apt-get install -y libopus0 opus-tools

RUN virtualenv --no-download /env -p python3.5

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD . /app/
CMD exec python -m disco.cli
