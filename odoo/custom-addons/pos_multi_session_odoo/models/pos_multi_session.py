# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import Warning
import random
from datetime import date, datetime


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pos_multi_session_id = fields.Many2one('pos.multi.session', 'POS Multi session')
    #pos_allow_order = fields.Boolean(string='Allow POS Order')
    #pos_deny_order = fields.Char(string='Deny POS Order')
    pos_accept_orders = fields.Boolean(string='Accept Multi Session Orders')
        
class PosMultiSession(models.Model):
    _name = 'pos.multi.session'

    name = fields.Char('Name')
    pos_session_ids = fields.One2many('pos.config','pos_multi_session_id','POS Session')
    '''show_stock_location = fields.Selection([
        ('all', 'All Warehouse'),
        ('specific', 'Current Session Warehouse'),
        ], string='Show Stock Of', default='all')'''


    @api.one
    def sync_multi_session(self, message):
        bi = []
        #print "selfffffffffffffffffffffffffffffffffffffffffffffffffffff",self,self.id,bi
        for pos_session in self.env['pos.session'].search([('state', '!=', 'closed'),('config_id.pos_multi_session_id', '=', self.id)]):
            if pos_session.user_id.id != self.env.user.id:
                bi.append([(self._cr.dbname, 'pos.multi.session', pos_session.user_id.id), message])
                #print "222222222222222222 biiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",bi
        self.env['bus.bus'].sendmany(bi)
        #print "biiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",bi
        return 1
        
                
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
