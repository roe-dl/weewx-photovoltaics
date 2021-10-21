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

Tag | Unit | Alt. Unit
----|------|----------
`emsBatteryPower` | W | kW
`emsBatteryCharge` | % |
`emsBatteryChargePower` | W | kW
`emsBatteryDischargePower` | W | kW
`sumBatteryChargeEnergy` | Wh | kWh
`sumBatteryDischargeEnergy` | Wh | kWh

### Supply

Tag | Unit | Alt. Unit
----|------|----------
`emsGridPower` | W | kW
`emsGridInPower` | W | kW
`emsGridOutPower` | W | kW
`emsSolarPower` | W | kW
`emsAddPower` | W | kW
`sumSolarEnergy` | Wh | kWh
`sumGridInEnergy` | Wh | kWh
`sumGridOutEnergy` | Wh | kWh
`sumAddEnergy` | Wh | kWh

### Consumption

Tag | Unit | Alt. Unit
----|------|----------
`emsHousePower` | W | kW
`emsWallPower` | W | kW
`emsAutarky` | % |
`sumHouseEnergy` | Wh | kWh
`sumWallEnergy` | Wh | kWh

### Static values

Tag | Unit |
----|------|
`installedPVPeakPower` | W
`installedBatteryCapacity` | Wh
`pvMaxAcPower` | W
`pvMaxBatChargePower` | W
`pvMaxBatDischargePower` | W

### PM

Tag | Unit |
----|------|
`pmGridPowerL1` | W
`pmGridPowerL2` | W
`pmGridPowerL3` | W
`pmGridVoltageL1` | V
`pmGridVoltageL2` | V
`pmGridVoltageL3` | V
`pmGridEnergyL1` | kWh
`pmGridEnergyL2` | kWh
`pmGridEnergyL3` | kWh

### myPV ACTHOR

Tag | Unit |
----|------|
`heataccuTemp` | °C
`heataccuVoltage` | V
`heataccuPower` | W
`heataccuMainsVoltage` | V
`heataccuMainsCurrent` | A

## Database

Readings are saved to `photovoltaics.sdb`

## MQTT

Reading can be output to MQTT. You need an MQTT broker for that.

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
