# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)

class FieldMapping(models.Model):
    _name = 'fb.field.mappning'

    name = fields.Char(string="Name",required=True)
    active = fields.Boolean(string="Active",default=True)
    field_mapping_line_ids = fields.One2many(comodel_name='fb.field.mappning.line',inverse_name='field_mapping_id',string="Fileds To Mapped")
