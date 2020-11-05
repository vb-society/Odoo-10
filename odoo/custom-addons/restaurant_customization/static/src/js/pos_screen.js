odoo.define('restaurant_customization.pos_screen', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var pop_up = require('point_of_sale.popups');
var models = require('point_of_sale.models');
var core = require('web.core');
var splitbill = require('pos_restaurant.splitbill')
var Model = require('web.DataModel');
var DB = require('point_of_sale.DB');
var gui = require('point_of_sale.gui');
var _t  = require('web.core')._t;
var _super_posmodel = models.PosModel.prototype;
var QWeb = core.qweb;
var ActionButtonWidget = screens.ActionButtonWidget;

var _super_order = models.Order.prototype;

models.load_fields("pos.order.line", ['kitchecn_order_state', 'discount_type', 'line_id']);

models.PosModel = models.PosModel.extend({
    initialize: function () {
        var self = this;
        var res = _super_posmodel.initialize.apply(this, arguments)
        var order_states = []
        return res;
    },

    delete_current_order: function(){
        var order = this.get_order();
        var self = this;
        
        if (order) {
            order.destroy({'reason':'abandon'});
            new Model('pos.order').call('cancel_pos_order',[order.name]).then(function(flag_sucess){
                if (flag_sucess.sucess == true){
                    self.gui.show_popup('alert', {
                        title: _t('Order cancel from kitchen'),
                        body: _t("Order is cancelled Successfully!"),
                    });
                }
            });
        }
    },
    
});

var _super_order = models.Order.prototype;
models.Order = models.Order.extend({

    initialize: function() {
        _super_order.initialize.apply(this,arguments);
        this.is_send_to_kitchen = this.is_send_to_kitchen || false;
        this.save_to_db();
    },
    export_as_JSON: function() {
        var json = _super_order.export_as_JSON.apply(this,arguments);
        json.is_send_to_kitchen = this.is_send_to_kitchen;
        return json;
    },

    init_from_JSON: function(json) {
        _super_order.init_from_JSON.apply(this,arguments);
        this.is_send_to_kitchen = json.is_send_to_kitchen || false;
        if (json.partner_id) {
            _.each(this.pos.partners, function(partner) {
                if (partner.id == json.partner_id) {
                    self.partner_id = partner.name;
                }
            });
        }
    },

    build_line_resume: function(){
        var resume = {};
        this.orderlines.each(function(line){
            if (line.mp_skip) {
                return;
            }
            var line_hash = line.get_line_diff_hash();
            var qty  = Number(line.get_quantity());
            var note = line.get_note();
            var product_id = line.get_product().id;
            var disc = line.get_discount();
            var price = line.price
            if (typeof resume[line_hash] === 'undefined') {
                resume[line_hash] = {
                    qty: qty,
                    note: note,
                    product_id: product_id,
                    product_name_wrapped: line.generate_wrapped_product_name(),
                    disc: disc,
                    price: price,
                };
            } else {
                resume[line_hash].qty += qty;
            }

        });
        return resume;
    },

    // coumpute changes override
    computeChanges: function(categories){
        var current_res = this.build_line_resume();
        var old_res     = this.saved_resume || {};
        var json        = this.export_as_JSON();
        var add = [];
        var rem = [];
        var price_change = false;
        var disc_change = false;
        var line_hash;

        for ( line_hash in current_res) {
            var curr = current_res[line_hash];
            var old  = old_res[line_hash];
            if (typeof old !== 'undefined'){
                if(curr.disc != old.disc)
                    disc_change = true
                if(curr.price != old.price)
                    price_change = true
            }
            if (typeof old === 'undefined') {
                add.push({
                    'id':       curr.product_id,
                    'name':     this.pos.db.get_product_by_id(curr.product_id).display_name,
                    'name_wrapped': curr.product_name_wrapped,
                    'note':     curr.note,
                    'qty':      curr.qty,
                });
            } else if (old.qty < curr.qty) {
                add.push({
                    'id':       curr.product_id,
                    'name':     this.pos.db.get_product_by_id(curr.product_id).display_name,
                    'name_wrapped': curr.product_name_wrapped,
                    'note':     curr.note,
                    'qty':      curr.qty - old.qty,
                });
            } else if (old.qty > curr.qty) {
                rem.push({
                    'id':       curr.product_id,
                    'name':     this.pos.db.get_product_by_id(curr.product_id).display_name,
                    'name_wrapped': curr.product_name_wrapped,
                    'note':     curr.note,
                    'qty':      old.qty - curr.qty,
                });
            }
        }

        for (line_hash in old_res) {
            if (typeof current_res[line_hash] === 'undefined') {
                var old = old_res[line_hash];
                rem.push({
                    'id':       old.product_id,
                    'name':     this.pos.db.get_product_by_id(old.product_id).display_name,
                    'name_wrapped': old.product_name_wrapped,
                    'note':     old.note,
                    'qty':      old.qty,
                });
            }
        }

        if(categories && categories.length > 0){
            // filter the added and removed orders to only contains
            // products that belong to one of the categories supplied as a parameter

            var self = this;

            var _add = [];
            var _rem = [];

            for(var i = 0; i < add.length; i++){
                if(self.pos.db.is_product_in_category(categories,add[i].id)){
                    _add.push(add[i]);
                }
            }
            add = _add;

            for(var i = 0; i < rem.length; i++){
                if(self.pos.db.is_product_in_category(categories,rem[i].id)){
                    _rem.push(rem[i]);
                }
            }
            rem = _rem;
        }

        var d = new Date();
        var hours   = '' + d.getHours();
            hours   = hours.length < 2 ? ('0' + hours) : hours;
        var minutes = '' + d.getMinutes();
            minutes = minutes.length < 2 ? ('0' + minutes) : minutes;

        return {
            'new': add,
            'cancelled': rem,
            'table': json.table || false,
            'floor': json.floor || false,
            'name': json.name  || 'unknown order',
            'time': {
                'hours':   hours,
                'minutes': minutes,
            },
            'order_type': this.order_type,
            'disc': disc_change,
            'price': price_change,
        };

    },

    hasChangesToPrint: function(){
        var printers = this.pos.printers;
        for(var i = 0; i < printers.length; i++){
            var changes = this.computeChanges(printers[i].config.product_categories_ids);
            if ( changes['new'].length > 0 || changes['disc'] == true || changes['price'] == true){
                return true;
            }
            if (changes['cancelled'].length > 0 && changes['new'].length == 0 && changes['disc'] == false && changes['price'] == false){
                return false;
            }
        }
        return false;
    },
    add_product: function(product, options) {
        if(this._printed){
            this.destroy();
            return this.pos.get_order().add_product(product, options);
        }
        this.assert_editable();
        options = options || {};
        var attr = JSON.parse(JSON.stringify(product));
        attr.pos = this.pos;
        attr.order = this;
        var line = new models.Orderline({}, {pos: this.pos, order: this, product: product});
        if(options.quantity !== undefined){
            line.set_quantity(options.quantity);
        }

        if(options.price !== undefined){
            line.set_unit_price(options.price);
        }

        //To substract from the unit price the included taxes mapped by the fiscal position
        this.fix_tax_included_price(line);

        if(options.discount !== undefined){
            line.set_discount(options.discount);
        }

        if(options.extras !== undefined){
            for (var prop in options.extras) { 
                line[prop] = options.extras[prop];
            }
        }

        if(options.disc_type !== undefined){
            line.discount_type = options.disc_type.id;
        }

        var last_orderline = this.get_last_orderline();
        if( last_orderline && last_orderline.can_be_merged_with(line) && options.merge !== false){
            last_orderline.merge(line);
        }else{
            this.orderlines.add(line);
        }
        this.select_orderline(this.get_last_orderline());

        if(line.has_product_lot){
            this.display_lot_popup();
        }
    },


    // For Reprint Kot

    compute_all_product: function(categories){
        var current_res = this.build_line_resume();
        var old_res     = this.saved_resume || {};
        var json        = this.export_as_JSON();
        var add = [];
        var rem = [];
        var line_hash;

        for ( line_hash in current_res) {
            var curr = current_res[line_hash];
            var old  = old_res[line_hash];
                add.push({
                    'id':       curr.product_id,
                    'name':     this.pos.db.get_product_by_id(curr.product_id).display_name,
                    'name_wrapped': curr.product_name_wrapped,
                    'note':     curr.note,
                    'qty':      curr.qty,
                });
          
        }
  

        var d = new Date();
        var hours   = '' + d.getHours();
            hours   = hours.length < 2 ? ('0' + hours) : hours;
        var minutes = '' + d.getMinutes();
            minutes = minutes.length < 2 ? ('0' + minutes) : minutes;
        return {
            'old': add,
            'new':[],
            'order_type':this.order_type,
            'reprint_kot': true,
            'cancelled':[],
            'table': json.table || false,
            'floor': json.floor || false,
            'name': json.name  || 'unknown order',
            'time': {
                'hours':   hours,
                'minutes': minutes,
            },
        };
        
    },

    print_all: function(){
        var self = this;
        if (self.pos.attributes.selectedOrder.orderlines.models == '') {
                self.pos.gui.show_popup('alert', {
                    title: _t('Warning !'),
                    body: _t('Can not create order which have no order line.'),
                });
                return false;
        }else{

            var printers = this.pos.printers;
            for(var i = 0; i < printers.length; i++){
                var all_orderline = this.compute_all_product(printers[i].config.product_categories_ids);

                var receipt = QWeb.render('OrderChangeReceipt',{changes:all_orderline, widget:this});
                    printers[i].print(receipt);
                
            }
        }
    },
});


var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options) {
            this.discount_type = this.discount_type || false;
            // // debugger
            // if (options.json){
            // }
            _super_order_line.initialize.call(this,attr,options);
            this.line_id =  this.line_id || '';

           
        },
        init_from_JSON: function(json) {
            _super_order_line.init_from_JSON.apply(this,arguments);
            var self = this;
            this.line_id = json.line_id;
            self.kitchecn_order_state = json.kitchecn_order_state
            self.discount_type = json.discount_type
        },
        set_line_id: function(line_id) {
            this.line_id = line_id;
            this.trigger('change', this);
        },
        get_line_id: function(line_id){
            return this.line_id;
        },
        export_as_JSON: function(json) {
            var json = _super_order_line.export_as_JSON.call(this);
            var self = this;
            json.line_id = this.line_id;
            json.kitchecn_order_state = 'in_queue';
            json.note = self.note;
            json.discount_type = self.discount_type;
            return json;
        },
        can_be_merged_with: function(orderline) {
        if (orderline.get_line_id() !== this.get_line_id()) {
                return false;
            } else {
                return _super_order_line.can_be_merged_with.apply(this,arguments);
            }
        },
        clone: function(){
            var orderline = _super_order_line.clone.call(this);
            orderline.line_id = this.line_id;
            orderline.order_id = this.order_id;
            return orderline;
        },
       
        set_quantity: function(quantity){
            _super_order_line.set_quantity.apply(this, arguments);
            if(quantity === 'remove'){
                if (this.line_id){
                    // orderline  is cancel from backend 
                    new Model('pos.order.line').call('cancel_order_line',[this.line_id]);
                }
            }
        },
    });

var _super_numpadstate = models.NumpadState.prototype;
models.NumpadState = models.NumpadState.extend({

    deleteLastChar: function() {
        if(this.get('buffer') === ""){
            if(this.get('mode') === 'quantity'){
                this.trigger('set_value','remove');
            }else{
                this.trigger('set_value',this.get('buffer'));
            }
        }else{
            if(this.get('mode') === 'quantity'){
                this.trigger('set_value','remove');
            }else{
                var newBuffer = this.get('buffer').slice(0,-1) || "";
                this.set({ buffer: newBuffer });
                this.trigger('set_value',this.get('buffer'));
            }
        }
    },
});

screens.ProductScreenWidget.include({
        start: function() {
            var self = this;
            this._super();
         
            this.$(".order_status_button").on('click', function() {
                console.log("clickkkkkkkkkkkkkkkkkk");
                self.view_order_status();
            });
        },

        view_order_status: function() {
            var self = this;
            var def  = new $.Deferred();

            var currentOrder = self.pos.get('selectedOrder');
            var list = [];
            //Check for order line before show order status
            if (self.pos.attributes.selectedOrder.orderlines.models == '') {
                self.gui.show_popup('alert', {
                    title: _t('Warning !'),
                    body: _t('No Order lines found for order status.'),
                });
                return false;
            }
            else{
                new Model('pos.order').call('compute_status', [currentOrder.name]).then(function (order_data) {
                    var get_order = order_data[currentOrder.name]
                    if (get_order){
                        for (var i = 0; i < get_order.length; i++) {
                            list.push({
                                'label': get_order[i][0]+' (' + get_order[i][1]+')',
                            });
                                
                        }
                        self.gui.show_popup('selection', {
                            title: _t('Order Status'),
                            list: list,
                            warning_icon: true,
                            cancel:  function(){ def.reject(); },
                        });
                    }
                    else{
                        //Display alert that order is not found in kitchen
                        self.gui.show_popup('alert', {
                        title: _t('Warning !'),
                        body: _t('Please send order to kitchen first.'),
                    });
                    return false;

                    }
                }); 
            }
        },
    });
    var SubmitOrderButton1 = screens.ActionButtonWidget.extend({
        'template': 'SubmitOrderButton1',        
        button_click: function(){
            var self = this;
            if (self.pos.attributes.selectedOrder.orderlines.models == '') {
                self.gui.show_popup('alert', {
                    title: _t('Warning !'),
                    body: _t('Can not create order which have no order line.'),
                });
                return false;
            }else {
                var order = [];
                self.pos.get_order().is_send_to_kitchen = true;
                var current_order = this.pos.get_order();
                var posOrderModel = new Model('pos.order');
                current_order['chair_count'] = current_order.chair_count;
                order.push({
                    'data': current_order.export_as_JSON()
                })
                posOrderModel.call('create_from_ui', [order,true]).then(function(callback) {
                    if (callback[2]){
                        var update_vals = [];
                        if (callback[1].is_note_update){
                            update_vals.push('Note')
                        }
                        if(callback[1].is_qty_update){
                            update_vals.push('Quantity')
                        }
                        if (callback[1].is_discount_update){
                            update_vals.push('Discount')
                        }
                        if (callback[1].is_price_update){
                            update_vals.push('Price')
                        }
                        if (callback[1].is_note_update){
                            update_vals.push('chair_count')
                        }

                        if (update_vals.length >= 1){
                            var warning = "Order";
                            for (var i = 0; i < update_vals.length; i++) {
                                if (i == 0){
                                   warning += " "+update_vals[i] 
                                }
                                if (update_vals.length - 1 != i && i > 0){
                                   warning += ", "+update_vals[i]     
                                }
                                if(update_vals.length - 1 == i){
                                    warning += " and "+update_vals[i]    
                                }
                            }
                        }
                    }
                    if(callback[1].length > 0){
                        // current_order.attributes.id = callback[0];
                        for (var idx in current_order.orderlines.models) {
                            current_order.orderlines.models[idx].line_id = callback[1][callback[1].length-1][idx];
                            current_order.orderlines.models[idx].set_line_id(callback[1][callback[1].length-1][idx]);
                        }
                    }
                    self.gui.show_popup('alert', {
                        title: _t('Successful'),
                        warning_icon: false,
                        body: _t('Order is received successfully!'),
                    })
                    var order = self.pos.get_order();
                    if(order && order.hasChangesToPrint()){
                        order.printChanges();
                        order.saveChanges();
                    }
                }, function(err, event) {
                    event.preventDefault();
                });
            }
        },    
    });    

    //Reprint kot
    var reprint_kot = screens.ActionButtonWidget.extend({
        'template': 'reprint_kot',        
        button_click: function(){
            var self = this;
            var order = self.pos.get_order();
            order.print_all();

            
         
        },
    });

    screens.define_action_button({
        'name': 'Reprint Kot',
        'widget': reprint_kot,
        'condition': function() {
            return this.pos.printers.length;
        },
    });

    screens.define_action_button({
        'name': 'submit_order1',
        'widget': SubmitOrderButton1,
        'condition': function() {
            return this.pos.printers.length;
        },
    });

    screens.OrderWidget.include({
        update_summary: function(event){
            var order = this.pos.get_order()
            this._super();
            var self = this;
            if(order){
                var changes = order.hasChangesToPrint();
                var skipped = changes ? false : this.pos.get_order().hasSkippedChanges();
                var buttons = this.getParent().action_buttons;

                if (buttons && buttons.submit_order1) {
                    buttons.submit_order1.highlight(changes);
                    buttons.submit_order1.altlight(skipped);
                }
                new Model('pos.order').call('check_payment', [order.name]).then(function (payment) {
                    if(payment === true){
                        order.finalized = true;
                        order.pos.gui.show_screen('receipt');
                    }
                });
            }
        },
    });

    screens.PaymentScreenWidget.include({
        finalize_validation: function() {
            var order = this.pos.get_order();
            this._super();
            if (order){
                var orderlines = order.get_orderlines();
                for(var i=0; i<orderlines.length; i++){
                    new Model('pos.order').call('splitbill_payment', [order.name,orderlines[i].line_id, orderlines[i].quantity])
                }
            }
        },
    });

    screens.ScreenWidget.include({
        renderElement: function(){
            this._super();
            var order = this.pos.get_order();
            if(order){
                new Model('pos.order').call('check_payment', [order.name]).then(function (payment) {
                    if(payment === true){
                        order.finalized = true;
                        order.pos.gui.show_screen('receipt');
                    }
                });
            }
        },
        show: function(){
            var order = this.pos.get_order();
            var self = this;
            this._super();
            if (order){
                var orderlines = order.get_orderlines();
                if (orderlines.length > 0){
                    new Model('pos.order').call('get_order', [orderlines[0].line_id]).then(function (chair) {
                        order['chair_count'] = chair
                    });
                }
            }
        }
    });
});