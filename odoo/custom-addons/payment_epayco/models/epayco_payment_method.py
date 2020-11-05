# -*- coding: utf-8 -*-

from odoo import fields, models, api,_


class EpaycoPaymentMethod(models.Model):
    _name = 'epayco.payment.method'

    code = fields.Char(
        string='Code payment method')
    name = fields.Char()
    active = fields.Boolean(default=True)
    payment_acquirer_id = fields.Many2many('payment.acquirer', string='Payment Acquirer', help='Only valid for ePayco.')

    _sql_constraints = [(
        'code_unique',
        'unique(code)',
        _('Code already exists for a payment method.'))]

    @api.model
    def _get_method_disable(self):
        """Returns Payment method disable."""
        pm_all = self.env['epayco.payment.method'].search([]).mapped('code')
        pm_available = self.mapped('code')
        disable = filter(lambda x: x not in pm_available, pm_all)

        return disable
