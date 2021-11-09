# Install

Raspbian buster

```bash
unzip -p 2021-05-07-raspios-buster-armhf-lite.zip | sudo dd status=progress of=/dev/mmcblk0 bs=4M conv=fsync
```

# Raspi-config

Network / Hostname: alarmxxxx
Locale / Locale: de_DE@UTF_8
Locale / Timezone: Europa/Berlin
Locale / Match Keyboard layout
Interfacing / SSH / enable

# Kernel Configuration

Copy [this configuration file](config.txt) to /boot/config.txt

It sets the correct video mode and enables sound via HDMI.

# Network

```bash
vi /etc/dhcpcd.conf
```

```config
# Example static IP configuration:
interface eth0
static ip_address=...
static ip6_address=...
static routers=...
static domain_name_servers=...
```

# Users

```bash
passwd pi
passwd root
```

# Software

```bash
sudo apt-get update

sudo apt-get install \
    cec-utils \
    command-not-found \
    cups \
    cups-bsd \
    git \
    libsox-fmt-mp3 \
    mercurial \
    pandoc \
    pulseaudio-utils \
    python-libcec \
    python3-babel \
    python3-caldav \
    python3-cheetah \
    python3-icalendar \
    python3-lxml \
    python3-mpltoolkits.basemap \
    python3-numpy \
    python3-openssl \
    python3-pip \
    python3-pyproj \
    python3-pyqt5 \
    python3-pyqt5.qtsvg \
    python3-requests \
    python3-rpi.gpio \
    python3-serial \
    python3-tzlocal \
    python3-urllib3 \
    python3-websocket \
    rrdtool \
    scrot \
    sox \
    texlive-fonts-recommended \
    texlive-latex-base \
    texlive-latex-recommended \
    vim \
    x11-xserver-utils \
    x11vnc \
    xinit

sudo apt-get upgrade

sudo pip3 install \
    gtts \
    imapclient \
    websocket-client
```

# Alarmdisplay Data

```bash
sudo mkdir -p /var/alarmdisplay/db
sudo mkdir -p /var/alarmdisplay/reports
sudo mkdir -p /opt/alarmdisplay/tiles
```

# Alarmdisplay Software

```bash
git clone https://gitlab.com/florianpose/alarmdisplay.git

cd alarmdisplay
sudo cp alarmdisplay-sample.conf /etc/alarmdisplay.conf
sudo vi /etc/alarmdisplay.conf

sudo cp alarmdisplay.service /etc/systemd/system
sudo systemctl enable alarmdisplay.service
sudo systemctl start alarmdisplay.service
```
