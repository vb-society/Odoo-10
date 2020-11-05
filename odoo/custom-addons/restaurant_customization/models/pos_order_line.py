# -*- coding: utf-8 -*-
from odoo import api, models


class PosOrderLine(models.Model):

    _inherit = "pos.order.line"

    @api.model
    def create(self, vals):
        res = super(PosOrderLine, self).create(vals)
        bus = self.env['bus.bus']
        bus.sendone('auto_refresh', self._name)
        return res
