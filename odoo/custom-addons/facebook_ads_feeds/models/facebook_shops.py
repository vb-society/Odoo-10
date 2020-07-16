# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import models,fields,api
import json
import logging
from odoo.http import request
_logger = logging.getLogger(__name__)
from odoo.tools.safe_eval import safe_eval
import xml.etree.ElementTree as ET
import base64
from odoo.fields import Datetime
from odoo.exceptions import UserError
from odoo.addons.http_routing.models.ir_http import slug

# text_with_g_at_beg = ['id','title','description','link','image_link','brand','condition','availability','price','sale_price']
fixed_fields_layout = ['price','link','image_link','sale_price']
to_remove_keys = ['CURRENCY','BASE_URL','ID','SLUG']
many2one_fields = ['google_product_category']

class xml(object):

    @staticmethod
    def _encode_content(data):
        # .replace('&', '&amp;')
        return data.replace('<','&lt;').replace('>','&gt;').replace('"', '&quot;')

    @classmethod
    def dumps(cls,key,obj):
        # if isinstance(obj, dict) and key in obj.keys() and isinstance(obj[key], list):
        #     return "".join("%s" % (cls.dumps(key, obj[key])))
        if isinstance(obj, dict):

            # return cls.dumps(key, obj[key])
            return "".join(("<%s>%s</%s>" % (key, cls.dumps(key, obj[key]), key),cls.dumps(key, obj[key]))[isinstance(obj[key], list)] for key in obj)
        elif isinstance(obj, list):

            return "".join("<%s>%s</%s>" % (key, cls.dumps(key,element), key) for index,element in enumerate(obj))
        else:
            return "%s" % (xml._encode_content(obj.__str__()))

    @staticmethod
    def loads(string):
        def _node_to_dict(node):
            if node.text:
                return node.text
            else:
                return {child.tag: _node_to_dict(child) for child in node}
        root = ET.fromstring(string)
        return {root.tag: _node_to_dict(root)}




class FacebookMerchantShop(models.Model):
    _name = 'fb.facebook.shop'



    def _get_default_domain(self):
        domain = [("sale_ok", "=", True),("website_published","=",True)]
        return domain

    @api.onchange('id','shop_url')
    def _get_feed_url(self):
        if self.shop_url and self.id:
            url = str(self.shop_url)+"/shop/"+str(self.id)+"/content"
            self.feed_url =  url

    name = fields.Char(string="Shop Name",required=True,translate=True)
    id=fields.Integer(string="Sequence No")
    currency_id = fields.Many2one(string="Currency",store=True)
    website_id = fields.Many2one('website', string="website")
    currency_id = fields.Many2one(string="Currency",related="pricelist_id.currency_id",readonly=True)
    content_language_id = fields.Many2one(string="Content Language",comodel_name="res.lang",required=True,help="Language in which your products will get sync on Facebook Shop")
    shop_url=fields.Char(name="Shop URL",help="Write your domain name of your website")
    feed_url=fields.Char(string="URL",readonly=True,compute="_get_feed_url")
    pricelist_id = fields.Many2one(comodel_name="product.pricelist",string="Product Pricelist",required=True,help="select the pricelist according to which your product price will get selected")
    field_mapping_id = fields.Many2one(comodel_name="fb.field.mappning",string="Field Mapping",domain=[('active','=',True)],required=True)
    product_selection_type = fields.Selection([('domain','Domain'),('manual','Manual'),('category','Category')],default = "domain",string="Product Select Way",help="Select wether you want to select the product manually or with the help of domain")
    domain_input = fields.Char(string="Domain",default="[]")
    limit = fields.Integer(string="Limit",default=10)
    product_ids_rel = fields.Many2many(comodel_name='product.template', relation='fb_shop_product_rel', column1='facebook_id', column2='product_id',domain=_get_default_domain , string="Products")
    public_categ_ids = fields.Many2many(comodel_name='product.public.category', relation='fb_shop_public_category_rel', column1='facebook_id', column2='prod_cat_id', string="Category")
    mapping_count=fields.Integer(srting="Total Mappings",compute="_mapping_count")
    crone_id=fields.Many2one(comodel_name='ir.cron',string="Cron Detail",readonly=True)

    def _mapping_count(self):
        for rec in self:
            rec.mapping_count=self.env['fb.attachment.mapping'].search_count([('fb_shop','=',self.id)])



    def test_function(self):

        mappings = self.env['fb.attachment.mapping'].search([('fb_shop','=',self.id)]).ids
        action = self.env.ref('facebook_ads_feeds.fb_attachment_mapping_action').read()[0]
        action['domain'] = [('id', 'in', mappings)]
        return action

    def _get_product_fields(self,field_mapping_lines_ids):
        field_mapping_model=self.env['fb.field.mappning.line'].search_read([('id','in',field_mapping_lines_ids),('fixed','=',False)],['model_field_id'])
        #
        field_mapping_model_ids=[x.get('model_field_id')[0] for x in field_mapping_model]
        field_mapping_model_name_ids=self.env['ir.model.fields'].sudo().search_read([('id','in',field_mapping_model_ids)],['name'])
        #
        field_mapping_model_name=[x.get('name') for x in field_mapping_model_name_ids]
        #
        #
        # return product_detail
        return field_mapping_model_name

    def _get_final_domain(self,domain=[]):
        design_domain=self._get_default_domain()
        s_count=len(design_domain)
        design_domain += domain
        return design_domain


    def _wrap2xml(self, data):
        resp_xml = "<?xml version='1.0' encoding='UTF-8'?>"
        resp_xml +="<feed xmlns='http://www.w3.org/2005/Atom' xmlns:g='http://base.google.com/ns/1.0'>"
        resp_xml += xml.dumps("",data)
        resp_xml +="</feed>"
        return resp_xml

    def _get_product_detail(self,field_mapping_lines_ids):

        sel_type=self.product_selection_type

        context = self._context.copy()
        context.update({'pricelist': self.pricelist_id.id,'website_id':self.website_id.id,'lang': self.content_language_id.code})

        field_mapping_model_name = self._get_product_fields(field_mapping_lines_ids)
        if(sel_type == 'domain'):
            domain = safe_eval(self.domain_input)
            final_domain=self._get_final_domain(domain=domain)

        elif(sel_type == 'manual'):

            return self.env['product.template'].with_context(context).browse(self.product_ids_rel.ids).read(field_mapping_model_name)
        elif(sel_type == 'category'):
            categ_ids=self.public_categ_ids.ids
            categ_domain=[('public_categ_ids','child_of',categ_ids)]
            final_domain=self._get_final_domain(domain=categ_domain)

            # self.env['product.template'].search(final_domain).ids
        else:
            return False
        return self.env['product.template'].with_context(context).search_read(final_domain,field_mapping_model_name)

    def _get_one_product_mapping(self,product_detail,field_mapping_lines):
        #
        product_ref=self.env['product.template'].browse(product_detail.get('id'))
        d={}
        d['SLUG'] = slug(product_ref)
        d['ID'] = str(product_detail.get('id'))
        d['BASE_URL'] = self.shop_url
        d['CURRENCY'] = self.currency_id.name
        for i in field_mapping_lines:
            key=i.facebook_field_id.name
            if i.fixed:
                value=i.fixed_text
            else:
                if (key in many2one_fields):
                    v_name=product_detail.get(i.model_field_id.name)
                    if v_name:
                        value=v_name[1]
                    else:
                        value = False or i.default

                elif (key in fixed_fields_layout): #  ---------------make value accorrding to fixed layout
                    v_name=product_detail.get(i.model_field_id.name) or i.default
                    value = self._default_designed_function(key,v_name,d)
                else:
                    # v_name=i.model_field_id.name
                    value=product_detail.get(i.model_field_id.name) or i.default
            if i.facebook_field_id.g_beg:
                key="g:"+str(key)
            d[key] = value


        for i in to_remove_keys:
            if(i in d.keys()):
                d.pop(i)

        return d
        # return 1
    def _get_product_mapping(self,product_detail,field_mapping_lines):
        final_list_of_dict=[]
        for i in product_detail:

            data = self._get_one_product_mapping(i,field_mapping_lines)
            final_list_of_dict+=[data]
        return final_list_of_dict

    def _default_designed_function(self,key,value,d):
        if(key == 'price'):
            value=self.website_id.company_id.currency_id.compute(value,self.pricelist_id.currency_id)
            return str(value)+" "+d.get('CURRENCY')
        elif (key == 'sale_price'):
            return str(value)+" "+d.get('CURRENCY')
        elif (key == 'link'):
            product_url=d.get('BASE_URL')+"/shop/product/"+d.get('SLUG')
            return product_url
        elif (key == 'image_link'):
            image_url = d.get('BASE_URL')+"/web/image/product.template/"+d.get('ID')+"/image_1024/600x600"
            return image_url
        else:
            pass


    def _get_dict(self):
        field_mapping_lines_ids=self.field_mapping_id.field_mapping_line_ids
        final_dict={}
        final_dict['title'] = self.with_context(lang = self.content_language_id.code).name
        final_dict['link'] = self.shop_url
        produc_detail = self._get_product_detail(field_mapping_lines_ids.ids)
        final_dict['entry'] = self._get_product_mapping(produc_detail,field_mapping_lines_ids)

        return self._wrap2xml(final_dict)

    def _store_data(self,final_xml):

        name=str(self.name)+"/"+str(Datetime.now())
        _attach_1 = self.env['ir.attachment'].create({
        'name':name,
        'type':'binary',
        'datas': base64.b64encode(final_xml.encode("utf8")),
        'public':True,
        'mimetype':'application/xml',
        # 'datas_fname':name+".xml"
        })
        self.env['fb.attachment.mapping'].search([('fb_shop','=',self.id),('latest','=',True)]).write({'latest':False})


        self.env['fb.attachment.mapping'].create({
        'fb_shop':self.id,
        'attachment_id':_attach_1.id,
        'latest':True,
        'updated':False
        })

    def create_xml(self, **kw):
        final_xml=self._get_dict()
        self._store_data(final_xml)
        message="Attachment is Created Please enter the following URL to the Facebook Catalog :-"+self.feed_url
        if not kw.get('cron'):
            _logger.info("Hey Attachment is Created Manually")
            return self.env['wk.wizard.message'].genrated_message(message=message,name='Message')
        else:
            _logger.info("Hey!!! Cron of FB Shop Executed and the Attachment is created")

    def create_cron(self):
        if(not self.crone_id):
            model_id=self.env['ir.model'].search([('name','=','fb.facebook.shop')],limit=1).id
            name=str(self.id)+":"+self.name
            code="env['fb.facebook.shop'].browse("+str(self.id)+").create_xml(cron=True)"
            crone_rec=self.env["ir.cron"].sudo().create({
                "name":name,
                "model_id":model_id,
                "state":"code",
                "code":code,
                "doall":False
                })
            self.crone_id=crone_rec.id
        else:
            raise UserError("More Than One Cron Cannot Be Created")

        pass
