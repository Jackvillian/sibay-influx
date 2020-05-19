FROM ubuntu:16.04
RUN apt-get update && apt install -y cron  vim software-properties-common build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
RUN wget https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tgz && tar -xf Python-3.7.4.tgz
RUN cd Python-3.7.4 && ./configure --enable-optimizations  --disable-test-suite && make -j 8 && make altinstall
RUN python3.7 -m pip install pip
ADD requirements.txt /tmp/requirements.txt
RUN pip3.7 install -r /tmp/requirements.txt
ADD owencloud.py /srv/owencloud.py
ADD owen-so2 /etc/cron.d/owen-so2
RUN chmod 0644 /etc/cron.d/owen-so2
RUN crontab /etc/cron.d/owen-so2
RUN touch /var/log/cron.log
CMD ["cron", "-f"]
