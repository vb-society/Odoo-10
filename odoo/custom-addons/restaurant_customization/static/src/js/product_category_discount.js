odoo.define('restaurant_customization.product_category_discount', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var popups = require('point_of_sale.popups');
var models = require('point_of_sale.models');
var DB = require('point_of_sale.DB');
var gui = require('point_of_sale.gui');
var core = require('web.core');
var Model = require('web.DataModel');

var QWeb = core.qweb;
var _t = core._t;

models.PosModel.prototype.models.push({
    model:  'pos.category.discount',
    fields: ['pos_category_id',
             'is_allow',
             'product_id',
             'id'
             ],
    loaded: function(self,category_wise_discount){
        self.db.add_pos_category_discount(category_wise_discount);
    },
});

models.PosModel.prototype.models.push({
    model:  'pos.discount.type',
    fields: ['name',
             ],
    loaded: function(self,discount_types){
        self.db.add_pos_discount_types(discount_types);
    },
});


var DiscountCategoryButton = screens.ActionButtonWidget.extend({
    template: 'DiscountCategoryButton',
    button_click: function(){
        var self = this;
        var categ_select = null
        var def  = new $.Deferred();
        var order = this.pos.get('selectedOrder');
        var list = [];

        for (var i in self.pos.db.category_wise_discount_by_id) {
            var product_categ = self.pos.db.category_wise_discount_by_id[i];
            if (product_categ.is_allow){
                list.push({
                    'label': product_categ.pos_category_id[1],
                    'item':  product_categ,
                });
            }
        }

        if(order.get_orderlines().length <= 0){
            self.gui.show_popup('error', {
                'title':_t('Empty Order'),
                'body': _t('There must be at least one product in your order to apply discount.'),
            });
        }
        else{
            this.gui.show_popup('selection',{
                'title': _t('Select Product Category'),
                list: list,
                confirm: function(categ_select){ def.resolve(categ_select); },
                cancel:  function(){ def.reject(); },
            });

            return def.then(function(categ_select){
                if (self.pos.user.pos_security_pin) {
                    return self.gui.ask_password(self.pos.user.pos_security_pin).then(function(){
                        self.gui.show_popup('number',{
                            'title': 'Discount Percentage',
                            'value': self.pos.config.discount_product_category,
                            'confirm': function(val) {
                                val = Math.round(Math.max(0,Math.min(100,val)));
                                self.apply_discount(val,categ_select);
                            },
                        });
                    });
                }
                else{
                    self.gui.show_popup('error', {
                        'title':_t('Discount could not be applied'),
                        'body': _t('You must have to set password to apply discount.'),
                    });
                }
            });
        }
    },
    apply_discount: function(pc,categ_select) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        var product  = this.pos.db.get_product_by_id(categ_select.product_id[0]);
        // Remove existing discounts
        var i = 0;
        while ( i < lines.length ) {
            if (lines[i].get_product() === product) {
                order.remove_orderline(lines[i]);
            } else {
                i++;
            }
        }

        // Add discount
        //product.display_name = categ_select.name+' '+'Discount';
            var discount = - pc / 100.0 * order.get_total_for_category_with_tax(categ_select.pos_category_id[0]);
        if( discount < 0 ){
            order.add_product(product, { price: discount });
        }
    },
});

screens.define_action_button({
    'name': 'discount by Product category',
    'widget': DiscountCategoryButton,
    'condition': function(){
        return this.pos.config.category_discount && this.pos.config.pos_category_discount_ids;
    },
});

screens.NumpadWidget.include({
    start: function() {
        this._super();
        this.$el.find('.disc-button').click(_.bind(this.clickDisc, this));
        this.$el.find('.price-button, .qty-button, .disc-button').click(_.bind(this.clickBillChangeMode, this));
    },
    clickDisc: function(event) {
        var order = this.pos.get('selectedOrder');
        var self = this;
        $('.selected-mode').removeClass('selected-mode');
        if (this.state.get('mode') === 'discount'){
            this.state['mode'] = 'quantity';
            self.state.changeMode(this.state['mode']);
        }
        if(order.get_orderlines().length <= 0){
            this.gui.show_popup('error', {
                'title':_t('Empty Order'),
                'body': _t('There must be at least one product in your order to apply discount.'),
            });
        }
        else{
            if (this.pos.user.pos_security_pin) {
                return this.gui.ask_password(this.pos.user.pos_security_pin).then(function(){
                    var newMode = event.currentTarget.attributes['data-mode'].nodeValue;
                    return self.state.changeMode(newMode);
                });
            }
            else{
                this.gui.show_popup('error', {
                    'title':_t('Discount could not be applied'),
                    'body': _t('You must have to set password to apply discount.'),
                });
            }
        }
    },
    clickBillChangeMode: function(event) {
        var self = this;
        if (self.state.get('mode') === 'discount'){
            $('.selected-mode').removeClass('selected-mode');
            self.state['mode'] = 'quantity';
            self.state.changeMode(this.state['mode']);
        }
        if (self.state.get('mode') === 'price'){
            $('.selected-mode').removeClass('selected-mode');
            self.state['mode'] = 'quantity';
            self.state.changeMode(this.state['mode']);
        }
        var newMode = event.currentTarget.attributes['data-mode'].nodeValue;
        if(this.pos.get_order().first_bill === "true"){
            if (this.pos.user.pos_security_pin) {
                return this.gui.ask_password(this.pos.user.pos_security_pin).then(function(){
                    return self.state.changeMode(newMode);
                });
            }
            else{
                this.gui.show_popup('error', {
                    'title':_t('Changes could not be applied'),
                    'body': _t('You must have to set password to apply changes.'),
                });
            }
        }
        else{
            return self.state.changeMode(newMode);
        }
    },
    clickDeleteLastChar: function() {
        var self = this;
        if(this.pos.get_order().first_bill === "true"){
            if (this.pos.user.pos_security_pin) {
                return this.gui.ask_password(this.pos.user.pos_security_pin).then(function(){
                    return self.state.deleteLastChar();
                });
            }
            else{
                this.gui.show_popup('error', {
                    'title':_t('Changes could not be applied'),
                    'body': _t('You must have to set password to apply changes.'),
                });
            }
        }
        else{
           return self.state.deleteLastChar(); 
        }
    },
});

screens.ProductScreenWidget.include({
    start: function () {
        this._super();
        $('.js_discount').remove();
        $('.order-printbill').remove();
        $('.note_btn').remove();
        $('.transfer_btn').remove();
    },
    click_product: function(product) {
        var order = this.pos.get_order();
        var self = this;
        if(order.first_bill === "true"){
            if (this.pos.user.pos_security_pin) {
                return this.pos.gui.ask_password(this.pos.user.pos_security_pin).then(function(){
                   if(product.to_weight && self.pos.config.iface_electronic_scale){
                    this.gui.show_screen('scale',{product: product});
                    }else{
                        self.pos.get_order().add_product(product);
                    } 
                });
            }
            else{
                this.pos.gui.show_popup('error', {
                    'title':_t('Changes could not be applied'),
                    'body': _t('You must have to set password to apply changes.'),
                });
            }
        }
        else if(order.order_type == false && order.chair_count == 0){
            this.pos.gui.show_popup('confirm', {
                'title':_t('Please select chairs for this order'),
                'body': _t('Order could not be placed until chairs are not get selected'),
            });
        }
        else{
            if(product.to_weight && self.pos.config.iface_electronic_scale){
                this.gui.show_screen('scale',{product: product});
            }else{
                self.pos.get_order().add_product(product);
            } 
        }  
    },
});

var DiscountButton = screens.ActionButtonWidget.extend({
    template: 'DiscountButton1',
    button_click: function(){
        var self = this;
        var list = [];
        var discount_type = null
        var def  = new $.Deferred();
        var order = this.pos.get('selectedOrder');

        for (var i in self.pos.db.discount_type_by_id) {
            var discount_type = self.pos.db.discount_type_by_id[i];
            list.push({
                'label': discount_type.name,
                'item':  discount_type,
            });
        }

        if(order.get_orderlines().length <= 0){
            self.gui.show_popup('error', {
                'title':_t('Empty Order'),
                'body': _t('There must be at least one product in your order to apply discount.'),
            });  
        }
        else{
            if (self.pos.user.pos_security_pin) {
                return self.gui.ask_password(self.pos.user.pos_security_pin).then(function(){
                    self.gui.show_popup('selection',{
                        'title': _t('Discount Types'),
                        list: list,
                        confirm: function(discount_type){
                            self.gui.show_popup('number',{
                                'title': 'Discount Percentage',
                                'value': self.pos.config.discount_pc,
                                'confirm': function(val) {
                                    val = Math.round(Math.max(0,Math.min(100,val)));
                                    self.apply_discount(val, discount_type);
                                },
                            });
                        },
                        cancel:  function(){ def.reject(); },
                    });
                });
            }
            else{
                self.gui.show_popup('error', {
                    'title':_t('Discount could not be applied'),
                    'body': _t('You must have to set password to apply discount.'),
                });
            }
        }
    },
    apply_discount: function(pc, discount_type) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        var product  = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);

        // Remove existing discounts
        var i = 0;
        while ( i < lines.length ) {
            if (lines[i].get_product() === product) {
                order.remove_orderline(lines[i]);
            } else {
                i++;
            }
        }

        // Add discount
        var discount = - pc / 100.0 * order.get_total_with_tax();
        if( discount < 0 ){
            order.add_product(product, { price: discount, disc_type: discount_type});
        }
    },
});

screens.define_action_button({
    'name': 'discount1',
    'widget': DiscountButton,
    'condition': function(){
        return this.pos.config.iface_discount && this.pos.config.discount_product_id;
    },
});

models.Order = models.Order.extend({
    hasChangesToPrintBill: function(){
        var printers = this.pos.printers;
        for(var i = 0; i < printers.length; i++){
            var changes = this.computeChanges(printers[i].config.product_categories_ids);
            if ( changes['new'].length > 0 || changes['cancelled'].length > 0){
                return true;
            }
        }
        return false;
    },
});

var PrintBillButton = screens.ActionButtonWidget.extend({
    template: 'PrintBillButton1',
    print_xml: function(){
        var order = this.pos.get('selectedOrder');
        var self = this;
        if(order.get_orderlines().length > 0){
            var receipt = order.export_for_printing();
            receipt.bill = true;
            self.pos.proxy.print_receipt(QWeb.render('BillReceipt',{
                receipt: receipt, widget: self, pos: self.pos, order: order,
            }));
        }
    },
    button_click: function(){
        var order = this.pos.get('selectedOrder');
        order.set_first_bill("true");
        if (!this.pos.config.iface_print_via_proxy) {
            this.gui.show_screen('bill');
        } else {
            this.print_xml();
        }
    },
});

screens.define_action_button({
    'name': 'print_bill1',
    'widget': PrintBillButton,
    'condition': function(){ 
        return this.pos.config.iface_printbill;
    },
});

var OrderlineNoteButton = screens.ActionButtonWidget.extend({
    template: 'OrderlineNoteButton1',
    button_click: function(){
        var order = this.pos.get_order()
        var line = order.get_selected_orderline();
        var self = this;
        if (line) {
            if(order.first_bill === "true"){
                if (this.pos.user.pos_security_pin) {
                    return this.pos.gui.ask_password(this.pos.user.pos_security_pin).then(function(){
                        self.gui.show_popup('textarea',{
                            title: _t('Add Note'),
                            value:   line.get_note(),
                            confirm: function(note) {
                                line.set_note(note);
                            },
                        });
                    });
                }
                else{
                    self.pos.gui.show_popup('error', {
                        'title':_t('Changes could not be applied'),
                        'body': _t('You must have to set password to apply changes.'),
                    });
                }
            }
            else{
                self.gui.show_popup('textarea',{
                    title: _t('Add Note'),
                    value:   line.get_note(),
                    confirm: function(note) {
                        line.set_note(note);
                    },
                }); 
            }
        }
    },
});

screens.define_action_button({
    'name': 'orderline_note1',
    'widget': OrderlineNoteButton,
    'condition': function(){
        return this.pos.config.iface_orderline_notes;
    },
});



/* ********************************************************
Overload: point_of_sale.PosDB
- Add to local storage Product Templates Data.
*********************************************************** */
    DB.include({
        init: function(options){
            this.category_wise_discount_by_id = {};
            this.discount_type_by_id = {};
            this._super(options);

        },

        add_pos_category_discount: function(category_wise_discount){
            for(var i=0, len = category_wise_discount.length; i < len; i++){
                this.category_wise_discount_by_id[category_wise_discount[i].id] = category_wise_discount[i];
            }
        },

        add_pos_discount_types: function(discount_types){
            for(var i=0, len = discount_types.length; i < len; i++){
                this.discount_type_by_id[discount_types[i].id] = discount_types[i];
            }
        }
    });
});