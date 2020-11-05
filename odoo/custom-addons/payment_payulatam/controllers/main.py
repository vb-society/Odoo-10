# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PayuLatamController(http.Controller):

    def _get_tx_from_data(self, data):

        tx_value = dict(data)

        if "notification_page" in data:
            if data.get("notification_page") == "response":
                tx_value = dict(data,
                                tx_value=data.pop('TX_VALUE'),
                                paymentMethodType=data.pop('polPaymentMethodType')
                                )
            elif data.get("notification_page") == "confirmation":
                tx_value = dict(data,

                                merchantId=data.pop('merchant_id'),
                                referenceCode=data.pop('reference_sale'),
                                tx_value=data.pop('value'),
                                transactionState=data.pop('state_pol'),
                                signature=data.pop('sign'),
                                paymentMethodType=data.pop('payment_method_type'),
                                processingDate=data.pop('transaction_date'),
                                transactionId=data.pop('transaction_id')
                                )
        return tx_value

    @http.route('/payment/payulatam_process/response', type='http', auth="public", website=True)
    def process_response(self, **params):
        """ PayUlatam."""
        _logger.info(
            'PayUlatam: entering form_feedback with get data %s', pprint.pformat(params))
        transaction_reference = None
        if params:
            params["notification_page"] = "response"
            transaction_reference = params.get('referenceCode')
            request.env['payment.transaction'].sudo().form_feedback(self._get_tx_from_data(params), 'payulatam')
            
        return_url = self._payment_validate(transaction_reference)
        
        return request.redirect(return_url)
    
    @http.route(['/payment/payulatam_process/confirmation'], type='http', auth='public')
    def process_confirmation(self, **post):
        """ PayUlatam."""
        _logger.info(
            'PayUlatam: entering form_feedback with post data %s', pprint.pformat(post))
        if post:
            post["notification_page"] = "confirmation"
            request.env['payment.transaction'].sudo().form_feedback(self._get_tx_from_data(post), 'payulatam')
            
        return http.Response(status=200)
    
    def _payment_validate(self, reference=None):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        shop_url = '/shop'
        if reference is None:
            tx = request.website.sale_get_transaction()
            order = request.website.sale_get_order()
        else:
            tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
            order = tx.sale_order_id  # request.env['sale.order'].sudo().search([('reference', '=', reference)])
            assert order.id == request.session.get('sale_last_order_id')

        if not order or (order.amount_total and not tx):
            return shop_url

        if tx and tx.state == 'cancel':
            # cancel the quotation
            order.action_cancel()

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return shop_url

        return '/shop/confirmation'
