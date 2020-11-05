# -*- coding: utf-8 -*-
# © 2020 Reison Torres <reison.torres@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def _picking_done(self, picking_type=None):
        picking = self.filtered(lambda rec: rec.state in ['assigned'] and rec.picking_type_code == picking_type)
        # finalizar flujo de entrega
        if picking:
            picking.force_assign()
            picking.do_transfer()
        return True
