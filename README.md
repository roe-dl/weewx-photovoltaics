# weewx-photovoltaics

Extension to WeeWX for processing data of the photovoltaics system E3/DC

## Prerequisites

```
pip install pye3dc
```

## Installation instructions

By now there is no installation script. Copy `photovoltaics.py` to the 
user directory of WeeWX and edit `weewx.conf` as follows:

```
[DataBindings]
    ...
    [[pv_binding]]
        database = pv_sqlite
        table_name = archive
        manager = weewx.manager.DaySummaryManager
        schema = user.photovoltaics.schema

[Databases]
    ...
    [[pv_sqlite]]
        database_name = photovoltaics.sdb
        database_type = SQLite

[Engine]
    [[Services]]
        prep_services = ..., user.photovoltaics.E3dcUnits
        data_services = ..., user.photovoltaics.E3dcService

[E3DC]
    [[S10EPRO]]
        protocol = RSCP
        host = replace_me
        username = replace_me
        password = replace_me
        api_key = replace_me
        query_interval = 1           # optional
        #mqtt_topic = "e3dc/weewx"   # normally not required
    [[ACTHOR]]
        protocol = MyPV
        host = replace_me
        #mqtt_topic = "acthor/weewx" # normally not required
    [[MQTT]]
        protocol = MQTT
        enable = true
        topic = "e3dc/weewx"

```

Restart WeeWX.

## Oberservation types

This extension provides several additional observation types
holding readings from the PV inverter.

To access these observation types you need to specify `data_binding =
pv_binding` 

### Battery storage

emsBatteryPower | W
emsBatteryCharge | %
emsBatteryChargePower | W
emsBatteryDischargePower | W
sumBatteryChargeEnergy | kWh
sumBatteryDischargeEnergy | kWh

### supply

emsGridPower | W
emsGridInPower | W
emsGridOutPower | W
emsSolarPower | W
emsAddPower | W
sumSolarEnergy | kWh
sumGridInEnergy | kWh
sumGridOutEnergy | kWh
sumAddEnergy | kWh

### Consumption

emsHousePower | W
emsWallPower | W
emsAutarky | %
sumHouseEnergy | kWh
sumWallEnergy | kWh

### Static values

installedPVPeakPower | W
installedBatteryCapacity | Wh
pvMaxAcPower | W
pvMaxBatChargePower | W
pvMaxBatDischargePower | W

### PM

pmGridPowerL1 | W
pmGridPowerL2 | W
pmGridPowerL3 | W
pmGridVoltageL1 | V
pmGridVoltageL2 | V
pmGridVoltageL3 | V
pmGridEnergyL1 | kWh
pmGridEnergyL2 | kWh
pmGridEnergyL3 | kWh

### myPV ACTHOR

heataccuTemp | °C
heataccuVoltage | V
heataccuPower | W
heataccuMainsVoltage | V
heataccuMainsCurrent | A

## Database

Readings are saved to `photovoltaics.sdb`

## MQTT

Reading can be output to MQTT. You need an MQTT broker for that.

## Links

[Python-E3/DC-driver](https://github.com/fsantini/python-e3dc)
[E3/DC photovolatics inverter](https://www.e3dc.com)
[myPV ACTHOR 9 and 9s](https://www.my-pv.com/de/produkte/ac-thor-9s)
