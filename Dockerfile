FROM python:2.7.14-wheezy
# Use the new sources for debian. From here: https://superuser.com/questions/1423486/issue-with-fetching-http-deb-debian-org-debian-dists-jessie-updates-inrelease
# If you don't use this, apt-get will return a 404
RUN printf "deb http://archive.debian.org/debian/ jessie main\ndeb-src http://archive.debian.org/debian/ jessie main\ndeb http://security.debian.org jessie/updates main\ndeb-src http://security.debian.org jessie/updates main" > /etc/apt/sources.list
RUN apt-get update -qq && apt-get upgrade -qqy

RUN mkdir -p /srv/tns-glass
ADD final-requirements.txt /srv/tns-glass

RUN ls /srv/tns-glass
RUN yes w | pip install -r /srv/tns-glass/final-requirements.txt

# Set the locale (https://stackoverflow.com/a/38553499/418706) - Because we're using Debian for development.  This is done to be able to use en_US.UTF8 as locale. (Look at urls.py)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

ENV LANG en_US.UTF-8 

EXPOSE 8000 