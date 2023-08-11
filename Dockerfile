#
# avviare con:
# docker build -t check-power .
# docker run -d --restart=always --name check-power-app-2 -e HA_MEDIA_PLAYER_ID="media_player.mopidy" -e HA_TTS_SERVICE_TOPIC="ha/tts/picotts_say" check-power
#
#
FROM alpine:3.16

# Uninstall pre-installed formatting and linting tools
# They would conflict with our pinned versions
RUN apk add --no-cache python3-dev
RUN apk add --no-cache gcc
RUN apk add --no-cache make py3-pip bash cmake g++ gfortran musl-dev linux-headers sed

COPY ta-lib-0.4.0-src.tar.gz ./
RUN tar -xzvf ta-lib-0.4.0-src.tar.gz
WORKDIR /ta-lib
RUN wget -O config.sub http://cvs.savannah.gnu.org/viewvc/*checkout*/config/config/config.sub
RUN wget -O config.guess http://cvs.savannah.gnu.org/viewvc/*checkout*/config/config/config.guess
RUN ./configure --prefix=/usr && make && make install
RUN cd .. && rm ta-lib-0.4.0-src.tar.gz

RUN mkdir /app
ADD app.py /app
ADD check-power.py /app
WORKDIR /app

# Install Python dependencies from requirements
COPY requirements.txt ./
RUN pip3 install -U pip
RUN pip3 install -r requirements.txt --use-deprecated=legacy-resolver
RUN rm -rf requirements.txt

RUN apk del gcc make py3-pip bash cmake g++ gfortran musl-dev linux-headers sed
# test app docker banner
# CMD ["python3", "app.py"]
# production app
ENV HA_MEDIA_PLAYER_ID="media_player.mopidy"
ENV HA_TTS_SERVICE_TOPIC="ha/tts/picotts_say"
CMD "python3" "check-power.py" "--HA_MEDIA_PLAYER_ID" ${HA_MEDIA_PLAYER_ID} "--HA_TTS_SERVICE_TOPIC" ${HA_TTS_SERVICE_TOPIC}