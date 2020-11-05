# -*- coding: utf-8 -*-
# © 2020 Reison Torres <reison.torres@gmail.com>

import json
from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _confirm_delivery(self):
        self.ensure_one()

        # finalizar flujo de entrega
        if self.state == "sale" and self.invoice_status in ['to invoice', 'invoiced']:
            self.picking_ids._picking_done('outgoing')

            # confirmar pago de website so
            if self.payment_tx_id and self.picking_ids.filtered(lambda rec: rec.picking_type_code == 'outgoing').state == ['done']:
                delivery_acquirer_ids = self.env['ir.values'].get_default('sale.config.settings', 'delivery_payment_acquirer_ids')
                provider_all = self.env['payment.acquirer'].browse(delivery_acquirer_ids).mapped('provider')
                provider = self.payment_acquirer_id.provider
                payment_tx = self.payment_tx_id
                if provider in provider_all:
                    # finalizar la transacion
                    if provider == "delivery" and payment_tx.state == 'pending':
                        data = dict(reference=payment_tx.reference,
                                    amount=payment_tx.amount,
                                    currency=payment_tx.currency_id.name if payment_tx.currency_id else '',
                                    state='done'
                                    )
                        payment_tx.with_context(send_email=True).form_feedback(data, provider)
                    elif provider in provider_all and payment_tx.state == 'done':
                        if self.invoice_status == 'invoiced':
                            self.invoice_ids.force_invoice_sent()

        return (self.picking_ids.state == 'done' and payment_tx.state == 'done')

    @api.multi
    def _prepare_delivery(self):
        self.ensure_one()
        
        if self.state == "sale" and self.invoice_status in ['to invoice', 'invoiced']:
            self.picking_ids._picking_done('internal')
        
        return (self.picking_ids.state == 'done')

    @api.multi
    def get_so_delivery(self, picking_type_code):
        picking_ids = self.env['stock.picking']\
                    .search([('state', 'in', ['assigned']), ('picking_type_code', '=', picking_type_code)])

        group_ids = picking_ids.mapped('group_id.id')
        rec = self.env['sale.order'].search([('procurement_group_id.id', 'in', group_ids)])

        return self._rec_to_dict(rec, picking_ids.mapped('id'))

    def _rec_to_dict(self, rec, picking_ids):
        result = []
        for sale in rec:
            data = dict(
                id=sale.id,
                name=sale.name,
                state=sale.state,
                amount_total=sale.amount_total,
                partner_id=dict(
                        id=sale.partner_id.id,
                        name=sale.partner_id.name,
                        street=sale.partner_id.street,
                        street2=sale.partner_id.street2,
                        city=sale.partner_id.city,
                        email=sale.partner_id.email,
                        phone=sale.partner_id.phone,
                        mobile=sale.partner_id.mobile
                    ),
                order_line=[
                    dict(
                        id=item.id,
                        name=item.name,
                        price_unit=item.price_unit,
                        product_uom_qty=item.product_uom_qty,
                        price_subtotal=item.price_subtotal,
                    ) for item in sale.order_line],
                picking_ids=[
                    dict(
                        id=pick.id,
                        picking_type_code=pick.picking_type_code,
                        state=pick.state,
                        min_date=pick.min_date
                    ) for pick in sale.picking_ids.filtered(lambda rec: rec.id in picking_ids)],
            )

            result.append(data)

        return result
