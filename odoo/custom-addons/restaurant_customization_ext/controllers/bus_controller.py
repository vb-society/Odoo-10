# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from odoo.addons.bus.controllers.main import BusController

CHANNEL_NAME = 'orderscreen.auto_refresh'

class Controller(BusController):
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            registry, cr, uid, context = request.registry, request.cr, request.session.uid, request.context
            new_channel = '["%s","%s","%s"]' % (request.db, CHANNEL_NAME, 'kitchen')
            channels.append(new_channel)
        return super(Controller, self)._poll(dbname, channels, last, options)