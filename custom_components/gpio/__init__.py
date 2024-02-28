"""Support for controlling GPIO pins of a device."""

import logging
_LOGGER = logging.getLogger(__name__)

from collections import defaultdict
from datetime import timedelta

import gpiod
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    Platform,
    EVENT_HOMEASSISTANT_STOP,
    CONF_PATH
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "gpio"
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.COVER,
    Platform.SWITCH,
]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({
            vol.Optional(CONF_PATH, default="/dev/gpiochip0"): cv.string
        })
    },
    extra=vol.ALLOW_EXTRA
)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the GPIO component."""
    path = config.get(DOMAIN, {}).get(CONF_PATH) or "/dev/gpiochip0" # last part for backwards compatibility
    _LOGGER.debug(f"Initializing {path}")
    if not gpiod.is_gpiochip_device(path):
        _LOGGER.warning(f"initilization failed: {path} not a gpiochip_device")
        return False
    with gpiod.Chip(path) as chip:
        info = chip.get_info()
        if "pinctrl" not in info.label:
            _LOGGER.warning(f"initialization failed: {path} no pinctrl")
            return False
    _LOGGER.debug(f"initialized: {path}")
    hass.data[DOMAIN] = { 
            "path": path,
            "config": defaultdict(gpiod.LineSettings),
            "lines": None
        }
    _LOGGER.debug(f"data: {hass.data[DOMAIN]}")

    def cleanup_gpio(event):
        """Stuff to do before stopping."""
        _LOGGER.debug("cleanup")
        hass.data[DOMAIN].config.clear()
        if hass.data[DOMAIN].lines:
            hass.data[DOMAIN].lines.release()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup_gpio)

    return True


