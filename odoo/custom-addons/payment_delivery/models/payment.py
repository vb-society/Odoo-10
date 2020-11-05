# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare

import logging
import pprint

_logger = logging.getLogger(__name__)


class DeliveryPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('delivery', 'On Delivery')])

    def delivery_get_form_action_url(self):
        return '/payment/delivery/feedback'

    @api.multi
    def delivery_form_generate_values(self, values):
        tx_values = dict(values,
                         state='pending')

        print "delivery_form_generate_values: tx_values: ", tx_values

        return tx_values


class DeliveryPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _delivery_form_get_tx_from_data(self, data):
        reference, amount, currency_name = data.get('reference'), data.get('amount'), data.get('currency_name')
        tx = self.search([('reference', '=', reference)])

        if not tx or len(tx) > 1:
            error_msg = _('received data for reference %s') % (pprint.pformat(reference))
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _delivery_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), self.currency_id.name))

        return invalid_parameters

    def _delivery_form_validate(self, data):
        status = data.get('state')
        if status == 'done':
            _logger.info('Validated payment on delivery for tx %s: set as done' % (self.reference))
            data.update(state='done', date_validate=data.get('processingDate', fields.datetime.now()))
            return self.write(data)
        elif status == 'pending':
            _logger.info('Received notification for payment on delivery %s: set as pending' % (self.reference))
            data.update(state='pending', date_validate=data.get('processingDate', fields.datetime.now()))
            return self.write(data)
        elif status == 'cancel':
            _logger.info('Received notification for payment on delivery %s: set as cancelled' % (self.reference))
            data.update(state='cancel',  date_validate=data.get('processingDate', fields.datetime.now()))
            return self.write(data)
        else:
            error = 'Received unrecognized status for payment on delivery %s: %s, set as error' % (self.reference, status)
            _logger.info(error)
            data.update(state='error',  date_validate=data.get('processingDate', fields.datetime.now()), state_message=error)
            return self.write(data)

    def _confirm_so(self, acquirer_name=False):
        """ Override to Auto-confirm SO if necessary, and if payment acquirer
        is delivery. """
        if acquirer_name == 'delivery':
            for tx in self:
                # check tx state, confirm the potential SO
                if tx.sale_order_id and tx.sale_order_id.state in ['draft', 'sent', 'sale']:
                    # verify SO/TX match, excluding tx.fees which are currently not included in SO
                    amount_matches = float_compare(tx.amount, tx.sale_order_id.amount_total, 2) == 0
                    if amount_matches:
                        if not acquirer_name:
                            acquirer_name = tx.sale_order_id.payment_acquirer_id.provider or 'unknown'
                        if tx.state == 'pending' and tx.acquirer_id.auto_confirm in ['confirm_so', 'generate_and_pay_invoice']:
                            _logger.info('<%s> transaction authorized, auto-confirming order %s (ID %s)', acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)
                            tx.sale_order_id.with_context(send_email=True).action_confirm()
                        if tx.state == 'done' and tx.sale_order_id.invoice_status == 'to invoice'and tx.acquirer_id.auto_confirm in ['generate_and_pay_invoice']:
                            _logger.info('<%s> transaction completed, generate and pay invoice for order %s (ID %s)', acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)
                            tx._generate_and_pay_invoice(tx, acquirer_name)
                        elif tx.state not in ['cancel', 'error'] and tx.sale_order_id.state == 'draft':
                            _logger.info('<%s> transaction pending/to confirm manually, sending quote email for order %s (ID %s)', acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)
                            tx.sale_order_id.force_quotation_send()
                    else:
                        _logger.warning('<%s> transaction MISMATCH for order %s (ID %s)', acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)
        else:
            super(DeliveryPaymentTransaction, self)._confirm_so(acquirer_name)

