# installer PV
# Copyright 2021, 2023 Johanna Roedenbeck
# Distributed under the terms of the GNU Public License (GPLv3)

from weecfg.extension import ExtensionInstaller

def loader():
    return PVInstaller()

class PVInstaller(ExtensionInstaller):
    def __init__(self):
        super(PVInstaller, self).__init__(
            version="0.7",
            name='Photovoltaics',
            description='Service to retrieve data from PV system E3/DC',
            author="Johanna Roedenbeck",
            author_email="",
            prep_services='user.photovoltaics.E3dcUnits',
            data_services='user.photovoltaics.E3dcService',
            config={
              'E3DC':{
                  'S10EPRO':{
                      'protocol':'RSCP',
                      'host':'replace_me',
                      'username':'replace_me',
                      'password':'replace_me',
                      'api_key':'replace_me',
                      'query_interval':' 1 # optional',
                      '#mqtt_topic':'e3dc/weewx # normally not required'},
                  'ACTHOR':{
                      'protocol':'MyPV',
                      'host':'replace_me',
                      '#mqtt_topic:':'acthor/weewx # normally not required'},
                  'MQTT':{
                      'protocol':'MQTT',
                      'enable':True,
                      'topic':'e3dc/weewx'}
                  }
              },
              'DataBindings': {
                  'pv_binding': {
                      'database':'pv_sqlite',
                      'table_name':'archive',
                      'manager':'weewx.manager.DaySummaryManager',
                      'schema':'user.photovoltaics.schema'
                  }
              },
              'Databases': {
                  'pv_sqlite':{
                      'database_name':'photovoltaics.sdb',
                      'database_type':'SQLite'
                  }
              }
            },
            files=[('bin/user', ['bin/user/photovoltaics.py',]),]
            )
      
