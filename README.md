vim: tw=78 spl=en spell

# Repository was moved to GitLab

> **Warning**
> This repository was moved to [GitLab](https://gitlab.com/florianpose/alarmdisplay).

# Alarm Display

This is an alarm display implementation for fire departments (etc). It has
been designed for the local circumstances of the Kreis Kleve, North
Rhine-Westphalia, Germany. It should be adaptable for other areas and
countries.

![Screenshot of idle mode](https://feuerwehr-kleve.de/images/alarmdisplay/alarmdisplay_idle.png)

## Hardware

The original hardware is a Raspberry Pi with a large display connected via
HDMI and a digital alarm pager connected via USB.

## Software

The software is written in Python3, using the PyQt libaries for Qt5.

## Features

- Alarm data display with target map and route map
- Maps using OpenStreetMap tiles or custom tiles with fire hydrants
- Alarm report document for printer output
- Receive alarms from pagers, IMAP or WebSockets (JSON)
- Show previous alarms, calendar information, weather data in idle mode
- Switch screen on and off via CEC
- Forward alarms to subsequent displays
- Use GPIO pins to switch lighting or open doors
- Play sounds and read alarm data with text-to-speech engines
- Display vehicle status
