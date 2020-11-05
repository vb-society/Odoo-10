# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def force_invoice_sent(self):
        for invoice in self:
            email_act = invoice.action_invoice_sent()
            if email_act and email_act.get('context'):
                email_ctx = email_act['context']
                email_ctx.update(default_email_from=invoice.company_id.email)
                invoice.with_context(email_ctx).message_post_with_template(email_ctx.get('default_template_id'))
        return True

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        if self.filtered(lambda inv: inv.state == 'paid'):
            if self.env.context.get('send_email'):
                self.force_invoice_sent()
        return res
