#!/bin/bash
#
# 4.7.2020 add ext ssd
#
pmount /dev/sda1 /media/usb_ssd
#
cd /home/chip/workspace/homeassistant
# source bin/activate
/home/chip/.pyenv/shims/hass --open-ui -c /media/usb_ssd/.homeassistant

