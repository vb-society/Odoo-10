# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


CHANNEL_NM_SYNCH = "pos.order.synch"
CHANNEL_NM_SYNCH_STATUS = "pos.order.synch.status"


class PosOrder(models.Model):
    _inherit = 'pos.order'

    priority = fields.Selection(
            [('low', 'Low'), ('normal', 'Normal'), ('high', 'High')],
            string="Priority", default="normal")

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({'priority': ui_order['priority']})
        return res


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_is_kitchen = fields.Boolean('Default Kitchen View', help="Set as default screen.")
    iface_btn_kitchen = fields.Boolean('Show Kitchen Button', help="Allow to show kitchen screen.")
    iface_btn_priority = fields.Boolean('Order Priority')
    categ_ids = fields.Many2many('pos.category', string='Category')


class Category(models.Model):
    _inherit = 'pos.category'

    color = fields.Char('Color')
