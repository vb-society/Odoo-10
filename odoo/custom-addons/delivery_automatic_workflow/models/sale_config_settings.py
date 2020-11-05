# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    def _default_delivery_payment_acquirer(self):

        return self.env['payment.acquirer']\
                   .search([('provider', 'in', ['epayco', 'delivery'])]).ids

    delivery_payment_acquirer_ids = fields.Many2many(
        'payment.acquirer',
        string='Payment Acquirer to delivery automatic',
        default=_default_delivery_payment_acquirer)

    @api.multi
    def set_delivery_payment_acquirer_ids_defaults(self):
        return self.env['ir.values'].sudo().set_default(
                'sale.config.settings',
                'delivery_payment_acquirer_ids',
                self.delivery_payment_acquirer_ids.mapped('id'))
