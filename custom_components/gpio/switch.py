"""Allows to configure a switch using GPIO."""
from __future__ import annotations
from . import _LOGGER

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_SWITCHES,
    CONF_UNIQUE_ID,
    DEVICE_DEFAULT_NAME,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
# from homeassistant.helpers.reload import setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity import generate_entity_id

from . import DOMAIN, _LOGGER

import gpiod
from gpiod.line import Direction, Value

CONF_PORTS = "ports"
CONF_INVERT_LOGIC = "invert_logic"
DEFAULT_INVERT_LOGIC = False

_SWITCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_SWITCHES, CONF_SWITCHES): vol.All(
                cv.ensure_list, [_SWITCH_SCHEMA]
            ),
            vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        },
    ),
    cv.has_at_least_one_key(CONF_PORTS, CONF_SWITCHES),
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the GPIO switches."""
    _LOGGER.debug(f"initializing switches {config}")
    # setup_reload_service(hass, DOMAIN, PLATFORMS)

    switches = []
    switches_conf = config.get(CONF_SWITCHES)
    if switches_conf is None:
        return
    for switch in switches_conf:
        _LOGGER.debug(f"adding switch: {switch}")
        switches.append(
            GPIOSwitch(
                switch[CONF_NAME],
                switch[CONF_PORT],
                switch[CONF_INVERT_LOGIC],
                switch.get(CONF_UNIQUE_ID),
            )
        )

        # add switch to gpiod config
        hass.data[DOMAIN]['config'][switch[CONF_PORT]] = gpiod.LineSettings(
            direction = Direction.OUTPUT,
            output_value = Value.ACTIVE if switch[CONF_INVERT_LOGIC] else Value.INACTIVE
        )

    async_add_entities(switches, True)
    if hass.data[DOMAIN]['lines']:
        hass.data[DOMAIN]['lines'].release()
    hass.data[DOMAIN]['lines'] = gpiod.request_lines(
        hass.data[DOMAIN]['path'],
        consumer = DOMAIN,
        config = hass.data[DOMAIN]['config']
    )
    return

class GPIOSwitch(SwitchEntity):
    """Representation of a GPIO Switch."""

    def __init__(self, name, port, invert_logic, unique_id=None):
        """Initialize the pin."""
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_unique_id = unique_id
        self._attr_should_poll = False
        self._port = port
        self._invert_logic = invert_logic
        self._state = False
        self.entity_id = generate_entity_id("switch.{}", self._attr_name, [], self.hass)

    @property
    def name(self) -> str:
        """Return name of the sensor."""
        return self._attr_name

    @property
    def unique_id(self) -> str|None:
        """Return name of the sensor."""
        return self._attr_unique_id

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state != self._invert_logic

    def turn_on(self, **kwargs):
        """Turn the device on."""
        value = Value.INACTIVE if self._invert_logic else Value.ACTIVE
        _LOGGER.debug(f"write_output: { self._port }, {value}")
        self.hass.data[DOMAIN]['lines'].set_value(self._port, value)
        self._state = True
        self.schedule_update_ha_state(False)

    def turn_off(self, **kwargs):
        """Turn the device off."""
        value = Value.ACTIVE if self._invert_logic else Value.INACTIVE
        _LOGGER.debug(f"write_output: { self._port }, {value}")
        self.hass.data[DOMAIN]['lines'].set_value(self._port, value)
        self._state = False
        self.schedule_update_ha_state(False)
