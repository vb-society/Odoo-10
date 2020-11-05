# -*- coding: utf-8 -*-
# Copyright 2019 ePayco.co
# - Manuel Marquez <buzondemam@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EpaycoDocumentType(models.Model):
    _name = 'epayco.document.type'
    # _rec_name = 'l10n_co_document_type'

    # @api.model
    # def _get_document_types(self):
    #    """Returns options for selection field l10n_co_document_type."""
    #    res_partner = self.env['res.partner']
    #    model_fields = res_partner.fields_get(['l10n_co_document_type'])
    #    options_dict = dict(
    #    model_fields['l10n_co_document_type']['selection'])
    #    options = [(k, options_dict[k]) for k in options_dict]
    #    return options

    active = fields.Boolean(default=True)
    epayco_document_type = fields.Char(
        string='ePayco Document Type',
        help='Code of document type comming from ePayco.')
    l10n_co_document_type = fields.Selection(
        selection=[('rut', 'RUT'),
                   ('id_document', 'Cédula'),
                   ('id_card', 'Tarjeta de Identidad'),
                   ('passport', 'Pasaporte'),
                   ('foreign_id_card', 'Cédula Extranjera'),
                   ('external_id', 'ID del Exterior'),
                   ('diplomatic_card', 'Carné Diplomatico'),
                   ('residence_document', 'Salvoconducto de Permanencia'),
                   ('civil_registration', 'Registro Civil'),
                   ('national_citizen_id', 'Cédula de ciudadanía')], string='Document Type')
    payment_acquirer_id = fields.Many2one(
        comodel_name='payment.acquirer',
        string='Payment Acquirer',
        help='Only valid for ePayco.')
