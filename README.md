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

Tag | Unit | Alternative Unit | Description
----|------|------------------|-----------
`emsBatteryPower` | W | kW | actual charge (postive) or discharge (negative) power
`emsBatteryCharge` | % | charge level
`emsBatteryChargePower` | W | kW | actual charge power
`emsBatteryDischargePower` | W | kW | actual discharge power
`sumBatteryChargeEnergy` | Wh | kWh | calculated charge energy
`sumBatteryDischargeEnergy` | Wh | kWh | calculated discharge energy

### Supply

Tag | Unit | Alternative Unit | Description
----|------|------------------|----------------
`emsGridPower` | W | kW | actual grid power, positive values mean consumption
`emsGridPurchasePower` | W | kW | actual grid power purchased
`emsGridFeedinPower` | W | kW | actual power feeded into grid
`emsSolarPower` | W | kW | actual solar production power
`emsAddPower` | W | kW | actual power of an additional supply
`sumSolarEnergy` | Wh | kWh | solar energy produced
`sumGridPurchaseEnergy` | Wh | kWh | energy received from grid
`sumGridFeedinEnergy` | Wh | kWh | energy sent to grid
`sumAddEnergy` | Wh | kWh | energy produced by additional supply

### Consumption

Tag | Unit | Alternative Unit | Description
----|------|------------------|------------
`emsHousePower` | W | kW | inhouse consumption power
`emsWallPower` | W | kW | wallbox consumption power
`emsAutarky` | % | | autarky level
`sumHouseEnergy` | Wh | kWh | calculated inhouse consumption energy
`sumWallEnergy` | Wh | kWh | calculated wallbox consumption energy

### Static values

Tag | Unit | Alternative Unit
----|------|-----------------
`installedPVPeakPower` | W | kW
`installedBatteryCapacity` | Wh | kWh
`pvMaxAcPower` | W | kW
`pvMaxBatChargePower` | W | kW
`pvMaxBatDischargePower` | W | kW

### PM

Readings of the power meter included in the E3/DC system

Tag | Unit | Description
----|------|-----------------
`pmGridPowerL1` | W | actual power at phase L1
`pmGridPowerL2` | W | actual power at phase L2
`pmGridPowerL3` | W | actual power at phase L3
`pmGridVoltageL1` | V  | actual voltage at phase L1
`pmGridVoltageL2` | V | actual voltage at phase L2
`pmGridVoltageL3` | V | actual voltage at phase L3
`pmGridEnergyL1` | kWh | electricity meter at phase L1 *)
`pmGridEnergyL2` | kWh | electricity meter at phase L2 *)
`pmGridEnergyL3` | kWh | electricity meter at phase L3 *)

*) upwards counting for getting energy from the grid, downwards counting for
sending energy into the grid, even negative values are possible

### myPV ACTHOR

Tag | Unit |
----|------|
`heataccuTemp` | °C
`heataccuVoltage` | V
`heataccuPower` | W
`heataccuMainsVoltage` | V
`heataccuMainsCurrent` | A

Note: The field `unixtime` in `data.jsn` is bogus. MyPV acknowledged that
bug and announced to remove it with the next release.

## Database

Readings are saved to `photovoltaics.sdb`

## MQTT

Readings can be output to MQTT. You need an MQTT broker for that.

## Usage in skins

### Belchertown skin

Example, what to add to `graphs.conf`:
```
[PV-Anlage]
    title = "PV-Anlage"
    show_button = true
    button_text = "PV-Anlage"
    data_binding = pv_binding
    page_content = """
some general text"""

    [[pvGraphToday]]
        time_length = today
        tooltip_date_format = "LLL"
        gapsize = 300 
        title = PV-Leistung heute
        yAxis_label = Leistung
        exporting = 1
        [[[emsSolarPower]]]
            name = "PV-Leistung (5-Minuten-Durchschnitt)"
            color = "#ffc83f"

    [[solarRadGraph]]
        time_length = today
        tooltip_date_format = "LLL"
        gapsize = 300 
        title = "Sonnenstrahlung und UV-Index heute"
        exporting = 1
        [[[radiation]]]
            name = Sonnenstrahlung
            zIndex = 1
            color = "#ffc83f"
        [[[maxSolarRad]]]
            name = Theoretischer Maximalwert
            type = area
            color = "#f7f2b4"
            yAxis_label = "W/m&sup2;"
        [[[UV]]]
            yAxis = 1
            yAxis_min = 0
            yAxis_max = 14
            color = "#90ed7d"
            yAxis_label = "UV"
            name = "UV-Index"
            zIndex = 2

    [[pvGraphWeek]]
        time_length = 604800 # Last 7 days
        tooltip_date_format = "LLLL"
        aggregate_type = avg
        aggregate_interval = 3600 # 1 hour
        gapsize = 3600 # 1 hour in seconds
        start_at_whole_hour = true
        title = PV-Leistung Woche
        yAxis_label = Leistung
        exporting = 1
        [[[emsSolarPower]]]
            name = "PV-Leistung (Stundendurchschnitt)"
            color = "#ffc83f"

    [[PVEnergy]]
        time_length = 2592000 # Last 30 days
        tooltip_date_format = "dddd LL"
        gapsize = 86400 # 1 day in seconds
        title = "PV-Ertrag"
        aggregate_interval = 86400
        yAxis_label = Energie
        yAxis_label_unit = "Wh"
        start_at_midnight = true
        exporting = 1
        [[[emsSolarPower]]]
            name = Tagesertrag
            aggregate_type = energy_integral
            type = column
            color = "#ffc83f"

    [[PVmax]]
        time_length = 2592000 # Last 30 days
        tooltip_date_format = "dddd LL"
        gapsize = 86400 # 1 day in seconds
        title = "Tägliches Leistungsmaximum"
        aggregate_interval = 86400
        yAxis_label = Leistung
        #yAxis_label_unit = "W"
        start_at_midnight = true
        exporting = 1
        [[[emsSolarPower]]]
            name = Tagesleistungsmaximum
            aggregate_type = max
            type = spline
            color = "#ffc83f"
```

See `skins/Belchertown/about/photovoltaics.html.tmpl` for an example
PV page with live update of solar power by MQTT. Please note: The
example assumes the readings to be stored in weewx.sdb rather than
photovoltaics.sdb. So add `data_binding = pv_binding` to change
that if necessary.

## Links

* [Python-E3/DC-driver](https://github.com/fsantini/python-e3dc)
* [E3/DC photovolatics inverter](https://www.e3dc.com)
* [myPV ACTHOR 9 and 9s](https://www.my-pv.com/de/produkte/ac-thor-9s)
* [example page](https://www.woellsdorf-wetter.de/about/photovoltaics.html)
