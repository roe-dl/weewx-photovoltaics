#!/usr/bin/python3 
#
# WeeWX service to read data from E3/DC power station
#
# Copyright (C) 2021 Johanna Roedenbeck
# thanks to Tom Keffer and Matthew Wall for WeeWX weather software
# RSCP API copyright Hager Energy GmbH
# MQTT output inspired by weewx-mqtt by Matthew Wall

VERSION = "0.7"

import threading
import configobj
import time
import json
import sys

from e3dc import E3DC,AuthenticationError,CommunicationError,FrameError

# deal with differences between python 2 and python 3
try:
    # Python 3
    import queue
except ImportError:
    # Python 2
    # noinspection PyUnresolvedReferences
    import Queue as queue

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


if __name__ != '__main__':
    from weewx.engine import StdService
    import weewx.units
    import weewx.accum
    import weewx.almanac
    import weewx.xtypes
    import weeutil.weeutil
else:
    # for standalone testing
    import collections
    class StdService(object):
        def __init__(self, engine, config_dict):
            pass
        def bind(self,p1,p2):
            #print("bind %s %s" % (p1.__name__,p2.__name__))
            pass
    class weewx(object):
        NEW_LOOP_PACKET = 1
        NEW_ARCHIVE_RECORD = 2
        class UnknownType(Exception):
            pass
        class UnknownAggregation(Exception):
            pass
        class CannotCalculate(Exception):
            pass
        class units(object):
            def convertStd(p1, p2):
                return p1
            def convert(p1, p2):
                return (p1[0],p2,p1[2])
            obs_group_dict = collections.ChainMap()
            default_unit_label_dict = collections.ChainMap()
            default_unit_format_dict = collections.ChainMap()
            class ValueHelper(object):
                def __init__(self, x):
                    self.x = x
                @property
                def raw(self):
                    return self.x
        class accum(object):
            accum_dict = collections.ChainMap()
            class Accum(object):
                def __init__(self, x):
                    pass
                def addRecord(self,x,**kvargs):
                    pass
            class OutOfSpan(ValueError):
                pass
        class almanac(object):
            class Almanac(object):
                def __init__(self, time_ts, lat, lon,
                 altitude=None,
                 temperature=None,
                 pressure=None,
                 horizon=None,
                 moon_phases=None,
                 formatter=None,
                 converter=None):
                    pass
                def sunrise(self):
                    return weewx.units.ValueHelper(None)
                def sunset(self):
                    return weewx.units.ValueHelper(None)
        class xtypes(object):
            pass
    class weeutil(object):
        class weeutil(object):
            def to_int(x):
                return int(x)
            def to_float(x):
                return float(x)
            def startOfInterval(x,y):
                return time.time()
            def TimeSpan(x,y):
                return (x,y)
            def startOfDay(x):
                return x
    class Event(object):
        def __init__(self):
            self.packet = { 'usUnits':16 }
    class Engine(object):
        class stn_info(object):
            latitude_f = 51.123
            longitude_f = 13.040
            altitude_vt = (0,'meter','group_altitude')
        class db_binder(object):
            def get_manager(binding='wx_binding'):
                return None
        archive_interval = 300
        class db_binder(object):
            def get_manager(**kvargs):
                pass

try:
    # Test for new-style weewx logging by trying to import weeutil.logger
    import weeutil.logger
    import logging
    log = logging.getLogger("user.E3DC")

    def logdbg(msg):
        log.debug(msg)

    def loginf(msg):
        log.info(msg)

    def logerr(msg):
        log.error(msg)

except ImportError:
    # Old-style weewx logging
    import syslog

    def logmsg(level, msg):
        syslog.syslog(level, 'user.E3DC: %s' % msg)

    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)

    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)

    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)


from e3dc._rscpLib import rscpFindTag

class WxE3DC(E3DC):
    
    #from e3dc._rscpLib import rscpFindTag
    
    def get_PM_data(self, pmIndex, keepAlive=False):
        
        req = ('PM_REQ_DATA', 'Container', [ 
                  ('PM_INDEX', 'Uint16', pmIndex), 
                  ('PM_REQ_POWER_L1', 'None', None), 
                  ('PM_REQ_POWER_L2', 'None', None), 
                  ('PM_REQ_POWER_L3', 'None', None), 
                  ('PM_REQ_MAX_PHASE_POWER', 'None', None),
                  ('PM_REQ_ENERGY_L1', 'None', None), 
                  ('PM_REQ_ENERGY_L2', 'None', None), 
                  ('PM_REQ_ENERGY_L3', 'None', None),
                  ('PM_REQ_VOLTAGE_L1', 'None', None), 
                  ('PM_REQ_VOLTAGE_L2', 'None', None), 
                  ('PM_REQ_VOLTAGE_L3', 'None', None),
                  ('PM_REQ_TYPE', 'None', None)])
        
        reply = self.sendRequest(req)
        
        x = dict()
        for ii in req[2]:
            if ii[0].find('REQ')>0:
                key = ii[0].replace('_REQ_','_')
                val = rscpFindTag(reply, key)[2]
                key = ii[0].replace('_REQ_','_%s_' % pmIndex)
                x[key] = val
        
        return x

    def get_PVI_AC_data(self, pviIndex, phase, keepAlive=False):
        req = self.sendRequest(
            (
                "PVI_REQ_DATA",
                "Container",
                [
                        ("PVI_INDEX", "Uint16", pviIndex),
                        ("PVI_REQ_AC_POWER", "Uint16", phase),
                        ("PVI_REQ_AC_VOLTAGE", "Uint16", phase),
                        ("PVI_REQ_AC_CURRENT", "Uint16", phase),
                        ("PVI_REQ_AC_APPARENTPOWER", "Uint16", phase),
                        ("PVI_REQ_AC_REACTIVEPOWER", "Uint16", phase),
                        ("PVI_REQ_AC_ENERGY_ALL", "Uint16", phase),
                        ("PVI_REQ_AC_ENERGY_GRID_CONSUMPTION", "Uint16", phase),
                ],
            ),
            keepAlive,
        )
        return {
          'PVI_AC_POWER': rscpFindTag(rscpFindTag(req, "PVI_AC_POWER"), "PVI_VALUE")[2],
          'PVI_AC_VOLTAGE': rscpFindTag(rscpFindTag(req, "PVI_AC_VOLTAGE"), "PVI_VALUE")[2], 
          'PVI_AC_CURRENT': rscpFindTag(rscpFindTag(req, "PVI_AC_CURRENT"), "PVI_VALUE")[2],
          'PVI_AC_APPARENTPOWER': rscpFindTag(rscpFindTag(req, "PVI_AC_APPARENTPOWER"), "PVI_VALUE")[2],
          'PVI_AC_REACTIVEPOWER': rscpFindTag(
                        rscpFindTag(req, "PVI_AC_REACTIVEPOWER"), "PVI_VALUE"
                    )[2],
          'PVI_AC_ENERGY_ALL': rscpFindTag(
                        rscpFindTag(req, "PVI_AC_ENERGY_ALL"), "PVI_VALUE"
                    )[2],
          'PVI_AC_ENERGY_GRID_CONSUMPTION': rscpFindTag(
                        rscpFindTag(req, "PVI_AC_ENERGY_GRID_CONSUMPTION"), "PVI_VALUE"
                    )[2]
          }
    
    def get_PVI_DC_data(self, pviIndex, string, keepAlive=False):
        req = self.sendRequest(
            (
                "PVI_REQ_DATA",
                "Container",
                [
                        ("PVI_INDEX", "Uint16", pviIndex),
                        ("PVI_REQ_DC_POWER", "Uint16", string),
                        ("PVI_REQ_DC_VOLTAGE", "Uint16", string),
                        ("PVI_REQ_DC_CURRENT", "Uint16", string),
                        ("PVI_REQ_DC_STRING_ENERGY_ALL", "Uint16", string),
                ],
            ),
            keepAlive
        )
        return {
            'PVI_DC_POWER': rscpFindTag(rscpFindTag(req, "PVI_DC_POWER"), "PVI_VALUE")[2],
            'PVI_DC_VOLTAGE': rscpFindTag(rscpFindTag(req, "PVI_DC_VOLTAGE"), "PVI_VALUE")[2],
            'PVI_DC_CURRENT': rscpFindTag(rscpFindTag(req, "PVI_DC_CURRENT"), "PVI_VALUE")[2],
            'PVI_DC_ENERGY_ALL': rscpFindTag(
                        rscpFindTag(req, "PVI_DC_STRING_ENERGY_ALL"), "PVI_VALUE"
                    )[2]
        }
    

# unit labels for optional MQTT output
try:
    from user.mqtt import UNIT_REDUCTIONS
except ImportError:
    UNIT_REDUCTIONS = {
        'watt_per_meter_squared': 'Wpm2',
        'uv_index': None,
        'percent': None,
        'unix_epoch': None }

ACCUM_SUM = { 'extractor':'sum' }
ACCUM_STRING = { 'accumulator':'firstlast','extractor':'last' }
ACCUM_LAST = { 'extractor':'last' }
    
E3DC_OBS = {
    # storage
    'consumption_battery':('emsBatteryPower','watt','group_power',None),
    'stateOfCharge':('emsBatteryCharge','percent','group_percent',None),
    'charge':('emsBatteryChargePower','watt','group_power',None),
    'discharge':('emsBatteryDischargePower','watt','group_power',None),
    'sumBatteryChargeEnergy':('sumBatteryChargeEnergy','watt_hour','group_energy',ACCUM_SUM),
    'sumBatteryDischargeEnergy':('sumBatteryDischargeEnergy','watt_hour','group_energy',ACCUM_SUM),
    # supply
    'production_grid':('emsGridPower','watt','group_power',None),
    'gridIn':('emsGridPurchasePower','watt','group_power',None),
    'gridOut':('emsGridFeedinPower','watt','group_power',None),
    'production_solar':('emsSolarPower','watt','group_power',None),
    'production_add':('emsAddPower','watt','group_power',None),
    'sumSolarEnergy':('sumSolarEnergy','watt_hour','group_energy',ACCUM_SUM),
    'sumGridInEnergy':('sumGridPurchaseEnergy','watt_hour','group_energy',ACCUM_SUM),
    'sumGridOutEnergy':('sumGridFeedinEnergy','watt_hour','group_energy',ACCUM_SUM),
    'sumAddEnergy':('sumAddEnergy','watt_hour','group_energy',ACCUM_SUM),
    # consumption
    'consumption_house':('emsHousePower','watt','group_power',None),
    'consumption_wallbox':('emsWallPower','watt','group_power',None),
    'selfConsumption':('emsSelfConsumption','percent','group_percent',None),
    'autarky':('emsAutarky','percent','group_percent',None),
    'sumHouseEnergy':('sumHouseEnergy','watt_hour','group_energy',ACCUM_SUM),
    'sumWallEnergy':('sumWallEnergy','watt_hour','group_energy',ACCUM_SUM),
    # balance
    'balance':('emsBalance','watt','group_power',None),
    # static values
    'installedPeakPower':('installedPVPeakPower','watt','group_power',None),
    'installedBatteryCapacity':('installedBatteryCapacity','watt_hour','group_energy',None),
    'maxAcPower':('pvMaxAcPower','watt','group_power',None),
    'maxBatChargePower':('pvMaxBatChargePower','watt','group_power',None),
    'maxBatDischargePower':('pvMaxBatDischargePower','watt','group_power',None),
    # PM
    'PM_6_POWER_L1':('pmGridPowerL1','watt','group_power',None),
    'PM_6_POWER_L2':('pmGridPowerL2','watt','group_power',None),
    'PM_6_POWER_L3':('pmGridPowerL3','watt','group_power',None),
    'PM_6_VOLTAGE_L1':('pmGridVoltageL1','volt','group_volt',None),
    'PM_6_VOLTAGE_L2':('pmGridVoltageL2','volt','group_volt',None),
    'PM_6_VOLTAGE_L3':('pmGridVoltageL3','volt','group_volt',None),
    'PM_6_ENERGY_L1':('pmGridEnergyL1','watt_hour','group_energy',ACCUM_LAST),
    'PM_6_ENERGY_L2':('pmGridEnergyL2','watt_hour','group_energy',ACCUM_LAST),
    'PM_6_ENERGY_L3':('pmGridEnergyL3','watt_hour','group_energy',ACCUM_LAST),
    # PVI
    'PVI_DC_VOLTAGE_T0':('pviDCvoltageT0','volt','group_volt',None),
    'PVI_DC_CURRENT_T0':('pviDCcurrentT0','amp','group_amp',None),
    'PVI_DC_POWER_T0':('pviDCpowerT0','watt','group_power',None),
    'PVI_DC_ENERGY_ALL_T0':('pviDCenergyT0','watt_hour','group_energy',ACCUM_LAST),

    'PVI_DC_VOLTAGE_T1':('pviDCvoltageT1','volt','group_volt',None),
    'PVI_DC_CURRENT_T1':('pviDCcurrentT1','amp','group_amp',None),
    'PVI_DC_POWER_T1':('pviDCpowerT1','watt','group_power',None),
    'PVI_DC_ENERTY_ALL_T1':('pviDCenergyT1','watt_hour','group_energy',ACCUM_LAST),

    'PVI_AC_APPARENTPOWER_L1':('pviACapparentPowerL1','watt','group_power',None),
    'PVI_AC_POWER_L1':('pviACpowerL1','watt','group_power',None),
    'PVI_AC_REACTIVEPOWER_L1':('pviACreactivePowerL1','watt','group_power',None),
    'PVI_AC_VOLTAGE_L1':('pviACvoltageL1','volt','group_volt',None),
    'PVI_AC_CURRENT_L1':('pviACcurrentL1','amp','group_amp',None),
    'PVI_AC_ENERGY_ALL_L1':('pviACenergyL1','watt_hour','group_energy',ACCUM_LAST),

    'PVI_AC_APPARENTPOWER_L2':('pviACapparentPowerL2','watt','group_power',None),
    'PVI_AC_POWER_L2':('pviACpowerL2','watt','group_power',None),
    'PVI_AC_REACTIVEPOWER_L2':('pviACreactivePowerL2','watt','group_power',None),
    'PVI_AC_VOLTAGE_L2':('pviACvoltageL2','volt','group_volt',None),
    'PVI_AC_CURRENT_L2':('pviACcurrentL2','amp','group_amp',None),
    'PVI_AC_ENERGY_ALL_L2':('pviACenergyL2','watt_hour','group_energy',ACCUM_LAST),

    'PVI_AC_APPARENTPOWER_L3':('pviACapparentPowerL3','watt','group_power',None),
    'PVI_AC_POWER_L3':('pviACpowerL3','watt','group_power',None),
    'PVI_AC_REACTIVEPOWER_L3':('pviACreactivePowerL3','watt','group_power',None),
    'PVI_AC_VOLTAGE_L3':('pviACvoltageL3','volt','group_volt',None),
    'PVI_AC_CURRENT_L3':('pviACcurrentL3','amp','group_amp',None),
    'PVI_AC_ENERGY_ALL_L3':('pviACenergyL3','watt_hour','group_energy',ACCUM_LAST),

    }

MYPV_OBS = {
    'temp1':('heataccuTemp','degree_C','group_temperature',None),
    'volt_out':('heataccuVoltage','volt','group_volt',None),
    'power_act':('heataccuPower','watt','group_power',None),
    'volt_mains':('heataccuMainsVoltage','volt','group_volt',None),
    'curr_mains':('heataccuMainsCurrent','amp','group_amp',None),
    'freq':('heataccuMainsFrequency','hertz','group_frequency',None)
    }

WX_OBS = [
    'dateTime','interval',
    'radiation','maxSolarRad',
    'solarAzimuth','solarAltitude','solarPath']

##############################################################################
#    Database schema                                                         #
##############################################################################

"""
This schema is used to create a separate database to store the data of the 
solar power plant and additional devices. It is created out of the 
translation tables before. If the weather station includes a radiation 
sensor, its readings are included here, too.
"""

exclude_from_summary = ['dateTime', 'usUnits', 'interval'] + [
    E3DC_OBS[e][0] for e in E3DC_OBS if E3DC_OBS[e][3]==ACCUM_LAST ] + [
    'solarAzimuth', 'solarAltitude', 'solarPath' ]
    
table = [('dateTime',             'INTEGER NOT NULL UNIQUE PRIMARY KEY'),
         ('usUnits',              'INTEGER NOT NULL'),
         ('interval',             'INTEGER NOT NULL'),
         ('solarAzimuth',         'REAL'),
         ('solarAltitude',        'REAL'),
         ('solarPath',            'REAL'),
         ('radiation',            'REAL'),
         ('maxSolarRad',          'REAL')] + [
         (E3DC_OBS[key][0],'REAL') for key in E3DC_OBS] + [
         (MYPV_OBS[key][0],'REAL') for key in MYPV_OBS]

day_summaries = [(e[0], 'scalar') for e in table
                 if e[0] not in exclude_from_summary] 

schema = {
    'table': table,
    'day_summaries' : day_summaries
}

##############################################################################

def _get_obs_type(tag):
    if tag is None: return None
    result = tag.split('_')
    rtn = result[0].lower()
    for ii in result[1:]:
        rtn = rtn + ii.capitalize()
    return rtn

##############################################################################
#    Base thread for retrieving data                                         #
##############################################################################

class BaseThread(threading.Thread):

    def __init__(self, thread_name, protocol):
        super(BaseThread,self).__init__()
        self.name = thread_name
        self.protocol = protocol
        # mark thread as active
        self.running = True
        # buffer for the received data
        self.lock = threading.Lock()
        self.evt = threading.Event()
        self.data = []
        self.last_get_ts = time.time()
        
    def shutDown(self):
        """ request shutdown of the thread """
        self.running = False
        self.evt.set()
        loginf("thread '%s': shutdown requested" % self.name)

    def get_data(self):
        """ get buffered data and empty buffer """
        try:
            self.lock.acquire()
            try:
                last_ts = self.data[-1]['time']
                interval = last_ts - self.last_get_ts
                self.last_get_ts = last_ts
            except (LookupError,TypeError,ValueError,ArithmeticError):
                interval = None
            data = self.data
            self.data = []
        finally:
            self.lock.release()
        #loginf("get_data interval %s data %s" % (interval,data))
        return data,interval

    def put_data(self, x):
        """ store newly received data to buffer and to MQTT queue if any """
        if x:
            if self.mqtt_queue and self.mqtt_topic:
                try:
                    self.mqtt_queue.put(
                                (self.mqtt_topic,x,self.protocol),
                                block=False)
                except queue.Full:
                    # If the queue is full (which should not happen),
                    # ignore the packet
                    pass
                except (KeyError,ValueError,LookupError,ArithmeticError) as e:
                    logerr("thread '%s': %s" % (self.name,e))
            try:
                self.lock.acquire()
                self.data.append(x)
            finally:
                self.lock.release()

##############################################################################
#    Thread to retrieve data from myPV
##############################################################################

import http.client

class MyPVThread(BaseThread):

    #import http.client
    
    def __init__(self, thread_name, protocol, address, query_interval, mqtt_queue, mqtt_topic):
        super(MyPVThread,self).__init__(thread_name, protocol)
        self.address = address
        self.query_interval = weeutil.weeutil.to_float(query_interval)
        self.mqtt_queue = mqtt_queue
        self.mqtt_topic = mqtt_topic
        self.acthor9s = None
        loginf("thread '%s', host '%s': initialized" % (self.name,self.address))
        
    def read_device_config(self):
        """ read config out of device """
        loginf("thread '%s', host '%s': read device config" % (self.name,self.address))
        reply = None
        try:
            connection = http.client.HTTPConnection(self.address)
            connection.request('GET','/setup.jsn')
            response = connection.getresponse()
            if response.status==200:
                reply = response.read()
            else:
                logerr("thread '%s', host '%s': Status %s - %s" % (self.name,self.address,response.status,response.reason))
        except http.client.HTTPException as e:
            logerr("thread '%s', host '%s': %s - %s" % (self.name,self.address,e.__class__.__name__,e))
        except OSError as e:
            loginf("thread '%s', host '%s': %s - %s" % (self.name,self.address,e.__class__.__name__,e))
        finally:
            connection.close()
        if reply:
            x = json.loads(reply)
            loginf("thread '%s', host '%s': S/N %s" % (self.name,self.address,x.get('serialno','unknown')))
            # value: 1 for AC-THOR, 2 for AC-THOR 9s
            self.acthor9s = x.get('acthor9s')
            try:
                self.acthor9s = weeutil.weeutil.to_int(self.acthor9s)
            except Exception:
                pass
            loginf("thread '%s', host '%s': type %s - %s" % (self.name,self.address,self.acthor9s,'AC-THOR'))
            if self.acthor9s==1:
                # AC-THOR --> MYPV_OBS already contains the right key
                pass
            elif self.acthor9s==2:
                # AC-THOR 9s --> replace 'power_act' by 'power_ac9'
                MYPV_OBS['power_ac9'] = MYPV_OBS.pop('power_act')


    def run(self):
        self.read_device_config()
        loginf("thread '%s', host '%s': starting" % (self.name,self.address))
        try:
            last_status = 0
            while self.running:
                reply = None
                try:
                    connection = http.client.HTTPConnection(self.address)
                    connection.request('GET','/data.jsn')
                    response = connection.getresponse()
                    if response.status!=last_status:
                        last_status = response.status
                        loginf("thread '%s', host '%s': Status %s - %s" % (self.name,self.address,response.status,response.reason))
                    if response.status==200:
                        reply = response.read()
                except http.client.HTTPException as e:
                    if last_status!=11111:
                        logerr("thread '%s', host '%s': %s - %s" % (self.name,self.address,e.__class__.__name__,e))
                    last_status = 11111
                except OSError as e:
                    if last_status!=22222:
                        logerr("thread '%s', host '%s': %s - %s" % (self.name,self.address,e.__class__.__name__,e))
                    last_status = 22222
                finally:
                    connection.close()
                if reply:
                    x = json.loads(reply)
                    # temperatures are in 10th of degree Centigrade
                    # currents are in 10th of amperes
                    for ii in x:
                        if len(ii)>=4 and ii[0:4] in ('temp','curr'):
                            try:
                                x[ii] = weeutil.weeutil.to_float(x[ii])/10.0
                            except (ArithmeticError,TypeError,ValueError):
                                pass
                        if ii=='freq':
                            try:
                                x[ii] = weeutil.weeutil.to_float(x[ii])/1000.0
                            except (ArithmeticError,TypeError,ValueError):
                                pass
                    # x['time'] = x['unixtime'] # unixtime is bogus
                    x['time'] = time.time()
                    #loginf(x)
                    self.put_data(x)
                self.evt.wait(self.query_interval)
        except Exception as e:
            logerr("thread '%s', host '%s': %s - %s" % (self.name,self.address,e.__class__.__name__,e))
        finally:
            loginf("thread '%s', host '%s' stopped" % (self.name,self.address))


##############################################################################
#    Thread to retrieve data from the E3/DC S10 station                      #
##############################################################################

class E3dcThread(BaseThread):

    def __init__(self, thread_name, protocol, username, password, address, api_key, query_interval=1.0, mqtt_queue=None, mqtt_topic=None):
        super(E3dcThread,self).__init__(thread_name,protocol)
        self.username = username
        self.password = password
        self.address = address
        self.api_key = api_key
        self.query_interval = weeutil.weeutil.to_float(query_interval)
        self.mqtt_queue = mqtt_queue
        self.mqtt_topic = mqtt_topic
        loginf("thread '%s', host '%s': initialized" % (self.name,self.address))
        
    def run(self):
        loginf("thread '%s', host '%s': starting" % (self.name,self.address))
        try:
            connection = WxE3DC(E3DC.CONNECT_LOCAL, 
                                username=self.username, 
                                password=self.password, 
                                ipAddress = self.address, 
                                key = self.api_key)
            loginf("thread '%s', host '%s': S/N %s%s" % (self.name,self.address,connection.serialNumberPrefix,connection.serialNumber))
            loginf("thread '%s', host '%s': installed PV power %.1f kW, installed battery capacity %.1f kW, maximum AC power %.1f kW" % (self.name,self.address,connection.installedPeakPower/1000.0,connection.installedBatteryCapacity/1000.0,connection.maxAcPower/1000.0))
            last_ts = time.time()
            err_ct = 0
            while self.running:
                try:
                    if err_ct<5: err_ct += 1
                    result = connection.poll(keepAlive=True)
                except AuthenticationError:
                    logerr("thread '%s': authentication failed" % self.name)
                    time.sleep(60*err_ct)
                    continue
                #except e3dc.NotAvailableError:
                #    logerr("thread '%s': not available" % self.name)
                #    time.sleep(60*err_ct)
                #    continue
                #except e3dc.SendError as e:
                #    logerr("thread '%s': send error %s" % (self.name,e))
                #    time.sleep(10*err_ct)
                #    continue
                except CommunicationError as e:
                    logerr("thread '%s': communication error %s" % (self.name,e))
                    time.sleep(10*err_ct)
                    continue
                except Exception as e:
                    logerr("thread '%s': %s - %s" % (self.name,e.__class__.__name__,e))
                    time.sleep(10*err_ct)
                    continue
                try:
                    result2 = connection.get_PM_data(6)
                except (AuthenticationError,CommunicationError,Exception):
                    result2 = {}
                try:
                    result3 = self.get_pvi_data(connection)
                except (AuthenticationError,CommunicationError,Exception):
                    result3 = {}
                #loginf("run %s" % result)
                err_ct = 0
                # flatten the result dict
                x = {}
                for lvl1 in result:
                    if lvl1 in ('time',):
                        x[lvl1] = result[lvl1].timestamp()
                    elif isinstance(result[lvl1],dict):
                        for lvl2 in result[lvl1]:
                            key = '%s_%s' % (lvl1,lvl2)
                            if result[lvl1][lvl2] is not None:
                                try:
                                    x[key] = weeutil.weeutil.to_float(
                                                            result[lvl1][lvl2])
                                except (ValueError,TypeError,LookupError):
                                    pass
                    else:
                        if result[lvl1] is not None:
                            try:
                                x[lvl1] = weeutil.weeutil.to_float(
                                                                  result[lvl1])
                            except (ValueError,TypeError,LookupError):
                                pass
                # result2 PM
                try:
                    # check that all readings can be converted to float
                    for lvl1 in result2:
                        try:
                            result2[lvl1] = weeutil.weeutil.to_float(
                                                                 result2[lvl1])
                        except (ValueError,TypeError,LookupError):
                            pass
                    # insert 
                    x.update(result2)
                except Exception:
                    pass
                # result3 PVI
                x.update(result3)
                # calculate time period since last record
                if last_ts>0:
                    try:
                        since_last = (x['time']-last_ts) / 3600.0
                    except (TypeError,ValueError,ArithmeticError,LookupError):
                        since_last = None
                else:
                    since_last = None
                # add derived values
                try:
                    bat = x['consumption_battery']
                    if bat>=0.0:
                        bat_in = bat
                        bat_out = 0
                    else:
                        bat_in = 0
                        bat_out = -bat
                    x['charge'] = bat_in
                    x['discharge'] = bat_out
                    if since_last:
                        x['sumBatteryChargeEnergy'] = bat_in * since_last
                        x['sumBatteryDischargeEnergy'] = bat_out * since_last
                except (ArithmeticError,ValueError,TypeError,LookupError):
                    pass
                try:
                    grid = x['production_grid']
                    if grid>=0.0:
                        grid_in = grid
                        grid_out = 0
                    else:
                        grid_in = 0
                        grid_out = -grid
                    x['gridIn'] = grid_in
                    x['gridOut'] = grid_out
                    if since_last:
                        x['sumGridInEnergy'] = grid_in * since_last
                        x['sumGridOutEnergy'] = grid_out * since_last
                except (ArithmeticError,ValueError,TypeError,LookupError):
                    pass
                # should be always 0.0
                try:
                    x['balance'] = (x['consumption_battery'] 
                                   + x['consumption_house']
                                   + x['consumption_wallbox']
                                   - x['production_grid']
                                   - x['production_solar']
                                   - x['production_add'])
                except (ArithmeticError,ValueError,TypeError,LookupError):
                    pass
                # calculate energy out of power and time
                if since_last:
                    try:
                        x['sumSolarEnergy'] = x['production_solar'] * since_last
                        x['sumHouseEnergy'] = x['consumption_house'] * since_last
                        x['sumWallEnergy'] = x['consumption_wall'] * since_last
                    except (ArithmeticError,ValueError,TypeError,LookupError):
                        pass
                # add static values
                try:
                    x['installedPeakPower'] = connection.installedPeakPower
                    x['installedBatteryCapacity'] = connection.installedBatteryCapacity
                    x['maxAcPower'] = connection.maxAcPower
                    x['maxBatChargePower'] = connection.maxBatChargePower
                    x['maxBatDischargePower'] = connection.maxBatDischargePower
                except (ArithmeticError,ValueError,TypeError,LookupError):
                    pass
                # store the result for further processing
                try:
                    if 'time' in x and x['time']>last_ts:
                        last_ts = x['time']
                        self.put_data(x)
                except (ValueError,TypeError,LookupError) as e:
                    logerr("thread '%s': cannot put into queue %s" % (self.name,e))
                # wait
                self.evt.wait(self.query_interval)
        except Exception as e:
            logerr("thread '%s', host '%s': %s - %s" % (self.name,self.address,e.__class__.__name__,e))
        finally:
            loginf("thread '%s', host '%s' stopped" % (self.name,self.address))
    
    def get_pvi_data(self, connection):
        """ 
            AC:
                AC_MAX_PHASE_COUNT
                
                Value der Anfrage beinhaltet die angefragte Phase
                
                AC_MAX_POWER, AC_POWER, AC_VOLTAGE, AC_CURRENT,
                AC_APPARENTPOWER, AC_REACTIVE_POWER, AC_ENERGY_ALL,
                AC_MAX_APPARENTPOWER, AC_ENERGY_DAY,
                AC_ENERGY_GRID_CONSUMPTION
            
            DC:
                DC_MAX_STRING_COUNT
                
                DC_POWER, DC_VOLTAGE, DC_CURRENT, DC_MAX_POWER,
                DC_MIN_VOLTAGE, DC_MAX_CURRENT, DC_MIN_CURRENT,
                DC_STRING_ENERGY_ALL
                
        """
        pviIndex = 0
        x = dict()
        """
        for tracker in range(0,2):
            pvi = connection.get_pvi_data(pviTracker=tracker,keepAlive=True)
            if pvi:
                for key in pvi:
                    trs = str(pvi['pviTracker'])
                    if key not in ['stringIndex','pviTracker']:
                        x['pvi'+trs+key] = pvi[key]
        """
        for tracker in range(0,2):
            tracker_name = 'T'+str(tracker)
            dc_data = connection.get_PVI_DC_data(pviIndex,tracker,keepAlive=True)
            for key in dc_data:
                x[key+'_'+tracker_name] = dc_data[key]
        for phase in range(0,3):
            phase_name = 'L'+str(phase+1)
            ac_data = connection.get_PVI_AC_data(pviIndex,phase,keepAlive=True)
            for key in ac_data:
                x[key+'_'+phase_name] = ac_data[key]
        #print(x)
        return x
    

##############################################################################
# Thread to output data to MQTT                                              #
##############################################################################

"""
    Note: If paho.mqtt is not available, MQTT output is silently discarded.
"""

try:

    import paho.mqtt.publish as mqtt

    class MqttThread(threading.Thread):

        def __init__(self, mqtt_queue, server_url, mqtt_port, obs_list=None):
            super(MqttThread,self).__init__()
            self.name = 'MQTT'
            self.mqtt_queue = mqtt_queue
            self.mqtt_port = mqtt_port
            self.running = True
            url = urlparse(server_url)
            if url.username and url.password:
                self.mqtt_auth = {'username':url.username,'password':url.password}
            else:
                self.mqtt_auth = None
            if mqtt_port:
                self.mqtt_port = mqtt_port
            elif url.port:
                self.mqtt_port = url.port
            else:
                self.mqtt_port = 1883
            self.mqtt_hostname = url.hostname
            if obs_list:
                self.wx_obs_list = obs_list
            else:
                self.wx_obs_list = WX_OBS
            loginf("thread '%s': broker %s port %s" % (self.name,self.mqtt_hostname,self.mqtt_port))
            loginf("thread '%s' initialized" % self.name)
        
        def shutDown(self):
            self.running = False
            loginf("thread '%s': shutdown requested" % self.name)
        
        def run(self):
            loginf("thread '%s' starting" % self.name)
            try:
                while self.running:
                    try:
                        reply = self.mqtt_queue.get(timeout=1.5)
                    except queue.Empty:
                        continue
                    try:
                        topic = reply[0]
                        queuesource = reply[2]
                        reply = reply[1]
                        x = dict()
                        if queuesource.upper()=='RSCP':
                            # data from E3/DC
                            if 'time' in reply:
                                x['dateTime'] = reply['time']
                            elif 'sysStatus' in reply:
                                x['sysStatus'] = reply['sysStatus']
                            for key in E3DC_OBS:
                                if key in reply:
                                    u = E3DC_OBS[key][1]
                                    if u and u in UNIT_REDUCTIONS:
                                        u = UNIT_REDUCTIONS[u]
                                    if u:
                                        mqtt_key = E3DC_OBS[key][0]+'_'+u
                                    else:
                                        mqtt_key = E3DC_OBS[key][0]
                                    val = reply[key]
                                    x[mqtt_key] = val
                        elif queuesource.upper()=='MYPV':
                            # data from ACTHOR
                            # Note: unixtime is bogus
                            if 'time' in reply:
                                x['dateTime'] = reply['time']
                            for key in MYPV_OBS:
                                if key in reply:
                                    u = MYPV_OBS[key][1]
                                    if u and u in UNIT_REDUCTIONS:
                                        u = UNIT_REDUCTIONS[u]
                                    if u:
                                        mqtt_key = MYPV_OBS[key][0]+'_'+u
                                    else:
                                        mqtt_key = MYPV_OBS[key][0]
                                    val = reply[key]
                                    x[mqtt_key] = val
                        else:
                            # data from WeeWX archive record or loop packet
                            for key in self.wx_obs_list:
                                if key in reply:
                                    if key=='dateTime':
                                        mqtt_key = key
                                    else:
                                        u = weewx.units.getStandardUnitType(
                                                reply['usUnits'],key,None)[0]
                                        if u and u in UNIT_REDUCTIONS:
                                            u = UNIT_REDUCTIONS[u]
                                        mqtt_key = key+'_'+u if u else key
                                    if key!='usUnits':
                                        x[mqtt_key] = reply[key]
                        # build MQTT messages
                        msgs = [(topic+'/loop',json.dumps(x),0,False)]
                        for key in x:
                            msgs.append((topic+'/'+key,x[key],0,False))
                        # send MQTT messages
                        if msgs:
                            mqtt.multiple(msgs,
                                hostname = self.mqtt_hostname ,port=self.mqtt_port,
                                client_id = "",
                                keepalive = 60,
                                will = None,
                                auth=self.mqtt_auth,
                                tls = None,
                                transport = "tcp")
                        
                    except Exception as e:
                        logerr("thread '%s', topics '%s/#': %s - %s" % (self.name,topic,e.__class__.__name__,e))
                        pass
                    try:
                        self.mqtt_queue.task_done()
                    except ValueError:
                        pass
            except Exception as e:
                logerr("thread '%s': %s" % (self.name,e))
            finally:
                loginf("thread '%s' stopped" % self.name)

    has_mqtt = True
    
except ImportError as e:

    has_mqtt = False
    logerr(e)


##############################################################################
#   data_services: augment LOOP packet with readings from E3/DC S10          #
##############################################################################

class E3dcService(StdService):

    def __init__(self, engine, config_dict):
        super(E3dcService,self).__init__(engine, config_dict)
        loginf("E3/DC %s service" % VERSION)
        self.log_success = config_dict.get('log_success',True)
        self.log_failure = config_dict.get('log_failure',True)
        self.debug = weeutil.weeutil.to_int(config_dict.get('debug',0))
        if self.debug>0:
            self.log_success = True
            self.log_failure = True
        self.dbm = None
        self.archive_interval = 300
        # MQTT output
        try:
            mqtt_host = config_dict['StdRESTful']['MQTT']['server_url']
        except Exception:
            mqtt_host = None
        try:
            mqtt_enable = config_dict['E3DC']['MQTT'].get('enable',True)
            mqtt_host = config_dict['E3DC']['MQTT'].get('server_url',mqtt_host)
            mqtt_topic = config_dict['E3DC']['MQTT'].get('topic','e3dc/weewx')
        except Exception:
            mqtt_enable = False
            mqtt_topic = None
        if has_mqtt and mqtt_host and mqtt_enable:
            self.mqtt_queue = queue.Queue()
            self.mqtt_thread = MqttThread(self.mqtt_queue,mqtt_host,None)
            self.mqtt_thread.start()
        else:
            self.mqtt_queue = None
            self.mqtt_thread = None
            self.mqtt_topic = None
        # init database
        binding = config_dict['E3DC'].get('data_binding','pv_binding')
        if binding:
            binding_found = 'DataBindings' in config_dict.sections and binding in config_dict['DataBindings']
        else:
            binding_found = None
        self.dbm_init(engine,binding,binding_found)
        # station altitude
        try:
            self.altitude = weewx.units.convert(engine.stn_info.altitude_vt,'meter')[0]
        except (ValueError,TypeError,IndexError):
            self.altitude=None
        loginf("Altitude %s ==> %.0f m" % (engine.stn_info.altitude_vt,self.altitude))
        # initial value for sunrise, sunset
        try:
            alm = weewx.almanac.Almanac(time.time(),
                                        engine.stn_info.latitude_f,
                                        engine.stn_info.longitude_f,
                                        self.altitude)
            self.sunrise = alm.sunrise
            self.sunset = alm.sunset
            loginf("initial sunrise sunset %s %s" % (self.sunrise,self.sunset))
        except (LookupError,ArithmeticError,AttributeError) as e:
            logerr("cannot calculate intial sunrise sunset: %s" % e)
            self.sunrise = None
            self.sunset = None
        # helper values for calculating solarAzimuth, solarAltitude
        try:
            wx_manager = engine.db_binder.get_manager()
            timespan = weeutil.weeutil.TimeSpan(weeutil.weeutil.startOfDay(self.sunrise.raw),self.sunrise.raw)
            val = weewx.xtypes.get_aggregate('outTemp',timespan,'last',wx_manager)
            self.last_archive_outTemp = weewx.units.convert(val,'degree_C')[0]
            loginf("initial outTemp %s °C" % self.last_archive_outTemp)
            val = weewx.xtypes.get_aggregate('pressure',timespan,'last',wx_manager)
            self.last_archive_pressure = weewx.units.convert(val,'mbar')[0]
            loginf("initial pressure %s mbar" % self.last_archive_pressure)
            alm = weewx.almanac.Almanac(self.sunrise.raw,
                                        engine.stn_info.latitude_f,
                                        engine.stn_info.longitude_f,
                                        self.altitude,
                                        temperature=self.last_archive_outTemp,
                                        pressure=self.last_archive_pressure)
            self.sunrise = alm.sunrise
            self.sunset = alm.sunset
            loginf("adapted initial sunrise sunset %s %s" % (self.sunrise,self.sunset))
        except (LookupError,ArithmeticError,AttributeError,weewx.UnknownType, weewx.UnknownAggregation, weewx.CannotCalculate) as e:
            logerr("cannot determine outTemp and pressure at sunrise time: %s" % e)
            self.last_archive_outTemp = None   # degree_C
            self.last_archive_pressure = None  # mbar
        self.last_almanac_error = time.time()-300
        # create threads to retreive data from devices
        self.threads = dict()
        if 'E3DC' in config_dict:
            ct = 0
            for name in config_dict['E3DC'].sections:
                if config_dict['E3DC'][name].get('enable',
                        config_dict['E3DC'].get('enable',True)):
                    if self._create_thread(name,
                            config_dict['E3DC'][name],
                            config_dict['E3DC'][name].get('mqtt_topic',
                                mqtt_topic)):
                        ct += 1
            if ct>0:
                self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)
                self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        
    def _create_thread(self, thread_name, thread_dict, mqtt_topic):
        protocol = thread_dict.get('protocol','')
        address = thread_dict.get('host')
        query_interval = thread_dict.get('query_interval',1)
        # MQTT output thread is created elsewhere.
        if protocol.upper()=='MQTT' or thread_name=='MQTT': return False
        # IP address is mandatory.
        if not address:
            logerr("thread '%s': missing IP address" % thread_name) 
            return False
        # Logging
        loginf("thread %s, host %s, poll interval %s" % (thread_name,address,query_interval))
        #loginf("u %s p %s k %s" % (username,password,api_key))
        self.threads[thread_name] = dict()
        if protocol.upper()=='MYPV':
            self.threads[thread_name]['thread'] = MyPVThread(
                thread_name,
                protocol,
                address,
                query_interval,
                self.mqtt_queue,
                mqtt_topic)
        elif protocol.upper()=='RSCP':
            self.threads[thread_name]['thread'] = E3dcThread(
                thread_name,
                protocol,
                thread_dict.get('username'),
                thread_dict.get('password'),
                address,
                thread_dict.get('api_key'),
                query_interval,
                self.mqtt_queue,
                mqtt_topic)
        else:
            logerr("thread '%s': unknown protocol '%s'" % (thread_name,protocol))
            del self.threads[thread_name]
            return False
        self.threads[thread_name]['protocol'] = protocol
        if has_mqtt and mqtt_topic:
            self.threads[thread_name]['topic'] = mqtt_topic
        else:
            self.threads[thread_name]['topic'] = None
        self.threads[thread_name]['reply_count'] = 0
        self.threads[thread_name]['thread'].start()
        return True
    
    def shutDown(self):
        for ii in self.threads:
            try:
                self.threads[ii]['thread'].shutDown()
            except Exception:
                pass
        if has_mqtt and self.mqtt_thread:
            try:
                self.mqtt_thread.shutDown()
            except:
                pass
        # wait at max 10 seconds for shutdown to complete
        timeout = time.time()+10
        for ii in self.threads:
            try:
                w = timeout-time.time()
                if w<=0: break
                self.threads[ii]['thread'].join(w)
                if self.threads[ii]['thread'].is_alive():
                    logerr("unable to shutdown thread '%s'" % self.threads[ii]['thread'].name)
            except:
                pass
        w = timeout-time.time()
        if has_mqtt and self.mqtt_thread and w>0:
            try:
                self.mqtt_thread.join(w)
            except:
                pass
        # report threads that are still alive
        _threads = [ii for ii in self.threads]
        for ii in _threads:
            try:
                if self.threads[ii]['thread'].is_alive():
                    logerr("unable to shutdown thread '%s'" % self.threads[ii]['thread'].name)
                del self.threads[ii]['thread']
                del self.threads[ii]
            except:
                pass
        try:
            self.dbm_close()
        except Exception:
            pass
            
    def _process_data(self, thread_name):
        # get collected data
        data,interval = self.threads[thread_name]['thread'].get_data()
        # get protocol dependent observation types list
        if self.threads[thread_name]['protocol'].upper()=='MYPV': 
            result = { obs:[0,0] for obs in MYPV_OBS }
            obs_list = MYPV_OBS
        elif self.threads[thread_name]['protocol'].upper()=='RSCP':
            result = { obs:[0,0] for obs in E3DC_OBS }
            obs_list = E3DC_OBS
        else:
            return {}
        # accumulate values
        for ii,val in enumerate(data):
            #loginf("1 %s" % val)
            for key in val:
                try:
                    if key in ('time','unixtime'):
                        result[key] = val[key]
                    elif key in ('sysStatus'):
                        result[key] = val[key]
                    elif key[0:3]=='sum':
                        result[key][0] += val[key]
                        result[key][1] = 1  # without + !!!
                    elif key in result:
                        if obs_list[key][3]==ACCUM_LAST or obs_list[key][3]==ACCUM_STRING:
                            result[key][0] = val[key]
                            result[key][1] = 1
                        elif obs_list[key][3]==ACCUM_SUM:
                            result[key][0] += val[key]
                            result[key][1] = 1  # without + !!!
                        else:
                            result[key][0] += val[key]
                            result[key][1] += 1
                except Exception:
                    pass
        # extract values (average, sum, last)
        #loginf("2 %s" % result)
        x = {}
        for key in result:
            try:
                val = (
                    result[key][0] / result[key][1],
                    obs_list[key][1],
                    obs_list[key][2])
            except (TypeError,IndexError):
                val = result[key]
            except (ValueError,KeyError,ArithmeticError):
                val = None
            try:
                x[obs_list[key][0]] = val
            except (TypeError,ValueError,LookupError):
                x[key] = val
        # convert interval from seconds to minutes
        try:
            interval /= 60.0
        except (ArithmeticError,TypeError,ValueError):
            pass
        x['interval'] = (interval,'minute','group_interval')
        x['count'] = (len(data),'count','group_count')
        return x
        
    def new_loop_packet(self, event):
        for thread_name in self.threads:
            reply = self._process_data(thread_name)
            if reply:
                data = self._to_weewx(thread_name,reply,event.packet['usUnits'])
                # 'dateTime' and 'interval' must not be in data
                if data.get('dateTime'): del data['dateTime']
                if data.get('interval'): del data['interval']
                if __name__ == '__main__' and thread_name=='S10':
                    data['dateTime'] = reply.get('time')
                    data['interval'] = reply.get('interval')[0]
                    data['count'] = reply.get('count')[0]
                # log 
                if self.debug>=3: 
                    logdbg("PACKET %s:%s" % (thread_name,data))
                # update loop packet with device data
                event.packet.update(data)
                # count records received from the device
                self.threads[thread_name]['reply_count'] += reply.get('count',(0,None,None))[0]
        self.almanac(event.packet)
        self.dbm_new_loop_packet(event.packet)
        if has_mqtt and self.mqtt_queue and self.mqtt_thread:
            try:
                record_m = weewx.units.to_std_system(event.packet,weewx.METRICWX)
                topics = dict()
                for ii in self.threads:
                    topic = self.threads[ii]['topic']
                    if topic: topics.update({topic:True})
                obs_list = ('dateTime','usUnits','radiation','maxSolarRad','solarAzimuth','solarAltitude','solarPath')
                x = dict()
                for ii in obs_list:
                    if ii in record_m: x[ii] = record_m[ii]
                for ii in topics:
                    if topics[ii]:
                        self.mqtt_queue.put(
                            (ii,x,'new_loop_packet'),
                            timeout=1.0)
            except Exception:
                pass
            
    def new_archive_record(self, event):
        try:
            val = weewx.units.as_value_tuple(event.record,'outTemp')
            self.last_archive_outTemp = weewx.units.convert(val,'degree_C')[0]
            logdbg("outTemp %s °C" % self.last_archive_outTemp)
        except (LookupError,ArithmeticError,AttributeError):
            pass 
        try:
            val = weewx.units.as_value_tuple(event.record,'pressure')
            self.last_archive_pressure = weewx.units.convert(val,'mbar')[0]
            logdbg("pressure %s mbar" % self.last_archive_pressure)
        except (LookupError,ArithmeticError,AttributeError):
            pass
        for thread_name in self.threads:
            # log error if we did not receive any data from the device
            if self.log_failure and not self.threads[thread_name]['reply_count']:
                logerr("no data received from %s during archive interval" % thread_name)
            # log success to see that we are still receiving data
            if self.log_success and self.threads[thread_name]['reply_count']:
                loginf("%s records received from %s during archive interval" % (self.threads[thread_name]['reply_count'],thread_name))
            # reset counter
            self.threads[thread_name]['reply_count'] = 0
        if has_mqtt and self.mqtt_queue and self.mqtt_thread:
            try:
                record_m = weewx.units.to_std_system(event.record,weewx.METRICWX)
                topics = dict()
                for ii in self.threads:
                    topic = self.threads[ii]['topic']
                    if topic: topics.update({topic:True})
                if len(topics)==1:
                    obs_list = [ii[0] for ii in schema['table']]
                else:
                    obs_list = ('dateTime','interval','usUnits','radiation','maxSolarRad','solarAzimuth','solarAltitude','solarPath')
                x = dict()
                for ii in obs_list:
                    if ii in record_m: x[ii] = record_m[ii]
                for ii in topics:
                    if topics[ii]:
                        self.mqtt_queue.put(
                            (ii,x,'new_archive_record'),
                            timeout=1.0)
                if self.debug>=3:
                    logdbg("RECORD %s" % x)
            except queue.Full:
                if self.log_failure:
                    logerr("could not send archive record to MQTT thread: timeout waiting for queue to become available")
            except (ArithmeticError,ValueError,TypeError,LookupError,AttributeError) as e:
                if self.log_failure:
                    logerr("could not send archive record to MQTT thread: %s" % e)
        self.dbm_new_archive_record(event.record)
        
    def _to_weewx(self, thread_name, reply, usUnits):
        data = {}
        for key in reply:
            if key in ('time','interval','count','sysStatus'):
                pass
            elif key in ('interval','count','sysStatus'):
                data[key] = reply[key]
            else:
                try:
                    val = reply[key]
                    val = weewx.units.convertStd(val, usUnits)[0]
                except (TypeError,ValueError,LookupError,ArithmeticError):
                    val = None
                data[key] = val
        return data
        
    def almanac(self, packet):
        """ calculate solarAzimuth, solarAltitude, solarPath """
        try:
            usUnits = packet['usUnits']
            ts = packet.get('dateTime',time.time())
            alm = weewx.almanac.Almanac(ts,
                                        self.engine.stn_info.latitude_f,
                                        self.engine.stn_info.longitude_f,
                                        self.altitude,
                                        temperature=self.last_archive_outTemp,
                                        pressure=self.last_archive_pressure)
            almsun = alm.sun
            packet['solarAzimuth'] = weewx.units.convertStd((almsun.az,'degree_compass','group_direction'),usUnits)[0]
            packet['solarAltitude'] = weewx.units.convertStd((almsun.alt,'degree_compass','group_direction'),usUnits)[0]
            # In the morning before sunrise adapt the values of sunrise
            # and sunset time according to the local temperature and
            # pressure. After sunrise do not change the values to get
            # continuous values for solarPath
            if not self.sunrise or self.sunrise.raw>ts or alm.sunrise.raw>(self.sunrise.raw+43200):
                self.sunrise = alm.sunrise
                self.sunset = alm.sunset
                #loginf("sunrise sunset %s %s" % (self.sunrise,self.sunset))
            # If sunrise and sunset time is available, calculate solarPath
            # Solar path is here defined as the percentage of the time
            # elapsed between sunrise and sunset.
            if self.sunrise and self.sunset:
                try:
                    if ts>=self.sunrise.raw and ts<=self.sunset.raw:
                        packet['solarPath'] = weewx.units.convertStd(((ts-self.sunrise.raw)/(self.sunset.raw-self.sunrise.raw)*100.0,'percent','group_percent'),usUnits)[0]
                    else:
                        packet['solarPath'] = None
                    #loginf("solarPath %s" % packet['solarPath'])
                except (ArithmeticError,AttributeError) as e:
                    #logerr(e)
                    pass
        except Exception as e:
            # report the error at most once every 5 minutes
            if time.time()>=self.last_almanac_error+300:
                logerr("almanac error: %s" % e)
                self.last_almanac_error = time.time()
        
    def dbm_init(self, engine, binding, binding_found):
        self.accumulator = None
        self.old_accumulator = None
        self.dbm = None
        if not binding: 
            loginf("no database storage configured")
            return
        if not binding_found: 
            logerr("binding '%s' not found in weewx.conf" % binding)
            return
        self.dbm = engine.db_binder.get_manager(data_binding=binding,
                                                     initialize=True)
        if self.dbm:
            loginf("Using binding '%s' to database '%s'" % (binding,self.dbm.database_name))
            # Back fill the daily summaries.
            _nrecs, _ndays = self.dbm.backfill_day_summary()
        else:
            loginf("no database access")
    
    def dbm_close(self):
        if self.dbm:
            self.dbm.close()
        
    def dbm_new_loop_packet(self, packet):
        """ Copyright (C) Tom Keffer """
        # Do we have an accumulator at all? If not, create one:
        if not self.accumulator:
            self.accumulator = self._new_accumulator(packet['dateTime'])

        # Try adding the LOOP packet to the existing accumulator. If the
        # timestamp is outside the timespan of the accumulator, an exception
        # will be thrown:
        try:
            self.accumulator.addRecord(packet, add_hilo=True)
        except weewx.accum.OutOfSpan:
            # Shuffle accumulators:
            (self.old_accumulator, self.accumulator) = \
                (self.accumulator, self._new_accumulator(packet['dateTime']))
            # Try again:
            self.accumulator.addRecord(packet, add_hilo=True)
        
    def dbm_new_archive_record(self, record):
        if self.dbm:
            self.dbm.addRecord(record,
                           accumulator=self.old_accumulator,
                           log_success=self.log_success,
                           log_failure=self.log_failure)
        
    def _new_accumulator(self, timestamp):
        """ Copyright (C) Tom Keffer """
        start_ts = weeutil.weeutil.startOfInterval(timestamp,
                                                   self.archive_interval)
        end_ts = start_ts + self.archive_interval

        # Instantiate a new accumulator
        new_accumulator = weewx.accum.Accum(weeutil.weeutil.TimeSpan(start_ts, end_ts))
        return new_accumulator

        
##############################################################################
#   prep_services: augment units.py                                          #
##############################################################################

class E3dcUnits(StdService):

    def __init__(self, engine, config_dict):
        super(E3dcUnits,self).__init__(engine, config_dict)
        # unit kilowatt
        weewx.units.default_unit_label_dict.setdefault('kilowatt',u" kW")
        weewx.units.default_unit_format_dict.setdefault('kilowatt',"%.1f") 
        # group_frequency and unit hertz
        weewx.units.default_unit_label_dict.setdefault('hertz',u" Hz")
        weewx.units.default_unit_format_dict.setdefault('hertz',"%.3f")
        if __name__ != '__main__':
            for ii in weewx.units.std_groups:
                weewx.units.std_groups[ii].setdefault('group_frequency','hertz')
        # augment groups dict by the PV observation types
        self._augment_obs_group_dict()
        
    def _augment_obs_group_dict(self):
        log_dict = {}
        _accum = {}
        for ii in E3DC_OBS:
            _obs_conf = E3DC_OBS[ii]
            if _obs_conf and _obs_conf[2] is not None:
                weewx_key = _obs_conf[0]
                weewx.units.obs_group_dict[weewx_key] = _obs_conf[2]
                log_dict[weewx_key] = _obs_conf[2]
                if _obs_conf[3]:
                    _accum[weewx_key] = _obs_conf[3]
        for ii in MYPV_OBS:
            _obs_conf = MYPV_OBS[ii]
            if _obs_conf and _obs_conf[2] is not None:
                weewx_key = _obs_conf[0]
                weewx.units.obs_group_dict[weewx_key] = _obs_conf[2]
                log_dict[weewx_key] = _obs_conf[2]
        if 'ephem' in sys.modules:
            weewx.units.obs_group_dict['solarAzimuth'] = 'group_direction'
            weewx.units.obs_group_dict['solarAltitude'] = 'group_direction'
            weewx.units.obs_group_dict['solarPath'] = 'group_percent'
            _accum['solarAzimuth'] = ACCUM_LAST
            _accum['solarAltitude'] = ACCUM_LAST
            _accum['solarPath'] = ACCUM_LAST
        if _accum:
            loginf("accumulator dict %s" % _accum)
            weewx.accum.accum_dict.maps.append(_accum)
        loginf("observation group dict %s" % log_dict)


if __name__ == '__main__':
    CONF = configobj.ConfigObj("photovoltaics.conf")
    print('################################################################')
    print(schema)
    print('################################################################')
    engine = Engine()
    E3dcUnits(engine,CONF)
    srv = E3dcService(engine,CONF)
    try:
        while True:
            evt = Event()
            evt.packet['dateTime'] = time.time()
            srv.new_loop_packet(evt)
            print(evt.packet)
            print('********')
            time.sleep(3)
    finally:
        srv.shutDown()
        
    
