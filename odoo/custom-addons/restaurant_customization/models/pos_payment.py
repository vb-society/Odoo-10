# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.exceptions import UserError


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    @api.multi
    def check(self):
        """Check the order:
        if the order is not paid: continue payment,
        if the order is paid print ticket.
        """
        self.ensure_one()
        order = self.env['pos.order'].browse(self.env.context.get(
            'active_id', False))
        if not order.partner_id:
            raise UserError(_('Customer is not defined.'))
        if order.order_type == 'delivery':
            if not order.delivery_boy:
                raise UserError(_('Delivery Boy is not defined.'))
        if self.amount < order.amount_total:
            if self.amount > 0.0:
                raise UserError(_('You can not do partial payments'))
        amount = order.amount_total - order.amount_paid
        data = self.read()[0]
        ''' this is probably a problem of osv_memory as it's not
            compatible with normal OSV's
        '''
        data['journal'] = data['journal_id'][0]
        if amount != 0.0:
            order.add_payment(data)
            order.backend_payment = True
        if order.test_paid():
            order.action_pos_order_paid()
            order.backend_payment = True
            return {'type': 'ir.actions.act_window_close'}
        return self.launch_payment()
