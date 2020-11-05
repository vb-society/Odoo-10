# -*- coding: utf-8 -*-
# Copyright 2019 ePayco.co
# - Manuel Marquez <buzondemam@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment_epayco.controllers.main import EpaycoController
from odoo.exceptions import ValidationError


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('epayco', 'ePayco')])
    payment_icon_ids = fields.Many2many('epayco.payment.icon', string='Supported Payment Icons')
    epayco_payment_method_ids = fields.Many2many(
        'epayco.payment.method',
        string='Payment Method  Available',
        help='Supported Payment method. '
        'Payment method available on ePayco checkout.')
    epayco_p_cust_id = fields.Char(
        'P_CUST_ID_CLIENTE',
        required_if_provider='epayco',
        help='Customer ID that identifies you in ePayco.'
        'You can find it in your dashboard in the configuration option.')
    epayco_p_key = fields.Char(
        'P_KEY',
        required_if_provider='epayco',
        help='Key to sign the information sent and received from ePayco.'
        'You can find it in your dashboard in the configuration option.')
    epayco_public_key = fields.Char(
        'PUBLIC_KEY',
        required_if_provider='epayco',
        help='Key to authenticate and consume ePayco services.'
        'You can find it in your dashboard in the configuration option.')
    epayco_checkout_type = fields.Selection(
        selection=[('onpage', 'Onpage Checkout'),
                   ('standard', 'Standard Checkout')],
        required_if_provider='epayco',
        string='Checkout Type',
        default='onpage')
    epayco_franchise_ids = fields.One2many(
        comodel_name='epayco.franchise',
        inverse_name='payment_acquirer_id',
        string='Franchises')
    epayco_tx_state_ids = fields.One2many(
        comodel_name='epayco.tx.state',
        inverse_name='payment_acquirer_id',
        string='Transaction States',
        help='Mapping of ePayco transaction states according to'
        'odoo transaction states.')
    epayco_document_type_ids = fields.One2many(
        comodel_name='epayco.document.type',
        inverse_name='payment_acquirer_id',
        string='Document Types',
        help='Mapping of ePayco document types according to'
        'odoo document types.')

    @api.multi
    def epayco_get_form_action_url(self):
        """Return url for form action of template form button."""
        return '/payment/epayco/checkout/'

    @api.multi
    def epayco_form_generate_values(self, values):
        """Generate values to use in template qweb of form button."""
        self.ensure_one()
        epayco_checkout_external = (
            'false' if self.epayco_checkout_type == 'onpage' else 'true')
        env_test = 'true' if self.environment == 'test' else 'false'
        partner_lang = values.get('partner') and values['partner'].lang
        lang = 'es' if 'es' in partner_lang else 'en'
        epayco_document_type = self.env['epayco.document.type']
        epayco_method_disable = bytes("[\'%s\']").encode('utf-8') % ('\',\''.join(self.epayco_payment_method_ids._get_method_disable()))
        
        #document_type = epayco_document_type.search([(
        #    'l10n_co_document_type',
        #    '=',
        #    values['partner'].l10n_co_document_type)])

        document_type = epayco_document_type.search([(
            'l10n_co_document_type',
            '=', 'national_citizen_id')])

        if not document_type:
            raise ValidationError(_(
                'There is no ePayco document type related to customer document'
                'type %s.') % values['partner'].l10n_co_document_type)

        partner_document_type = document_type.epayco_document_type
        partner_vat = values.get('partner') and values['partner'].vat
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        reference = values.get('reference')
        epayco_tx_values = dict(values)
        
        order = ''
        tx = self.env['payment.transaction'].search([('reference', '=', reference)])
        sorder_s = False
        if tx:
            order = tx.sale_order_id.name
            sorder_s = tx.sale_order_id
            
        so_amount_tax = sorder_s.amount_tax if sorder_s else 0.0
        so_amount_untaxed = sorder_s.amount_untaxed if sorder_s else 0.0
        
        epayco_show_button = (not reference == '/')
        epayco_tx_values.update({
            'epayco_show_button': epayco_show_button,
            'currency_code': values.get('currency') and values[
                'currency'].name.lower(),
            'epayco_public_key': self.epayco_public_key,
            'epayco_checkout_external': epayco_checkout_external,
            'country_code': values.get('partner_country') and values[
                'partner_country'].code.lower(),
            'epayco_env_test': env_test,
            'epayco_lang': lang,
            'billing_partner_document_type': partner_document_type,
            'billing_partner_vat': partner_vat,
            'billing_partner_city': values.get('billing_partner_city'),
            'response_url': urls.url_join(
                base_url, EpaycoController._response_url),
            'confirmation_url': urls.url_join(
                base_url, EpaycoController._confirmation_url),
            'order': order,
            'amount_tax': so_amount_tax,
            'amount_untaxed': so_amount_untaxed,
            'epayco_method_disable': epayco_method_disable
        })
        return epayco_tx_values
