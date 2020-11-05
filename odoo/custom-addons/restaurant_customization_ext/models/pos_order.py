# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import psycopg2
from functools import partial
from odoo.tools import float_is_zero
import logging
_logger = logging.getLogger(__name__)


order_status = {
    'in_queue': 'Queue',
    'in_progress': 'In Progress',
    'is_done': 'Done',
    'cancel': 'Cancel'
}


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def create_from_ui(self, orders, is_kitchen=False):
        posorder = super(PosOrder, self).create_from_ui(orders, is_kitchen)
        if is_kitchen:
            channel = '["%s","%s","%s"]' % (self._cr.dbname, 'orderscreen.auto_refresh', 'kitchen')
            message = {"updated_orders": posorder[0]}
            if len(posorder[0]) > 0 or any(v for k, v in posorder[2].iteritems()):
                bus = self.env['bus.bus']
                bus.sendone(channel, message)

        return posorder
