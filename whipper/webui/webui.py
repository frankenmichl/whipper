import pyudev
import os

import cdio
import importlib.util
import os
import glob
import logging
import os
import sys
import pkg_resources
import musicbrainzngs
import site
import whipper
from distutils.sysconfig import get_python_lib
from whipper.command import cd, offset, drive, image, accurip, mblookup
from whipper.command.main import Whipper
from whipper.command.basecommand import BaseCommand
from whipper.common import common, directory, config
from whipper.extern.task import task
from whipper.program.utils import eject_device

import whipper
from whipper.command.cd import Info

from flask import Flask
from flask_table import Table, Col

from io import StringIO
import sys


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout




app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"

@app.route('/discinfo')
def discinfo():
    return "Disc Information"

def wait_for_disc(cddevice):
    context = pyudev.Context()
    devices = context.list_devices()

    cddrives = devices.match_subsystem('block').match_property('DEVNAME', cddevice)
    for drive in cddrives:
        print ("Found CD drive: ", drive)
    

    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('block')
    for device in iter(monitor.poll, None):
        if device.action == 'change':
            print("drive changed")

#wait_for_disc("/dev/sr0")

class DiscTable(Table):
    name = Col('Disc Information')
    description = Col('')

class ReleaseTable(Table):
    name = Col('Release Information')
    description = Col('')

def update_discinfo():
    with Capturing() as output:
        cmd = Whipper(["cd", "info"], "info", None)
        ret = cmd.do()
    count = 0
    
    cddb_id = ""
    mb_id = ""
    mblookup = ""
    duration = ""
    tracks = ""
    releases = []
    
    for i in range(len(output)):
        line = output[i].strip()
        if line == "" or line == "Matching releases":
            continue
        if line.startswith("Reading"):
            continue
        if line.startswith("Track"):
            continue
    
        if line.startswith("CDDB disc id"):
            cddb_id = line.split(':')[1].strip()
        if line.startswith("MusicBrainz disc id"):
            mb_id = line.strip().split(" ")[3]
        if line.startswith("MusicBrainz lookup URL"):
            mblookup = line.split(" ")[-1]
        if line.startswith("Disc duration"):
            tmp = line.split(",")
            duration = tmp[0].split(":",1)[-1].strip()
            tracks = tmp[-1].strip().split(" ")[0]
    
        if line.startswith("Artist"):
            info = {}
    
            for j in range(0,9):
                l = output[i+j].strip()
                if l == "": 
                    break
                key, value = l.split(':', 1)
                key = key.strip()
                value = value.strip()
                info[key] = value

            
            rel = [dict(name='Artist',   description=info['Artist']),
                   dict(name='Title',    description=info['Title']),
                   dict(name='Duration', description=info['Duration']),
                   dict(name='URL',      description='<a href=' + info['URL'] + '>' + info['URL'] + '</a>'),
                   dict(name='Release',  description=info['Release']),
                   dict(name='Type',     description=info['Type']),
                   dict(name='Barcode',  description=info['Barcode']),
                   dict(name='Country',  description=info['Country']),
                   dict(name='Cat no',   description=info['Cat no'])]

            releases.append(ReleaseTable(rel))

    discinfo = [dict(name='CDDB ID',                description=cddb_id),
                dict(name='MusicBrainz ID',         description=mb_id),
                dict(name='MusicBrainz Lookup URL', description=mblookup),
                dict(name='Duration',               description=duration),
                dict(name='# Tracks',               description=tracks)]
    disc_table = DiscTable(discinfo)

    html = "<p>" + disc_table.__html__() + "</p>"
    for r in releases:
        html = html + "<p>" + r.__html__() + "</p>"

    print(html)

update_discinfo()
