# -*- coding: utf-8 -*-
# © 2020 Reison Torres <reison.torres@gmail.com>

import json
from odoo import models, fields, api, _

class PosOrder(models.Model):
    _inherit = "pos.order"

    delivery_state = fields.Selection(
        [('waiting', 'Waiting Another Operation'), ('kitchen', 'On kitchen'), ('delivery', 'To delivery'), ('done', 'Done')],
        'Delivery status', readonly=True, copy=False, default='waiting')

    @api.multi
    def _update_delivery_state(self):
        d_state = self.delivery_state
        data = {}
        if d_state == "waiting":
            data.update(delivery_state='kitchen')
        elif d_state == "kitchen":
            data.update(delivery_state='delivery')
        elif d_state == "delivery":
            data.update(delivery_state='done')
        
        if d_state != 'done':
            self.write(data)
        
        return True