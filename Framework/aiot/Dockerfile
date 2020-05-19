FROM ubuntu:18.04
LABEL Author="Jack Chen" email="Q36061020@gs.ncku.edu.tw" organization="RTESLAB,EE,NCKU"
ENV DEBIAN_FRONTEND=noninteractive
RUN mkdir /AIOT-CORE &&\
    ln -fs /usr/share/zoneinfo/Asiz/Taipei /etc/localtime &&\
    apt update &&\
    apt install -y --no-install-recommends\
    tzdata\
    python3.8\
    python2.7\
    python-setuptools\
    build-essential\
    python-dev\
    python-pip\
    python3-pip &&\
    dpkg-reconfigure --frontend noninteractive tzdata &&\
    python3.8 -m pip install requests crate --no-cache-dir&&\
    python2.7 -m pip install wheel --no-cache-dir&&\
    python2.7 -m pip install nupic --no-cache-dir&&\
    python2.7 -m pip install pymysql --upgrade --no-cache-dir&&\
    python2.7 -m pip uninstall -y wheel &&\
    apt remove -y build-essential python-pip python-dev python3-pip &&\
    apt autoremove -y && apt autoclean -y && rm -rf /var/lib/apt/lists/*
COPY ./Data-Flow-Controller /AIOT-CORE
COPY nupic-default.xml /usr/local/lib/python2.7/dist-packages/nupic/support/
WORKDIR /AIOT-CORE
ENV USER=root
CMD ["python3.8","aiotServer.py"]