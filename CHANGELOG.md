# Changelog

## Unreleased

Code review and modernization against Home Assistant 2026.11 (Python 3.14).
Requires Python 3.12+ (uses the `type` statement).

### Fixed

- **Security:** the plaintext password was logged at `INFO` level on every poll. The log line is removed and replaced with a `debug` message that omits credentials.
- **Security:** diagnostics now redact `username` and `password` (`async_redact_data`).
- **Config flow:** removed the deprecated `CONN_CLASS_LOCAL_POLL` and the legacy `@config_entries.HANDLERS.register(...)` decorator. `"iot_class": "local_polling"` is now set in `manifest.json`.
- **Config flow:** an HTTP 404 error is now attached to the host field instead of the password field.
- **Config flow:** a `TimeoutError` is now reported as `cannot_connect`.
- **Translations:** `strings.json` and `translations/en.json` used the key `hostname`, but the form field is `host`, so the label was not translated. Both are corrected.
- **Device registry:** the `via_device` deprecation warning is fixed. The Wifi logger (hub) device is registered before the platforms are set up, and the inverter references it with `via_device_id`. The lookup uses `async_get_device_by_identifier`.
- **Coordinator:** `getOffLineData` was called after the API session had been closed, and only `ClientConnectionError` was handled. Timeouts now fall back to offline data. HTTP and parse errors raise `UpdateFailed`.
- **Sensors:** removed the invalid `_attr_state = Type[float]` assignment.
- **Sensors:** the inverter `temperature`, `current_power` and `daily_power_yield` sensors are no longer `EntityCategory.DIAGNOSTIC`, so they can be used in the Energy dashboard.
- **Cache:** `last_seen` is restored from the cache as a timezone-aware `datetime` (it was a plain string). Old naive timestamps are treated as UTC. A corrupt cache is treated as missing.
- **Entities:** unloading and reloading the integration now works (`async_unload_entry` added).

### Changed

- **Entity naming:** entities use `has_entity_name = True` with short names, so the displayed name is now the device name plus a short name. `unique_id` values and existing entity IDs are unchanged, so history is kept.
- **Entity descriptions:** sensors and binary sensors are defined with `SensorEntityDescription` and `BinarySensorEntityDescription` subclasses instead of positional list mappings. They use `SensorDeviceClass`, `UnitOfTemperature`, `UnitOfPower`, `UnitOfEnergy` and `PERCENTAGE`.
- **Runtime data:** the coordinator is stored on `entry.runtime_data` (typed `SolisConfigEntry`) instead of `hass.data[DOMAIN][COORDINATOR]`. Removed the `COORDINATOR` constant and the unused `async_setup`.
- **HTTP session:** uses Home Assistant's shared client session (`async_get_clientsession`) instead of creating a new `aiohttp.ClientSession` on every poll. `SolisWifiApiManager` is removed.
- **Cache storage:** the last known state is stored with Home Assistant's `Store` (`.storage/solis_wifi_data_logger_<entry_id>`) instead of `solis_init_data.json` read through `aiofiles`. The `aiofiles` requirement is removed.
- **Coordinator:** uses `asyncio.timeout` instead of `async_timeout`, takes `config_entry`, and overrides `_async_update_data`.
- **Timestamps:** `last_seen` uses `dt_util.utcnow()` (timezone-aware).
- **Imports:** uses `homeassistant.const.EntityCategory`, `Platform` and `device_registry.DeviceInfo`.
- **Docker:** removed the obsolete `version:` key from `docker/docker-compose.yml`.

### Removed

- `options_update_listener`. It was never registered and the integration has no options flow.

### Notes

- The old `solis_init_data.json` is no longer read and can be deleted. The first offline start after upgrading has no cached state until one successful poll has been stored.
- Not yet addressed: the empty `documentation` URL in `manifest.json`.
