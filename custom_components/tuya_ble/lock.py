"""The Tuya BLE integration - Lock platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .devices import TuyaBLEData, TuyaBLEEntity, TuyaBLEProductInfo
from .tuya_ble import TuyaBLEDataPointType, TuyaBLEDevice

_LOGGER = logging.getLogger(__name__)


class TuyaBLELock(TuyaBLEEntity, LockEntity):
    """Representation of a Tuya BLE Lock."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        device: TuyaBLEDevice,
        product: TuyaBLEProductInfo,
    ) -> None:
        super().__init__(
            hass,
            coordinator,
            device,
            product,
            LockEntityDescription(
                key="lock",
                name="Lock",
                icon="mdi:lock",
            ),
        )
        self._control_dp_id = 33  # DP for lock/unlock control (automatic_lock)
        self._status_dp_id = 47   # DP for lock status (lock_motor_state)

    @property
    def is_locked(self) -> bool | None:
        """Return true if lock is locked."""
        # Read status from DP 47 (lock_motor_state)
        datapoint = self._device.datapoints.get(self._status_dp_id)
        if datapoint is not None:
            return bool(datapoint.value)
        return None

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        _LOGGER.debug("%s: Locking", self._device.address)
        # Use DP 33 to toggle - if currently unlocked (False), set to True to lock
        datapoint = self._device.datapoints.get_or_create(
            self._control_dp_id,
            TuyaBLEDataPointType.DT_BOOL,
            False,
        )
        if datapoint and not self.is_locked:
            await datapoint.set_value(True)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        _LOGGER.debug("%s: Unlocking", self._device.address)
        # Use DP 33 to toggle - if currently locked (True), set to False to unlock
        datapoint = self._device.datapoints.get_or_create(
            self._control_dp_id,
            TuyaBLEDataPointType.DT_BOOL,
            False,
        )
        if datapoint and self.is_locked:
            await datapoint.set_value(False)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tuya BLE locks."""
    data: TuyaBLEData = hass.data[DOMAIN][entry.entry_id]
    entities: list[TuyaBLELock] = []

    # Add lock entity for Smart Lock devices (category "ms")
    if data.device.category == "ms":
        entities.append(
            TuyaBLELock(
                hass,
                data.coordinator,
                data.device,
                data.product,
            )
        )

    async_add_entities(entities)
