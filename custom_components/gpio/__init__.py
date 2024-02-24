"""Support for controlling GPIO pins of a device."""

import logging
_LOGGER = logging.getLogger(__name__)

from collections import defaultdict
from datetime import timedelta

import gpiod
import time

from homeassistant.const import (
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "gpio"
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.COVER,
    Platform.SWITCH,
]

# Using globals like this seems a bit icky, but since GPIO pins
# are global in very physical sense it might be fine.
gpiod_config = defaultdict(gpiod.LineSettings)
gpiod_lines = None
gpio_chip = None

def setup_entry(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the GPIO component."""
    global device_name
    _LOGGER.info("ha_gpio is initialized")
    gpio_chip = discover_gpiochip()
    _LOGGER.info("initialized gpiochip: {gpio_chip}")
    return True

def unload_entry(hass: HomeAssistant, entry) -> bool:
    """Stuff to do before stopping."""
    global gpiod_config, gpiod_lines
    _LOGGER.info("ha_gpio is being unloaded: {gpiod_lines}")

    gpiod_config.clear()
    if gpiod_lines:
      gpiod_lines.release()
    return True

def discover_gpiochip():
    for id in range(5):
        device_name = f"/dev/gpiochip{id}"
        is_device = gpiod.is_gpiochip_device(device_name)
        if is_device:
            with gpiod.Chip(device_name) as chip:
                info = chip.get_info()
                if "pinctrl" in info.label:
                    return device_name

def update_gpiod_lines():
    global gpiod_config, gpiod_lines, gpio_chip
    _LOGGER.debug("update_gpiod_lines: {gpiod_config}")
    
    if gpiod_lines:
        gpiod_lines.release()

    gpiod_lines = gpiod.request_lines(
        gpio_chip,
        consumer="ha-gpio",
        config=gpiod_config)

def setup_output(port, invert_logic):
    """Set up a GPIO as output."""
    _LOGGER.info(f"setup_output: {port}, {invert_logic}")
    global gpiod_config
    gpiod_config[port].direction = gpiod.line.Direction.OUTPUT
    gpiod_config[port].output_value = gpiod.line.Value.ACTIVE if invert_logic else gpiod.line.Value.INACTIVE

    update_gpiod_lines()

def setup_input(port, pull_mode):
    """Set up a GPIO as input."""
    _LOGGER.info(f"setup_input: { port }, { pull_mode }")
    global gpiod_config
    gpiod_config[port].direction = gpiod.line.Direction.INPUT
    gpiod_config[port].bias = gpiod.line.Bias.PULL_DOWN if pull_mode == "DOWN" else gpiod.line.Bias.PULL_UP

    update_gpiod_lines()

def write_output(port, value):
    """Write a value to a GPIO."""
    _LOGGER.debug(f"write_output: { port }, { value }")
    global gpiod_lines
    gpiod_lines.set_value(port, gpiod.line.Value.ACTIVE if value else gpiod.line.Value.INACTIVE)

def read_input(port):
    """Read a value from a GPIO."""
    _LOGGER.debug(f"read_output: { port }")
    global gpiod_lines
    return gpiod_lines.get_value(port) == gpiod.line.Value.ACTIVE

def edge_detect(port, bounce):
    """Add detection for RISING and FALLING events."""
    _LOGGER.info(f"edge_detect: { port }, { bounce }")
    global gpiod_config
    global gpiod_lines

    gpiod_config[port].edge_detection = gpiod.line.Edge.BOTH
    gpiod_config[port].bias = gpiod.line.Bias.PULL_UP
    gpiod_config[port].debounce_period = timedelta(milliseconds=bounce)
    gpiod_config[port].event_clock = gpiod.line.Clock.REALTIME
    
    return gpiod_lines.wait_edge_events(timedelta(milliseconds=500))
