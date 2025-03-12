# weewx-photovoltaics

Extension to WeeWX for processing data of the photovoltaics system E3/DC

Display example:

<p align="center"><img src="example-display-800.png" /></p>

## Prerequisites

```
pip install pye3dc
```

## Installation instructions

Copy `photovoltaics.py` to the user directory of WeeWX and 
edit `weewx.conf` as follows:

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

There is an installer in the base directory, but it is alpha and untested.
Use it on your own risk. Make a backup of WeeWX before using the installer.
If you are not sure, copy photovoltaics.py to the user directory of WeeWX
manually, and also edit weewx.conf manually.

## Oberservation types

This extension provides several additional observation types
holding readings from the PV inverter.

To access these observation types you need to specify `data_binding =
pv_binding` 

### Battery storage

Tag | Unit | Alternative Unit | Description
----|------|------------------|-----------
`emsBatteryPower` | W | kW | actual charge (postive) or discharge (negative) power
`emsBatteryCharge` | % | | charge level
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
`sumGridFeedinEnergy` | Wh | kWh | energy feeded into grid
`sumAddEnergy` | Wh | kWh | energy produced by additional supply

### Consumption

Tag | Unit | Alternative Unit | Description
----|------|------------------|------------
`emsHousePower` | W | kW | inhouse consumption power
`emsWallPower` | W | kW | wallbox consumption power
`emsSelfConsumption` | % | | self-consumption level
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
feeding energy into the grid, even negative values are possible

### PVI DC

solar tracker readings 

Tag | Unit | Description
----|------|-----------------
`pviDCpowerT0` | W | actual power of tracker 1
`pviDCpowerT1` | W | actual power of tracker 2
`pviDCvoltageT0` | V | actual voltage of tracker 1
`pviDCvoltageT1` | V | actual voltage of tracker 2
`pviDCcurrentT0` | A | actual current of tracker 1
`pviDCcurrentT1` | A | actual current of tracker 2
`pviDCenergyT0` | Wh | earned energy so far for tracker 1
`pviDCenergyT1` | Wh | earned energy so far for tracker 2

### PVI AC

PV inverter AC output

Tag | Unit | Description
----|------|-----------------
`pviACpowerL1` | W | AC power L1
`pviACpowerL2` | W | AC power L2
`pviACpowerL3` | W | AC power L3
`pviACapparentPowerL1` | VA | AC apparent power L1
`pviACapparentPowerL2` | VA | AC apparent power L2
`pviACapparentPowerL3` | VA | AC apparent power L3
`pviACreactivePowerL1` | var | AC reactive power L1
`pviACreactivePowerL2` | var | AC reactive power L2
`pviACreactivePowerL3` | var | AC reactive power L3
`pviACvoltageL1` | V | AC voltage L1
`pviACvoltageL2` | V | AC voltage L2
`pviACvoltageL3` | V | AC voltage L3
`pviACcurrentL1` | A | AC current L1
`pviACcurrentL2` | A | AC current L2
`pviACcurrentL3` | A | AC current L3
`pviACenergyL1` | Wh | energy L1
`pviACenergyL2` | Wh | energy L2
`pviACenergyL3` | Wh | energy L3


### myPV ACTHOR

Tag | Unit |
----|------|
`heataccuTemp` | °C
`heataccuVoltage` | V
`heataccuPower` | W
`heataccuMainsVoltage` | V
`heataccuMainsCurrent` | A
`heataccuMainsFrequency` | Hz

Note: The field `unixtime` in `data.jsn` is bogus. MyPV acknowledged that
bug and announced to remove it with the next release.

### Sun

These observation types are only provided if they are not already there,
for example calculated by the WeeWX Skyfield almanac extension.

Tag | Unit | Description
----|------|------------
`solarAzimuth` | ° | solar azimuth (compass direction of the sun)
`solarAltitude` | ° | solar altitude
`solarPath` | % | percentage of the time elapsed between sunrise and sunset

What is the difference between `solarAzimuth`, `solarAltitude` and 
`$almanac.sun.az`, `$almanac.sun.alt`, respectively?

* `solarAzimuth` and `solarAltitude` are output to MQTT and thus allow
  live updates on web sites.
* As `solarAzimuth` and `solarAltitude` are observation types, they
  can be saved to the database (as they indeed are) and displayed
  in diagrams.

The values are calculated by the `Almanac` class that provides the
`$almanac` tag.

All those values honour temperature (`outTemp`) and pressure (`pressure`).

## Database

Readings are saved to `photovoltaics.sdb`

## MQTT

Readings can be output to MQTT. You need an MQTT broker for that.

## Usage in skins

### Display values (CheetahGenerator)

The observeration types described above can be used as any observation
type in WeeWX.

Examples:
```
$current.emsBatteryPower
$day($data_binding='pv_binding').emsGridPower.max
$week($data_binding='pv_binding').sumSolarEnergy.sum
$month($data_binding='pv_binding').emsHousePower.energy_integral
```

To get the energy for a time span, there are two ways:

* observation types `sum...Energy` together with aggregation type `sum`
* observation types `ems...Power` together with aggregation type
  `energy_integral`

The latter of them two requires the weewx-GTS extension to be installed.

Please note: The `sum...Energy` observation types integrate the respective
power over the archive interval. That results in a higher accuracy
than the E3/DC display shows, as there 15 minutes averages are used
for calculation. And it results in little differences in the readings.

#### Full load hours

Often people are interested in a measure of the degree of utilisation.
That measure is called full load hour (in german: Vollaststunde,
spezifischer Ertrag)
and measured in kWh/kWp or simply hours.

The following example shows how you could calculate und display full
load hours for various time periods within a template:
```
#from weewx.units import ValueTuple, ValueHelper
...
  <table class="table-striped">
    <tbody>
    <tr>
      <td></td>
      <td>Heute</td>
      <td>Gestern</td>
      <td>Diese Woche</td>
      <td>Diesen Monat</td>
      <td>Dieses Jahr</td>
    </tr>
#set $kwp=$current.installedPVPeakPower.kilowatt.raw
#if $kwp is not None and $kwp>0
#set $hday=$day(data_binding="pv_binding").emsSolarPower.energy_integral.kilowatt_hour.raw/$kwp*3600.0
#set $hday_vh=ValueHelper(ValueTuple($hday,'second','group_deltatime'),formatter=$station.formatter)
#set $hyday=$yesterday(data_binding="pv_binding").emsSolarPower.energy_integral.kilowatt_hour.raw/$kwp*3600.0
#set $hyday_vh=ValueHelper(ValueTuple($hyday,'second','group_deltatime'),formatter=$station.formatter)
#set $hweek=$week(data_binding="pv_binding").emsSolarPower.energy_integral.kilowatt_hour.raw/$kwp*3600.0
#set $hweek_vh=ValueHelper(ValueTuple($hweek,'second','group_deltatime'),formatter=$station.formatter)
#set $hmonth=$month(data_binding="pv_binding").emsSolarPower.energy_integral.kilowatt_hour.raw/$kwp*3600.0
#set $hmonth_vh=ValueHelper(ValueTuple($hmonth,'second','group_deltatime'),formatter=$station.formatter)
#set $hyear=$year(data_binding="pv_binding").emsSolarPower.energy_integral.kilowatt_hour.raw/$kwp*3600.0
#set $hyear_vh=ValueHelper(ValueTuple($hyear,'second','group_deltatime'),formatter=$station.formatter)
    <tr>
      <td>Vollaststunden</td>
      <td style="text-align:right">$hday_vh.format("%(hour)d:%(minute)02d:%(second)02d h")</td>
      <td style="text-align:right">$hyday_vh.format("%(hour)d:%(minute)02d:%(second)02d h")</td>
      <td style="text-align:right">$hweek_vh.format("%(hour)d:%(minute)02d:%(second)02d h")</td>
      <td style="text-align:right">$hmonth_vh.format("%(hour)d:%(minute)02d:%(second)02d h")</td>
      <td style="text-align:right">$hyear_vh.format("%(hour)d h")</td>
    </tr>
#end if
    </tbody>
  </table>
```

#### Energy consumption during day and night time

During the light day you can use the PV energy for yourself and reduce
energy costs. When it is dark you need energy from the grid or a
battery pack. To think about a battery you need to know how much
energy is consumed by night. So this is an example how to calculate it
for the day:
```
#from weewx.units import ValueTuple, ValueHelper
...
#set $n1=$daylight(horizon=2,use_center=1).emsHousePower.energy_integral.kilowatt_hour.raw-$day(data_binding="pv_binding").heataccuPower.energy_integral.kilowatt_hour.raw
#set $n1_vh=ValueHelper(ValueTuple($n1,'kilowatt_hour','group_energy'),formatter=$station.formatter)
#set $n2=$day.emsHousePower.energy_integral.kilowatt_hour.raw-$daylight(horizon=2,use_center=1).emsHousePower.energy_integral.kilowatt_hour.raw
#set $n2_vh=ValueHelper(ValueTuple($n2,'kilowatt_hour','group_energy'),formatter=$station.formatter)
<p>heating: $day(data_binding="pv_binding").heataccuPower.energy_integral.kilowatt_hour</p>
<p>daylight consumption (without heating): $n1_vh</p>
<p>night consumption: $n1_vh</p>
```

To calculate those values for the week is more difficult:
```
#set $weekEd=0.0
#set $weekEn=0.0
#for $span in $LMTweek(data_binding="pv_binding").days
#for $pp in $span.daylights(horizon=1,use_center=1)
#set $houseday=$pp.emsHousePower.energy_integral.kilowatt_hour.raw
#end for
#set $heat=$span.heataccuPower.energy_integral.kilowatt_hour.raw
#set $house=$span.emsHousePower.energy_integral.kilowatt_hour.raw
#if $houseday is not None and $heat is not None and $house is not None
#set $weekEd+=$houseday-$heat
#set $weekEn+=$house-$houseday
#end if
#end for
#set $weekEd_vh=ValueHelper(ValueTuple($weekEd,'kilowatt_hour','group_energy'),formatter=$station.formatter)
#set $weekEn_vh=ValueHelper(ValueTuple($weekEn,'kilowatt_hour','group_energy'),formatter=$station.formatter)
<p>week heating: $week(data_binding="pv_binding").heataccuPower.energy_integral.kilowatt_hour</p>
<p>week daylight consumption: $weekEd_vh</p>
<p>week night consumption: $weekEn_vh</p>
```

To use those examples [weewx-GTS](https://github.com/roe-dl/weewx-GTS)
neeeds to be installed. It provides the `$daylight` and `.daylights`
time spans.

Those examples assume it is light enough for the PV modules to produce
energy if the altitude of the sun is above 2°.

### Diagrams (ImageGenerator)

in `skin.conf`:
```
[ImageGenerator]
    ...
    [[day_images]]
        ...
        [[[dayPV]]]
            data_binding = pv_binding
            [[[[emsSolarPower]]]]
                label = Sonne
                color = "#ffc83f"
            [[[[emsGridPower]]]]
                label = Netz
            [[[[emsBatteryPower]]]]
                label = Batterie
            [[[[emsHousePower]]]]
                label = Verbrauch

        [[[dayPVcharge]]]
            data_binding = pv_binding
            yscale = 0,100,10
            [[[[emsBatteryCharge]]]]
                label = Ladestand der Batterie
```
Repeat those definitions with `week`, `month`, and `year`

To show those diagrams add the appropriate img tags in a template:
```
<img src="dayPV.png" />
<img src="dayPVcharge.png />
```

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

To show a diagram about solar course you could use the following configuration:
```
    [[sunpath]]
        time_length = 172800
        title = "Sonnenstand"
        yAxis_label = Winkel
        [[[solarPath]]]
            zIndex = 2
            yAxis = 1
            yAxis_min = -25
            yAxis_max = 100
            yAxis_tickInterval = 25
            yAxis_label = "Zeit (%)"
        [[[solarAzimuth]]]
            yAxis = 0
            yAxis_min = -90
            yAxis_max = 360
            yAxis_tickInterval = 90
        [[[solarAltitude]]]
            yAxis = 0
            yAxis_min = -90
            yAxis_max = 360
            yAxis_tickInterval = 90
```


## Links

* [Python-E3/DC-driver](https://github.com/fsantini/python-e3dc)
* [E3/DC photovolatics inverter](https://www.e3dc.com)
* [myPV ACTHOR 9 and 9s](https://www.my-pv.com/de/produkte/ac-thor-9s)
* [example page](https://www.woellsdorf-wetter.de/photovoltaics/)
* [photovoltaics icons](https://github.com/roe-dl/photovoltaicsicons)
