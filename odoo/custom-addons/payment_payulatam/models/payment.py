# -*- coding: utf-'8' "-*-"

import math
import base64
try:
    import simplejson as json
except ImportError:
    import json
import logging
import hashlib
import urlparse
import werkzeug.urls
import urllib2
import datetime
import requests
import re

from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo import osv, fields, models, api
from odoo.tools.float_utils import float_compare
from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)
from dateutil.tz import *

dateformat="%Y-%m-%dT%H:%M:%S."
dateformatmilis="%f"
dateformatutc="%z"

from odoo.addons.payment_mercadopago.mercadopago import mercadopago


def _float_round(num, places=0, direction=math.floor):
    return direction(num * (10**places)) / float(10**places)

class PaymentAcquirerPayulatam(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('payulatam', 'PayULatam')])

    payulatam_merchant_id = fields.Char('Merchant ID',
                    required_if_provider='payulatam',
                    size=256,
                    help='The Merchant ID is the identifying number of your business in the PayU Latam system.')

    payulatam_api_key = fields.Char('API Key', 
                    required_if_provider='payulatam',
                    size=256,
                    help='The ApiKey is account in PayU Latam')

    payulatam_account_id = fields.Char('Account ID', 
                    required_if_provider='payulatam',
                    size=256,
                    help='User account identifier for each country associated with the business, when sending it, only the means of payment belonging to that country are displayed.')

    def _get_payulatam_urls(self, environment):
        """ PayULatam URLS """
        if environment == 'prod':
            return {'payulatam_form_url': 'https://checkout.payulatam.com/ppp-web-gateway-payu'}
        else:
            return {'payulatam_form_url': 'https://sandbox.checkout.payulatam.com/ppp-web-gateway-payu'}

    def _get_providers(self, context=None):

        providers = super(PaymentAcquirerPayulatam, self)._get_providers(cr, uid, context=context)
        providers.append(['payulatam', 'PayULatam'])

        print "_get_providers: ", providers

        return providers

    def _banker_round(self, value):
        """Round half to even"""
        new_value = '0.00'
        parte_entera, parte_decimal = str(value).split('.')

        if len(parte_decimal) > 0:
            first_dig = int(parte_decimal[0])
            second_dig = int(parte_decimal[1])
            if first_dig % 2 == 0 and second_dig == 5:
                # redondear menor valor
                new_value = _float_round(float(value), 1)
            elif first_dig % 2 != 0 and second_dig == 5:
                # redondear mayor valor
                new_value = _float_round(float(value), 1, math.ceil)
            else:
                new_value = _float_round(float(value), 1, round)

        return new_value

    def _second_dec_with_zero(self, value):
        new_value = 0.0
        parte_entera, parte_decimal = str(value).split('.')

        second_dig = int(parte_decimal[1])
        if second_dig == 0:
            # solo un decimal
            new_value = (parte_entera + '.' + first_dig)
        else:
            # dos decimal
            new_value = value
        
        return new_value

    def _payulatam_generate_sign(self, inout, values):
        """ Generate the shasign for incoming or outgoing communications.
        :param self: the self browse record. It should have a shakey in shakey out
        :param string inout: 'in' (odoo contacting payulatam) or 'out' (payulatam
                             contacting odoo).
        :param dict values: transaction values

        :return string: shasign
        """
        if inout not in ('in', 'out'):
            raise Exception("Type must be 'in' or 'out'")

        if "tx_value" in values:
            notification_page = False

            if "notification_page" in values:
                notification_page = values.get('notification_page')
         
            if notification_page:
                if notification_page == "response":
                    values["new_value"] = self._banker_round(values.get("tx_value"))
                elif notification_page == "confirmation":
                    values["new_value"] = self._second_dec_with_zero(values.get("tx_value"))

        if inout == 'in':
            keys = "~merchantId~referenceCode~amount~currency".split('~')
            sign = ''.join('%s~' % (values.get(k) or '') for k in keys)
            sign = self.payulatam_api_key + sign
        else:
            keys = "~merchantId~referenceCode~new_value~currency~transactionState".split('~')
            sign = ''.join('%s~' % (values.get(k) or '') for k in keys)
            sign = self.payulatam_api_key + sign

        sign = sign.rstrip("~")
        shasign = hashlib.md5(sign.rstrip("~")).hexdigest()
        return shasign

    def payulatam_dateformat(self, date):
        stf = date.strftime(dateformat)
        stf_utc_milis = date.strftime(dateformatmilis)
        stf_utc_milis = stf_utc_milis[0]+stf_utc_milis[1]+stf_utc_milis[2]
        stf_utc_zone = date.strftime(dateformatutc)
        stf_utc_zone = stf_utc_zone[0]+stf_utc_zone[1]+stf_utc_zone[2]+":"+stf_utc_zone[3]+stf_utc_zone[4]
        stf_utc = stf+stf_utc_milis+stf_utc_zone
        return stf_utc

    @api.multi
    def payulatam_form_generate_values(self, values):
        
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        acquirer = self

        saleorder_obj = self.env['sale.order']
        sorder_s = saleorder_obj.search([('name', '=', values["reference"])])

        payulatam_values = dict(values,
                                merchantId=self.payulatam_merchant_id,
                                accountId=self.payulatam_account_id,
                                description="Orden Ecommerce " + values['reference'],
                                referenceCode=values['reference'],
                                amount='{0:.2f}'.format(values['amount']), # '{0:.2f}'.format(values['amount']),
                                tax='{0:.2f}'.format(sorder_s.amount_tax) if sorder_s.amount_tax != 0.0 else '0',
                                taxReturnBase='{0:.2f}'.format(sorder_s.amount_untaxed) if sorder_s.amount_tax != 0.0 else '0',
                                currency=(values['currency'] and values['currency'].name or ''),
                                buyerFullName=values.get('partner_name'),
                                buyerEmail=values.get('partner_email'),
                                shippingAddress=values.get('partner_city'),
                                shippingCity=values.get('partner_address'),
                                shippingCountry=values['partner_country'].name,
                                telephone=values.get('partner_phone')
                                )

        payulatam_values['signature'] = self._payulatam_generate_sign('in', payulatam_values)
        payulatam_values['test'] = self.environment == 'prod' and '0' or '1'
        payulatam_values['responseUrl'] = '%s' % urlparse.urljoin(base_url, '/payment/payulatam_process/response')
        payulatam_values['confirmationUrl'] = '%s' % urlparse.urljoin(base_url, '/payment/payulatam_process/confirmation')
        
        print "payulatam_form_generate_values: payulatam_values: ", payulatam_values

        return payulatam_values

    @api.multi
    def payulatam_get_form_action_url(self):
        return self._get_payulatam_urls(self.environment)['payulatam_form_url']


class PaymentTransactionPayulatam(models.Model):
    _inherit = 'payment.transaction'

    payulatam_txn_id = fields.Char('Transaction ID')
    payulatam_txn_type = fields.Char('Transaction type')


    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------
    @api.model
    def _payulatam_form_get_tx_from_data(self, data, context=None):

        reference = data.get('referenceCode')
        payu_tx_id = data.get('reference_pol')
        shasign = data.get('signature')
        if not reference or not payu_tx_id or not shasign:
            error_msg = 'PayUlatam: received data with missing reference (%s) or payu_tx_id (%s) or shasign (%s)' % (reference,payu_tx_id,shasign)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        transaction = self.env['payment.transaction'].search([('reference', '=', reference)])
        if not transaction or len(transaction) > 1:
            error_msg = 'PayUlatam: received data for reference %s' % (reference)
            if not transaction:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        #verify shasign
        shasign_check = transaction.acquirer_id._payulatam_generate_sign('out', data)
        if shasign_check.upper() != shasign.upper():
            raise ValidationError(_('PayUlatam: invalid shasign, received %s, computed %s, for data %s') % (shasign, shasign_check, data))

        return transaction

    @api.multi
    def _payulatam_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        _logger.warning('Received a notification from PayUlatam.')

        if self.acquirer_reference and data.get('reference_pol') != self.acquirer_reference:
            invalid_parameters.append(('Transaction Id', data.get('reference_pol'), self.acquirer_reference))
        
        #check what is buyed
        if float_compare(float(data.get('tx_value', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('Amount', data.get('tx_value'), '%.2f' % self.amount))
        
        return invalid_parameters

    #From http://developers.payulatam.com/es/web_checkout/integration.html
    #
    #approved 	El pago fue aprobado y acreditado.
    #pending 	Transacción en validación.
    #declined  	Transacción rechazada.
    #error 	    No fue posible establecer comunicación con la entidad financiera.
    #called by Trans.form_feedback(...) > %s_form_validate(...)
    @api.multi
    def _payulatam_form_validate(self, data):

        status = data.get('transactionState')
        data = {
            'acquirer_reference': data.get('reference_pol'),
            'payulatam_txn_id': data.get('transactionId'),
            'payulatam_txn_type': data.get('paymentMethodType')
        }
        if status == '4':  # (approved)
            _logger.info('Validated PayUlatam payment for tx %s: set as done' % (self.reference))
            data.update(state='done', date_validate=data.get('processingDate', fields.datetime.now()))
            return self.write(data)
        elif status == '7':  # (pending)
            _logger.info('Received notification for PayUlatam payment %s: set as pending' % (self.reference))
            data.update(state='pending', date_validate=data.get('processingDate', fields.datetime.now()))
            return self.write(data)
        elif status == '6':  # (declined)
            _logger.info('Received notification for PayUlatam payment %s: set as cancelled' % (self.reference))
            data.update(state='cancel',  date_validate=data.get('processingDate', fields.datetime.now()))
            return self.write(data)
        else:  # 104(error) or 5(expired) or other
            error = 'Received unrecognized status for PayUlatam payment %s: %s, set as error' % (self.reference, status)
            _logger.info(error)
            data.update(state='error',  date_validate=data.get('processingDate', fields.datetime.now()), state_message=error)
            return self.write(data)
