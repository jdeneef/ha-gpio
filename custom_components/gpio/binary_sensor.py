"""Support for binary sensor using GPIO."""
from __future__ import annotations
from . import _LOGGER
from datetime import timedelta

# import asyncio
import threading

import voluptuous as vol

from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_SENSORS,
    CONF_UNIQUE_ID,
    DEVICE_DEFAULT_NAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
# from homeassistant.helpers.reload import setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity import generate_entity_id

from . import DOMAIN, PLATFORMS

import gpiod
from gpiod.line import Direction, Bias, Edge, Clock, Value

CONF_BOUNCETIME = "bouncetime"
CONF_INVERT_LOGIC = "invert_logic"
CONF_PORTS = "ports"
CONF_PULL_MODE = "pull_mode"

DEFAULT_BOUNCETIME = 50
DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = "UP"

_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
        vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_SENSORS, CONF_SENSORS): vol.All(
                cv.ensure_list, [_SENSOR_SCHEMA]
            ),
            vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
            vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
            vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
        },
    ),
    cv.has_at_least_one_key(CONF_PORTS, CONF_SENSORS),
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
    ) -> None:
    """Set up the GPIO binary_sensors."""
    _LOGGER.debug(f"initializing binary_sensors {config}")
    # setup_reload_service(hass, DOMAIN, PLATFORMS)

    sensors = []

    sensors_conf = config.get(CONF_SENSORS)
    if sensors_conf is None:
        return
    for sensor in sensors_conf:
        _LOGGER.debug(f"adding sensor: {sensor}")
        sensors.append(
            GPIOBinarySensor(
                sensor[CONF_NAME],
                sensor[CONF_PORT],
                sensor[CONF_PULL_MODE],
                sensor[CONF_BOUNCETIME],
                sensor[CONF_INVERT_LOGIC],
                sensor.get(CONF_UNIQUE_ID),
            )
        )
        # add binary_sensor to gpiod config
        hass.data[DOMAIN]['config'][sensor[CONF_PORT]] = gpiod.LineSettings(
            direction = Direction.INPUT,
            bias = Bias.PULL_DOWN if sensor[CONF_PULL_MODE]== "DOWN" else Bias.PULL_UP,
            edge_detection = Edge.BOTH,
            debounce_period = timedelta(milliseconds=sensor[CONF_BOUNCETIME]),
            event_clock= Clock.REALTIME
        )

    # add entities to hass
    async_add_entities(sensors, True)
    # add gpiod lines to hass
    if hass.data[DOMAIN]['lines']:
        hass.data[DOMAIN]['lines'].release()
    hass.data[DOMAIN]['lines'] = gpiod.request_lines(
        hass.data[DOMAIN]['path'],
        consumer = DOMAIN,
        config = hass.data[DOMAIN]['config']
    )

    listener = Listener(hass, sensors)
    # thread = threading.Thread(target=listener.listen_for_events)
    # thread.start()

    # asyncio.create_task(listener.listen_for_events())

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, listener.stop)

    return 

class Listener:
    """event listener, listening for edge_events"""
    def __init__(self, hass, sensors):
        _LOGGER.debug("starting gpio edge listener")
        self.running = False
        self.hass = hass
        self.sensors = sensors
        self.thread = threading.Thread(target=self.listen_for_events)
        self.thread.start()

    def handle_event(self, events):
        for event in events:
            _LOGGER.debug(f"Event: {event.event_type} {event.line_offset} {event.timestamp_ns}")
            for sensor in self.sensors:
                if sensor._port == event.line_offset:
                    sensor.update()

    def listen_for_events(self):
        self.running = True
        while self.running:
            events = self.hass.data[DOMAIN]['lines'].read_edge_events()
            self.handle_event(events)

    def stop(self, event, **kwargs):
        _LOGGER.debug(f"stopping listener {event}")
        self.running = False

class GPIOBinarySensor(BinarySensorEntity):
    """Represent a binary sensor that uses GPIO."""

    def __init__(self, name, port, pull_mode, bouncetime, invert_logic, unique_id=None):
        """Initialize the binary sensor."""
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_unique_id = unique_id
        self._attr_should_poll = False
        self._port = port
        self._pull_mode = pull_mode
        self._bouncetime = bouncetime
        self._invert_logic = invert_logic
        self._state:bool | None = None
        self.entity_id = generate_entity_id("sensor.{}", self._attr_name, [], self.hass)

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
        """Return the state of the entity."""
        return self._state != self._invert_logic

    def update(self) -> None:
        """Update the GPIO state."""
        value = self.hass.data[DOMAIN]['lines'].get_value(self._port)
        self._state = ((value == Value.ACTIVE) != self._invert_logic)
        _LOGGER.debug(f"updating sensor {self._port} to {value} with {self._state}")
        self.schedule_update_ha_state(False)
