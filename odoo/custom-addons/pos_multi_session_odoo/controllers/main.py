# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import json
import logging
import werkzeug.utils

from odoo import exceptions
from odoo.http import Controller, request, route
from odoo.addons.bus.models.bus import dispatch

from odoo import http
from odoo.addons.bus.controllers.main import BusController

_logger = logging.getLogger(__name__)


'''class BusController(Controller):
    @route('/longpolling/send', type="json", auth="public")
    def send(self, channel, message):
        if not isinstance(channel, basestring):
            raise Exception("bus.Bus only string channels are allowed.")
        return request.env['bus.bus'].sendone(channel, message)

    # override to add channels
    def _poll(self, dbname, channels, last, options):
        # update the user presence
        if request.session.uid and 'bus_inactivity' in options:
            request.env['bus.presence'].update(options.get('bus_inactivity'))
        request.cr.close()
        request._cr = None
        return dispatch.poll(dbname, channels, last, options)

    @route('/longpolling/poll', type="json", auth="public")
    def poll(self, channels, last, options=None):
        if options is None:
            options = {}
        if not dispatch:
            raise Exception("bus.Bus unavailable")
        if [c for c in channels if not isinstance(c, basestring)]:
            raise Exception("bus.Bus only string channels are allowed.")
        if request.registry.in_test_mode():
            raise exceptions.UserError("bus.Bus not available in test mode")
        return self._poll(request.db, channels, last, options)'''
        
class PosMultiSessionController(BusController):

    def _poll(self, dbname, channels, last, options):
        #print "pollllllllllllllllllllllllllllllllllllllllllllllll",dbname, channels
        # update the user presence
        if request.session.uid:
            channels.append((request.db, 'pos.multi.session', request.uid))
            #print "chanelsssssssssssssssssssssssssssssssssssssssssss",channels
        return super(PosMultiSessionController, self)._poll(dbname, channels, last, options)


    @route('/pos_sync_multi_session/sync', type="json", auth="public")
    def PosSyncMultiSession(self, pos_multi_session_id, message):
        #print "session iddddddddddddddddddddddddddddddddddddddddd",pos_multi_session_id, type(pos_multi_session_id), message
        multi_session = request.env["pos.multi.session"]
        res = multi_session.browse(pos_multi_session_id).sync_multi_session(message)
        #print "/pod/web calllledddddddddddddddddddddddddddddddddddddddddd",res
        return res
        
                
    @http.route('/pod/web', type='http', auth='user')
    def pod_web(self, debug=False, **k):
        # if user not logged in, log him in
        #print "/pod/web calllledddddddddddddddddddddddddddddddddddddddddd"
        context = {
            'session_info': json.dumps(request.env['ir.http'].session_info())
        }
        #print "contextttttttttttttttttttttttttttttttttttttttttttttttt",context
        return request.render('point_of_delivery.index', qcontext=context)

    @http.route('/pod/incoming', type='http', auth='user')
    def pod_incoming(self, debug=False, **k):
        # if user not logged in, log him in
        #print "/pod/incoming calllledddddddddddddddddddddddddddddddddddddddddd"
        context = {
            'session_info': json.dumps(request.env['ir.http'].session_info())
        }
        #print "index_incoming contextttttttttttttttttttttttttttttttttttttttttttttttt",context
        return request.render('point_of_delivery.index_incoming', qcontext=context)        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
