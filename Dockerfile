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
   libio-socket-ssl-perl \
   libdbi-perl \
   libinline-python-perl \
   libdbd-sqlite3-perl \
 && apt-get autoremove \
 && rm -rf /var/run/apt \
 && useradd -m spads

RUN mkdir -p /opt/spads /spring-data

COPY docker/spadsInstaller.auto /opt/spads
COPY docker/scripts/*.sh /opt/
COPY docker/scripts/*.sh /opt/

RUN chown -R spads:spads /opt /spring-data

USER spads

RUN mkdir -p /opt/spring \
 && cd /opt/spring \
 && curl -SLO 'https://github.com/beyond-all-reason/spring/releases/download/spring_bar_%7BBAR105%7D105.1.1-475-gd112b9e/spring_bar_.BAR105.105.1.1-475-gd112b9e_linux-64-minimal-portable.7z' \
 && 7z x 'spring_bar_.BAR105.105.1.1-475-gd112b9e_linux-64-minimal-portable.7z' \
 && rm 'spring_bar_.BAR105.105.1.1-475-gd112b9e_linux-64-minimal-portable.7z'

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
