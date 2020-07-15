# -*- coding: utf-'8' "-*-"

import base64
try:
    import simplejson as json
except ImportError:
    import json
import logging
import urlparse
import werkzeug.urls
import urllib2
import datetime
import requests
import re

from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_mercadopago.controllers.main import MercadoPagoController
from odoo import osv, fields, models, api
from odoo.tools.float_utils import float_compare
from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)
from dateutil.tz import *

dateformat="%Y-%m-%dT%H:%M:%S."
dateformatmilis="%f"
dateformatutc="%z"

from odoo.addons.payment_mercadopago.mercadopago import mercadopago

class AcquirerMercadopago(models.Model):
    _inherit = 'payment.acquirer'

    def _get_mercadopago_urls(self, environment):
        """ MercadoPago URLS """
        if environment == 'prod':
            return {
                #https://www.mercadopago.com/mla/checkout/pay?pref_id=153438434-6eb25e49-1bb8-4553-95b2-36033be216ad
                #'mercadopago_form_url': 'https://www.paypal.com/cgi-bin/webscr',
                'mercadopago_form_url': 'https://www.mercadopago.com/mla/checkout/pay',
                'mercadopago_rest_url': 'https://api.mercadolibre.com/oauth/token',
            }
        else:
            return {
                #'mercadopago_form_url': 'https://www.sandbox.paypal.com/cgi-bin/webscr',
                #https://api.mercadolibre.com/oauth/token
                'mercadopago_form_url': 'https://sandbox.mercadopago.com/mla/checkout/pay',
                'mercadopago_rest_url': 'https://api.sandbox.mercadolibre.com/oauth/token',
            }

    def _get_providers(self, context=None):

        providers = super(AcquirerMercadopago, self)._get_providers(cr, uid, context=context)
        providers.append(['mercadopago', 'MercadoPago'])

        print "_get_providers: ", providers

        return providers

    provider = fields.Selection(selection_add=[('mercadopago', 'MercadoPago')])
    #mercadopago_client_id = fields.Char('MercadoPago Client Id',required_if_provider='mercadopago')
    mercadopago_client_id = fields.Char('MercadoPago Client Id', size=256)
    #mercadopago_secret_key = fields.Char('MercadoPago Secret Key',required_if_provider='mercadopago')
    mercadopago_secret_key = fields.Char('MercadoPago Secret Key', size=256)

    #mercadopago_email_account = fields.Char('MercadoPago Email ID', required_if_provider='mercadopago')
    mercadopago_email_account = fields.Char('MercadoPago Email ID', size=256)

    mercadopago_seller_account = fields.Char(
            'MercadoPago Merchant ID',
            size=256,
            help='The Merchant ID is used to ensure communications coming from MercadoPago are valid and secured.')

    mercadopago_use_ipn = fields.Boolean('Use IPN', help='MercadoPago Instant Payment Notification')

    # Server 2 server
    mercadopago_api_enabled = fields.Boolean('Use Rest API')
    mercadopago_api_username = fields.Char('Rest API Username')
    mercadopago_api_password = fields.Char('Rest API Password')
    mercadopago_api_access_token = fields.Char('Access Token')
    mercadopago_api_access_token_validity = fields.Datetime('Access Token Validity')


    _defaults = {
        'mercadopago_use_ipn': True,
        'fees_active': False,
        'fees_dom_fixed': 0.35,
        'fees_dom_var': 3.4,
        'fees_int_fixed': 0.35,
        'fees_int_var': 3.9,
        'mercadopago_api_enabled': False,
    }

    def _migrate_mercadopago_account(self, context=None):
        """ COMPLETE ME """

        #cr.execute('SELECT id, mercadopago_account FROM res_company')
        #res = cr.fetchall()
        company_ids = self.env["res.company"].search([])
        for company in self.env['res.company'].browse(company_ids):
            company_id = company.id
            company_mercadopago_account = company.mercadopago_account
        #for (company_id, company_mercadopago_account) in res:
            if company_mercadopago_account:
                company_mercadopago_ids = self.search([('company_id', '=', company_id), ('provider', '=', 'mercadopago')], limit=1, context=context)
                if company_mercadopago_ids:
                    self.write( company_mercadopago_ids, {'mercadopago_email_account': company_mercadopago_account}, context=context)
                else:
                    mercadopago_view = self.env['ir.model.data'].get_object(cr, uid, 'payment_mercadopago', 'mercadopago_acquirer_button')
                    self.create({
                        'name': 'MercadoPago',
                        'provider': 'mercadopago',
                        'mercadopago_email_account': company_mercadopago_account,
                        'view_template_id': mercadopago_view.id,
                    }, context=context)
        return True

    def mercadopago_compute_fees(self, amount, currency_id, country_id):
        """ Compute mercadopago fees.

            :param float amount: the amount to pay
            :param integer country_id: an ID of a res.country, or None. This is
                                       the customer's country, to be compared to
                                       the acquirer company country.
            :return float fees: computed fees
        """
        #acquirer = self.browse( id, context=context)
        acquirer = self
        if not acquirer.fees_active:
            return 0.0
        country = self.env['res.country'].browse( country_id)
        if country and acquirer.company_id.country_id.id == country.id:
            percentage = acquirer.fees_dom_var
            fixed = acquirer.fees_dom_fixed
        else:
            percentage = acquirer.fees_int_var
            fixed = acquirer.fees_int_fixed
        fees = (percentage / 100.0 * amount + fixed ) / (1 - percentage / 100.0)
        return fees

    def mercadopago_dateformat(self, date):
        stf = date.strftime(dateformat)
        stf_utc_milis = date.strftime(dateformatmilis)
        stf_utc_milis = stf_utc_milis[0]+stf_utc_milis[1]+stf_utc_milis[2]
        stf_utc_zone = date.strftime(dateformatutc)
        stf_utc_zone = stf_utc_zone[0]+stf_utc_zone[1]+stf_utc_zone[2]+":"+stf_utc_zone[3]+stf_utc_zone[4]
        stf_utc = stf+stf_utc_milis+stf_utc_zone
        return stf_utc

    def make_path(self, path, params={}):
        # Making Path and add a leading / if not exist
        if not (re.search("^http", path)):
            if not (re.search("^\/", path)):
                path = "/" + path
            path = self.API_ROOT_URL + path
        if params:
            path = path + "?" + urlencode(params)
        return path

    @api.multi
    def mercadopago_form_generate_values(self, values):
        #import pdb; pdb.set_trace()

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        acquirer = self

        tx_values = dict(values)
        #print "mercadopago_form_generate_values: tx_values: ", tx_values
        #print "partner_values:", partner_values

        saleorder_obj = self.env['sale.order']
        saleorderline_obj = self.env['sale.order.line']
        sorder_s = saleorder_obj.search([ ('name','=',tx_values["reference"]) ] )
        shipments = ''
        amount = tx_values["amount"]
        melcatid = False
        if (sorder_s):
            print "sorder_s.name: ", sorder_s.name
            print "len(sorder_s.order_line): ", len(sorder_s.order_line)
            print "sorder_s.order_line[0]: ", sorder_s.order_line[0].name
            if (len(sorder_s.order_line)>0):
                firstprod = sorder_s.order_line[0].product_id
                if hasattr(firstprod, 'meli_category') and (firstprod.meli_category):
                    melcatid = firstprod.meli_category.meli_category_id
            for oline in  sorder_s.order_line:
                print "oline: ", oline.name
                print "oline.product_id: ", oline.product_id
                print "oline.product_id.name ", oline.product_id.name
                #print "oline.product_id.name ", oline.product_id.
                if (str(oline.product_id.name.encode("utf-8")) == str('MercadoEnvíos')):
                    print "oline category: ", melcatid
                    melcatidrequest = 'https://api.mercadolibre.com/categories/'+str(melcatid)+'/shipping'
                    headers = {'Accept': 'application/json', 'Content-type':'application/json'}
                    uri = self.make_path(melcatidrequest)
                    print "oline melcatidrequest: ", melcatidrequest
                    response = requests.get(uri, params='', headers=headers)
                    print "oline melcatidrequest RESPONSE: ", str(response.content)
                    if response.status_code == requests.codes.ok:
                        rdims = response.json()
                        dims = str(rdims["height"])+str("x")+str(rdims["width"])+str("x")+str(rdims["length"])+str(",")+str(rdims["weight"])
                        shipments = {
                            "mode": "me2",
                            #"dimensions": "30x30x30,500",
                            "dimensions": dims,
                            "zip_code": tx_values.get("partner_zip"),
                        }
                    print "oline shipments: ", shipments

        MPago = False
        MPagoPrefId = False

        if acquirer.mercadopago_client_id and acquirer.mercadopago_secret_key:
            MPago = mercadopago.MP( acquirer.mercadopago_client_id, acquirer.mercadopago_secret_key )
            #_logger.info( MPago )
            print "MPago:", MPago
        else:
            error_msg = 'YOU MUST COMPLETE acquirer.mercadopago_client_id and acquirer.mercadopago_secret_key'
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        jsondump = ""

        if MPago:

            if acquirer.environment=="prod":
                MPago.sandbox_mode(False)
            else:
                MPago.sandbox_mode(True)

            MPagoToken = MPago.get_access_token()

            #mpago = https://api.mercadolibre.com/categories/MLA371926/shipping
            #cost: https://api.mercadolibre.com/users/:user_id/shipping_options?category_id=:category_id&dimensions=:dim&zip_code=13565905
            #request

            #{ "category_id": "MLA371926", "height": 30, "width": 30, "length": 30, "weight": 650 }

            preference = {
                "items": [
                {
                    "title": "Orden Ecommerce "+ tx_values["reference"] ,
                    #"picture_url": "https://www.mercadopago.com/org-img/MP3/home/logomp3.gif",
                    "quantity": 1,
                    "currency_id":  tx_values['currency'] and tx_values['currency'].name or '',
                    "unit_price": amount,
                    #"categoryid": "Categoría",
                }
                ]
                ,
                "payer": {
		            "name": tx_values.get("partner_name"),
		            "surname": tx_values.get("partner_first_name"),
		            "email": tx_values.get("partner_email"),
#		            "date_created": "2015-01-29T11:51:49.570-04:00",
		            "phone": {
#			            "area_code": "+5411",
			            "number": tx_values.get("partner_phone")
		            },
#		            "identification": {
#			            "type": "DNI",
#			            "number": "12345678"
#		            },
		            "address": {
			            "street_name": tx_values.get("partner_address"),
			            "street_number": "",
			            "zip_code": tx_values.get("partner_zip"),
		            }
	            },
	            "back_urls": {
		            "success": '%s' % urlparse.urljoin( base_url, MercadoPagoController._return_url),
		            "failure": '%s' % urlparse.urljoin( base_url, MercadoPagoController._cancel_url),
		            "pending": '%s' % urlparse.urljoin( base_url, MercadoPagoController._return_url)
	            },
	            "auto_return": "approved",
#	            "payment_methods": {
#		            "excluded_payment_methods": [
#			            {
#				            "id": "amex"
#			            }
#		            ],
#		            "excluded_payment_types": [
#			            {
#				            "id": "ticket"
#			            }
#		            ],
#		            "installments": 24,
#		            "default_payment_method_id": '',
#		            "default_installments": '',
#	            },
#	            "shipments": {
#		            "receiver_address":
#		             {
#			            "zip_code": "1430",
#			            "street_number": 123,
#			            "street_name": "Calle Trece",
#			            "floor": 4,
#			            "apartment": "C"
#		            }
#	            },
	            "notification_url": '%s' % urlparse.urljoin( base_url, MercadoPagoController._notify_url),
	            "external_reference": tx_values["reference"],
	            "expires": True,
	            "expiration_date_from": self.mercadopago_dateformat( datetime.datetime.now(tzlocal()) ),
	            "expiration_date_to": self.mercadopago_dateformat( datetime.datetime.now(tzlocal())+datetime.timedelta(days=31) )
                }

            if (len(shipments)):
                preference["shipments"] = shipments

            print "preference:", preference

            preferenceResult = MPago.create_preference(preference)

            print "preferenceResult: ", preferenceResult
            if 'response' in preferenceResult:
                if 'error' in preferenceResult['response']:
                    error_msg = 'Returning response is:'
                    error_msg+= json.dumps(preferenceResult, indent=2)
                    _logger.error(error_msg)
                    raise ValidationError(error_msg)

                if 'id' in preferenceResult['response']:
                    MPagoPrefId = preferenceResult['response']['id']
            else:
                error_msg = 'Returning response is:'
                error_msg+= json.dumps(preferenceResult, indent=2)
                _logger.error(error_msg)
                raise ValidationError(error_msg)


            if acquirer.environment=="prod":
                linkpay = preferenceResult['response']['init_point']
            else:
                linkpay = preferenceResult['response']['sandbox_init_point']

            jsondump = json.dumps( preferenceResult, indent=2 )

            print "linkpay:", linkpay
            print "jsondump:", jsondump
            print "MPagoPrefId: ", MPagoPrefId
            print "MPagoToken: ", MPagoToken


        mercadopago_tx_values = dict(tx_values)
        if MPagoPrefId:
            mercadopago_tx_values.update({
            'pref_id': MPagoPrefId,
#            'cmd': '_xclick',
#            'business': acquirer.mercadopago_email_account,
#            'item_name': tx_values['reference'],
#            'item_number': tx_values['reference'],
#            'amount': tx_values['amount'],
#            'currency_code': tx_values['currency'] and tx_values['currency'].name or '',
#            'address1': partner_values['address'],
#            'city': partner_values['city'],
#            'country': partner_values['country'] and partner_values['country'].name or '',
#            'state': partner_values['state'] and partner_values['state'].name or '',
#            'email': partner_values['email'],
#            'zip': partner_values['zip'],
#            'first_name': partner_values['first_name'],
#            'last_name': partner_values['last_name'],
#            'return': '%s' % urlparse.urljoin(base_url, MercadoPagoController._return_url),
#            'notify_url': '%s' % urlparse.urljoin(base_url, MercadoPagoController._notify_url),
#            'cancel_return': '%s' % urlparse.urljoin(base_url, MercadoPagoController._cancel_url),
            })

#        if acquirer.fees_active:
#            mercadopago_tx_values['handling'] = '%.2f' % mercadopago_tx_values.pop('fees', 0.0)
#        if mercadopago_tx_values.get('return_url'):
#            mercadopago_tx_values['custom'] = json.dumps({'return_url': '%s' % mercadopago_tx_values.pop('return_url')})
        return mercadopago_tx_values

    @api.multi
    def mercadopago_get_form_action_url(self):
        return self._get_mercadopago_urls( self.environment)['mercadopago_form_url']

    def _mercadopago_s2s_get_access_token(self, ids, context=None):
        """
        Note: see # see http://stackoverflow.com/questions/2407126/python-urllib2-basic-auth-problem
        for explanation why we use Authorization header instead of urllib2
        password manager
        """
        res = dict.fromkeys(ids, False)
        parameters = werkzeug.url_encode({'grant_type': 'client_credentials'})

        for acquirer in self.browse( ids, context=context):
            tx_url = self._get_mercadopago_urls( acquirer.environment)['mercadopago_rest_url']
            request = urllib2.Request(tx_url, parameters)

            # add other headers (https://developer.paypal.com/webapps/developer/docs/integration/direct/make-your-first-call/)
            request.add_header('Accept', 'application/json')
            request.add_header('Accept-Language', 'en_US')

            # add authorization header
            base64string = base64.encodestring('%s:%s' % (
                acquirer.mercadopago_api_username,
                acquirer.mercadopago_api_password)
            ).replace('\n', '')
            request.add_header("Authorization", "Basic %s" % base64string)

            request = urllib2.urlopen(request)
            result = request.read()
            res[acquirer.id] = json.loads(result).get('access_token')
            request.close()
        return res


class TxMercadoPago(models.Model):
    _inherit = 'payment.transaction'

    mercadopago_txn_id = fields.Char('Transaction ID')
    mercadopago_txn_type = fields.Char('Transaction type')


    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------
    @api.model
    def _mercadopago_form_get_tx_from_data(self, data, context=None):
#        reference, txn_id = data.get('external_reference'), data.get('txn_id')
        #import pdb; pdb.set_trace()
        reference, collection_id = data.get('external_reference'), data.get('collection_id')
        if not reference or not collection_id:
            error_msg = 'MercadoPago: received data with missing reference (%s) or collection_id (%s)' % (reference,collection_id)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        tx_ids = self.env['payment.transaction'].search( [('reference', '=', reference)])
        if not tx_ids or len(tx_ids) > 1:
            error_msg = 'MercadoPago: received data for reference %s' % (reference)
            if not tx_ids:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx_ids

    @api.multi
    def _mercadopago_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        _logger.warning('Received a notification from MercadoLibre.')

        # TODO: txn_id: shoudl be false at draft, set afterwards, and verified with txn details
#        if tx.acquirer_reference and data.get('txn_id') != tx.acquirer_reference:
#            invalid_parameters.append(('txn_id', data.get('txn_id'), tx.acquirer_reference))
        # check what is buyed
#        if float_compare(float(data.get('mc_gross', '0.0')), (tx.amount + tx.fees), 2) != 0:
#            invalid_parameters.append(('mc_gross', data.get('mc_gross'), '%.2f' % tx.amount))  # mc_gross is amount + fees
#        if data.get('mc_currency') != tx.currency_id.name:
#            invalid_parameters.append(('mc_currency', data.get('mc_currency'), tx.currency_id.name))
#        if 'handling_amount' in data and float_compare(float(data.get('handling_amount')), tx.fees, 2) != 0:
#            invalid_parameters.append(('handling_amount', data.get('handling_amount'), tx.fees))
        # check buyer
#        if tx.partner_reference and data.get('payer_id') != tx.partner_reference:
#            invalid_parameters.append(('payer_id', data.get('payer_id'), tx.partner_reference))
        # check seller
#        if data.get('receiver_email') != tx.acquirer_id.mercadopago_email_account:
#            invalid_parameters.append(('receiver_email', data.get('receiver_email'), tx.acquirer_id.mercadopago_email_account))
#        if data.get('receiver_id') and tx.acquirer_id.mercadopago_seller_account and data['receiver_id'] != tx.acquirer_id.mercadopago_seller_account:
#            invalid_parameters.append(('receiver_id', data.get('receiver_id'), tx.acquirer_id.mercadopago_seller_account))

        return invalid_parameters

#From https://developers.mercadopago.com/documentacion/notificaciones-de-pago
#
#approved 	El pago fue aprobado y acreditado.
#pending 	El usuario no completó el proceso de pago.
#in_process	El pago está siendo revisado.
#rejected 	El pago fue rechazado. El usuario puede intentar nuevamente.
#refunded (estado terminal) 	El pago fue devuelto al usuario.
#cancelled (estado terminal) 	El pago fue cancelado por superar el tiempo necesario para realizar el pago o por una de las partes.
#in_mediation 	Se inició una disputa para el pago.
#charged_back (estado terminal) 	Se realizó un contracargo en la tarjeta de crédito.
    #called by Trans.form_feedback(...) > %s_form_validate(...)
    @api.multi
    def _mercadopago_form_validate(self, data):
        #import pdb;pdb.set_trace()
        status = data.get('collection_status')
        data = {
            'acquirer_reference': data.get('external_reference'),
            'mercadopago_txn_type': data.get('payment_type')
        }
        if status in ['approved', 'processed']:
            _logger.info('Validated MercadoPago payment for tx %s: set as done' % (self.reference))
            data.update(state='done', date_validate=data.get('payment_date', fields.datetime.now()))
            return self.write(data)
        elif status in ['pending', 'in_process','in_mediation']:
            _logger.info('Received notification for MercadoPago payment %s: set as pending' % (self.reference))
            data.update(state='pending', state_message=data.get('pending_reason', ''))
            return self.write(data)
        elif status in ['cancelled','refunded','charged_back','rejected']:
            _logger.info('Received notification for MercadoPago payment %s: set as cancelled' % (self.reference))
            data.update(state='cancel', state_message=data.get('cancel_reason', ''))
            return self.write(data)
        else:
            error = 'Received unrecognized status for MercadoPago payment %s: %s, set as error' % (self.reference, status)
            _logger.info(error)
            data.update(state='error', state_message=error)
            return self.write(data)

    # --------------------------------------------------
    # SERVER2SERVER RELATED METHODS
    # --------------------------------------------------

    def _mercadopago_try_url(self, request, tries=3, context=None):
        """ Try to contact MercadoPago. Due to some issues, internal service errors
        seem to be quite frequent. Several tries are done before considering
        the communication as failed.

         .. versionadded:: pre-v8 saas-3
         .. warning::

            Experimental code. You should not use it before OpenERP v8 official
            release.
        """
        done, res = False, None
        while (not done and tries):
            try:
                res = urllib2.urlopen(request)
                done = True
            except urllib2.HTTPError as e:
                res = e.read()
                e.close()
                if tries and res and json.loads(res)['name'] == 'INTERNAL_SERVICE_ERROR':
                    _logger.warning('Failed contacting MercadoPago, retrying (%s remaining)' % tries)
            tries = tries - 1
        if not res:
            pass
            # raise openerp.exceptions.
        result = res.read()
        res.close()
        return result

    def _mercadopago_s2s_send(self, values, cc_values, context=None):
        """
         .. versionadded:: pre-v8 saas-3
         .. warning::

            Experimental code. You should not use it before OpenERP v8 official
            release.
        """
        tx = self.create( values, context=context)
        tx_id = tx.id

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % tx.acquirer_id._mercadopago_s2s_get_access_token()[tx.acquirer_id.id],
        }
        data = {
            'intent': 'sale',
            'transactions': [{
                'amount': {
                    'total': '%.2f' % tx.amount,
                    'currency': tx.currency_id.name,
                },
                'description': tx.reference,
            }]
        }
        if cc_values:
            data['payer'] = {
                'payment_method': 'credit_card',
                'funding_instruments': [{
                    'credit_card': {
                        'number': cc_values['number'],
                        'type': cc_values['brand'],
                        'expire_month': cc_values['expiry_mm'],
                        'expire_year': cc_values['expiry_yy'],
                        'cvv2': cc_values['cvc'],
                        'first_name': tx.partner_name,
                        'last_name': tx.partner_name,
                        'billing_address': {
                            'line1': tx.partner_address,
                            'city': tx.partner_city,
                            'country_code': tx.partner_country_id.code,
                            'postal_code': tx.partner_zip,
                        }
                    }
                }]
            }
        else:
            # TODO: complete redirect URLs
            data['redirect_urls'] = {
                # 'return_url': 'http://example.com/your_redirect_url/',
                # 'cancel_url': 'http://example.com/your_cancel_url/',
            },
            data['payer'] = {
                'payment_method': 'mercadopago',
            }
        data = json.dumps(data)

        request = urllib2.Request('https://api.sandbox.paypal.com/v1/payments/payment', data, headers)
        result = self._mercadopago_try_url(request, tries=3, context=context)
        return (tx_id, result)

    def _mercadopago_s2s_get_invalid_parameters(self, tx, data, context=None):
        """
         .. versionadded:: pre-v8 saas-3
         .. warning::

            Experimental code. You should not use it before OpenERP v8 official
            release.
        """
        invalid_parameters = []
        return invalid_parameters

    def _mercadopago_s2s_validate(self, tx, data, context=None):
        """
         .. versionadded:: pre-v8 saas-3
         .. warning::

            Experimental code. You should not use it before OpenERP v8 official
            release.
        """
        values = json.loads(data)
        status = values.get('state')
        if status in ['approved']:
            _logger.info('Validated Mercadopago s2s payment for tx %s: set as done' % (tx.reference))
            tx.write({
                'state': 'done',
                'date_validate': values.get('udpate_time', fields.datetime.now()),
                'mercadopago_txn_id': values['id'],
            })
            return True
        elif status in ['pending', 'expired']:
            _logger.info('Received notification for MercadoPago s2s payment %s: set as pending' % (tx.reference))
            tx.write({
                'state': 'pending',
                # 'state_message': data.get('pending_reason', ''),
                'mercadopago_txn_id': values['id'],
            })
            return True
        else:
            error = 'Received unrecognized status for MercadoPago s2s payment %s: %s, set as error' % (tx.reference, status)
            _logger.info(error)
            tx.write({
                'state': 'error',
                # 'state_message': error,
                'mercadopago_txn_id': values['id'],
            })
            return False

    def _mercadopago_s2s_get_tx_status(self, tx, context=None):
        """
         .. versionadded:: pre-v8 saas-3
         .. warning::

            Experimental code. You should not use it before OpenERP v8 official
            release.
        """
        # TDETODO: check tx.mercadopago_txn_id is set
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % tx.acquirer_id._mercadopago_s2s_get_access_token()[tx.acquirer_id.id],
        }
        url = 'https://api.sandbox.paypal.com/v1/payments/payment/%s' % (tx.mercadopago_txn_id)
        request = urllib2.Request(url, headers=headers)
        data = self._mercadopago_try_url(request, tries=3, context=context)
        return self.s2s_feedback( tx.id, data, context=context)
