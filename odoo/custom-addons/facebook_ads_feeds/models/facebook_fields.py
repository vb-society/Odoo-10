# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################

from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)

class FacebookFields(models.Model):
    _name = 'fb.facebook.fields'

    name = fields.Char(string="Field",required=True)
    required = fields.Boolean(string="Required")
    g_beg = fields.Boolean(string="Begins With \'g:\'")
