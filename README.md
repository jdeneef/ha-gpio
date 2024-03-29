# Home Assistant GPIO custom integration

**This is a spin-off from the [ha-rpi_gpio](https://github.com/thecode/ha-rpi_gpio) integration, adapted in [ha-gpio](https://codeberg.org/raboof/ha-gpio) to work with libgpiod2 instead and partially redone by me to get the button event driven and some cleanups **

The `gpio` integration supports the following platforms: `Binary Sensor` and `Switch`

# Installation

### Manual installation

Copy the `gpio` folder and all of its contents into your Home Assistant's `custom_components` folder. This folder is usually inside your `/config` folder. If you are running Hass.io, use SAMBA to copy the folder over. You may need to create the `custom_components` folder and then copy the `gpio` folder and all of its contents into it.

# Usage

## Platform
The `gpio` platform should be initialized using the path to the gpio chip. Default is `/dev/gpiochip0`. Add the following to your `configuration.yaml` file:

```yaml
# GPIO platform configuration
gpio:
  path: /dev/gpiochip0
```

## Binary Sensor

The `gpio` binary sensor platform allows you to read sensor values of the GPIOs of your device.

### Configuration

To use your device's GPIO in your installation, add the following to your `configuration.yaml` file:

```yaml
# Basic configuration.yaml entry
binary_sensor:
  - platform: gpio
    sensors:
      - port: 11
        name: "PIR Office"
      - port: 12
        name: "PIR Bedroom"
```

```yaml
# Full configuration.yaml entry
binary_sensor:
  - platform: gpio
    sensors:
      - port: 11
        name: "PIR Office"
        unique_id: "pir_office_sensor_port_11"
        bouncetime: 80
        invert_logic: true
        pull_mode: "DOWN"
      - port: 12
        name: "PIR Bedroom"
        unique_id: "pir_bedroom_sensor_port_12"
```

### Options

| Key            | Required | Default               | Type    | Description                                                                                                 |
| -------------- | -------- | --------------------- | --------|------------------------------------------------------------------------------------------------------------ |
| `sensors`      | yes      |                       | list    | List of sensor IO ports ([Raspberry Pi BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png))      |
| `name`         | yes      |                       | string  | The name for the binary sensor entity                                                                       |
| `unique_id`    | no       |                       | string  | An ID that uniquely identifies the sensor. Set this to a unique value to allow customization through the UI |
| `bouncetime`   | no       | `50`                  | integer | The time in milliseconds for port debouncing                                                                |
| `invert_logic` | no       | `false` (ACTIVE HIGH) | boolean | If `true`, inverts the output logic to ACTIVE LOW                                                           |
| `pull_mode`    | no       | `UP`                  | string  | Type of internal pull resistor to use: `UP` - pull-up resistor, `DOWN` - pull-down resistor                 |

For more details about the Raspberry Pi GPIO layout, visit the Wikipedia [article](https://en.wikipedia.org/wiki/Raspberry_Pi#General_purpose_input-output_(GPIO)_connector) about the Raspberry Pi.

## Switch

The `gpio` switch platform allows you to control the GPIOs of your device.

### Configuration

To use your device's GPIO in your installation, add the following to your `configuration.yaml` file:

```yaml
# Basic configuration.yaml entry
switch:
  - platform: gpio
    switches:
      - port: 11
        name: "Fan Office"
      - port: 12
        name: "Light Desk"
```

```yaml
# Full configuration.yaml entry
switch:
  - platform: gpio
    switches:
      - port: 11
        name: "Fan Office"
        unique_id: "fan_office_switch_port_11"
      - port: 12
        name: "Light Desk"
        unique_id: "light_desk_switch_port_12"
        invert_logic: true
```

### Options

| Key            | Required | Default | Type    | Description                                                                                                 |
| -------------- | -------- | ------- | --------| ----------------------------------------------------------------------------------------------------------- |
| `switches`     | yes      |         | list    | List of switch IO ports ([Raspberry Pi BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png))      |
| `name`         | yes      |         | string  | The name for the switch entity                                                                              |
| `unique_id`    | no       |         | string  | An ID that uniquely identifies the switch. Set this to a unique value to allow customization through the UI |
| `invert_logic` | no       | `false` | boolean | If true, inverts the output logic to ACTIVE LOW                                                             |

For more details about the Raspberry Pi GPIO layout, visit the Wikipedia [article](https://en.wikipedia.org/wiki/Raspberry_Pi#General_purpose_input-output_(GPIO)_connector) about the Raspberry Pi.

A common question is what does Port refer to, this number is the actual GPIO #, not the pin #.
For example, if you have a relay connected to pin 11 its GPIO # is 17.

```yaml
# Basic configuration.yaml entry
switch:
  - platform: gpio
    switches:
      - port: 17
        name: "Speaker Relay"
```
