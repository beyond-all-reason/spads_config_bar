# syntax=docker/dockerfile:1
FROM ubuntu:rolling

RUN apt-get update \
 && apt-get upgrade -y \
 && DEBIAN_FRONTEND=noninteractive \
   apt-get install --no-install-recommends -y \
   curl \
   perl \
   swig \
   g++ \
   ca-certificates \
   libcurl4 \
   libsdl2-2.0-0 \
   net-tools \
   python \
   python3-pycurl \
   p7zip-full \
   jq \
   openssh-client \
   sshpass \
   libio-socket-ssl-perl \
   libdbi-perl \
   libdbd-sqlite3-perl \
   cpanminus build-essential git python3-dev python3-distutils \
   vim \
   less \
 && apt-get autoremove \
 && rm -rf /var/run/apt \
 && useradd -m spads

RUN cpanm https://github.com/niner/inline-python-pm.git

RUN mkdir -p /opt/spads /spring-data /spring-engines

COPY docker/spadsInstaller.auto /opt/spads
COPY docker/update-engine.sh /opt/
COPY docker/update-games.sh /opt/
COPY docker/scripts/*.sh /opt/
COPY upload_replay.sh /opt/

RUN chown -R spads:spads /opt /spring-data /spring-engines

USER spads

RUN /opt/update-engine.sh

WORKDIR /opt/spads/

RUN curl -SLO http://planetspads.free.fr/spads/installer/spadsInstaller.tar \
 && tar -xf spadsInstaller.tar \
 && rm spadsInstaller.tar \
 && perl /opt/spads/spadsInstaller.pl

COPY etc /spads_etc/
COPY var /spads_var/

# perl /opt/spads/spads.pl /opt/spads/etc/spads.conf
#ENTRYPOINT [ "/opt/spads-entrypoint.sh" ]
CMD [ "/opt/run-spads.sh" ]
