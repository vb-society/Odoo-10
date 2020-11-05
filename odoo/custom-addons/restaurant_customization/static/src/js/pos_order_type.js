odoo.define('restaurant_customization.pos_order_type', function (require) {
"use strict";
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    var floors = require('pos_restaurant.floors');
    var screens = require('point_of_sale.screens');
    var ScreenWidget = screens.ScreenWidget;
    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var chrome = require('point_of_sale.chrome')
    var Model = require('web.DataModel');
    var _super_posmodel = models.PosModel.prototype;
    // START LOAD FIELDS FROM USERS AND SET USERS AND USER
    
    models.load_models({
        model:  'res.users',
        fields: ['allow_outdoor_order','is_delivery_boy', 'is_cashier', 'is_waiter','allow_outdoor_order_delivery'],
        loaded: function(self,users){
            for (var i = 0; i < users.length; i++) {
                var user = _.find(self.users, function(el){ return el.id == users[i].id; });
                if (user) {
                    _.extend(user,users[i]);
                }
            }
        }
    });

    // END LOAD FIELDS FROM USERS AND SET USERS AND USER
    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        init: function(options){
            _super_posmodel.init.apply(this,arguments);
            this.current_partner_id = this.current_partner_id || false;
        },
        set_current_partner_id: function(partner_id){
            this.current_partner_id = partner_id;
            this.trigger('change', this);
        },

        // ADD ORDER IN TABLE SCREEN, IF ORDER IS NOT ALREADY SELECTED.
        set_table: function(table) {
            var self = this;
            if (!table) {
                this.set_order(null);
            } else if (this.order_to_transfer_to_different_table) {
                this.order_to_transfer_to_different_table.table = table;
                this.order_to_transfer_to_different_table.save_to_db();
                this.order_to_transfer_to_different_table = null;
                this.set_table(table);

            } else {
                this.table = table;
                var orders = this.get_order_list();
                var t_orders = []
                for (var i = 0; i < orders.length; i++) {
                    if ( orders[i].table === this.table) {
                        t_orders.push(orders[i]);
                    }
                }
                if (t_orders.length) {
                    this.set_order(t_orders[0]);
                } else {
                    this.add_new_order();
                }
            }
        },

        // ADD ALL TABLES ORDERS ON ORDER SCREEN.
        get_order_list: function() {
            var orders = this.get('orders').models;
            if (!this.config.iface_floorplan) {
                return orders;
            } else {
                var t_orders = [];
                for (var i = 0; i < orders.length; i++) {
                    if (orders[i].table === this.table){
                        t_orders.push(orders[i]);
                    }
                      else if(orders[i].order_type == 'take_away' || orders[i].order_type == 'delivery'){
                        t_orders.push(orders[i]);
                    }
                }
                return t_orders;
            }
        },

        get_unpaid_deliver_order_list: function() {
            var orders = this.get_order_list()
            var unpaid_dos = []
            for (var i = 0; i < orders.length; i++) {
                if (orders[i].order_type === 'delivery'){
                    unpaid_dos.push(orders[i]);
                }
            }
            return unpaid_dos.length
        },

        get_delivery_boy: function() {
            var order = this.get_order();
            if(order)
                return order.get_delivery_boy();
            return null;
        },

        get_delivery_boy_name:function(){
            var order = this.get_order();
            if(order)
                return order.get_delivery_boy_name();
            return null;
        },

        get_chair_count: function(table) {
            var orders = this.get_table_orders(table);
            var count  = 0;
            for (var i = 0; i < orders.length; i++) {
                count += orders[i].get_chair_count();
            }
            return count;
        },

        get_selected_chairs: function(table) {
            var self = this;
            var orders = self.get_table_orders(table);
            var chairs  = [];
            for (var i = 0; i < orders.length; i++) {
                if(orders[i].order_chairs){
                    $.each( orders[i].order_chairs, function( k, v ){
                        chairs.push(v)
                    });
                }
            }
            chairs = chairs.filter(function(elem, index, self) {
                return index == self.indexOf(elem);
            });
            return chairs;
        },
        get_state: function(order){
            if (order){
                new Model('pos.order').call('get_state', [order.name]).then(function (state) {
                    order['state'] = state;
                });

            }
        }
    });

    models.load_fields("pos.order", ['order_type', 'delivery_boy', 'state']);
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this,arguments);
            this.order_type = this.order_type || false;
            this.delivery_boy = this.delivery_boy || false;
            this.first_bill = this.first_bill || false;
            this.chair_count = this.chair_count || 0;
            this.order_chairs = this.order_chairs || [];
            this.state = this.state ;
            this.status = this.status;
            this.save_to_db();
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this,arguments);
            this.order_type = json.order_type || false;
            this.delivery_boy = json.delivery_boy || false;
            this.first_bill = json.first_bill || false;
            this.chair_count = json.chair_count || 0;
            this.order_chairs = json.order_chairs || [];
            this.state = json.state
            this.status = json.status
        },
        set_order_type: function(order_type){
            this.order_type = order_type;
            this.trigger('change', this);
        },
        set_delivery_boy: function(user){
            this.delivery_boy = user;
            this.trigger('change', this);
        },
        get_delivery_boy: function(){
            return this.delivery_boy;
        },
        get_delivery_boy_name:function(){
            var user = this.get_user_by_id(this.delivery_boy);
            return (user && user.name) || false;
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            json.order_type = this.order_type;
            json.delivery_boy = this.get_delivery_boy();
            json.first_bill = this.first_bill
            json.chair_count = this.chair_count;
            json.order_chairs = this.order_chairs;
            json.state = this.state;
            json.status = this.status;
            return json;
        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this,arguments);
            json.chair_count = this.get_chair_count();
            json.state = this.state;
            return json;
        },
        get_user_by_id: function(user_id){
            if (user_id){
                for (var i in this.pos.users){
                    if (this.pos.users[i].id == user_id){
                        return this.pos.users[i];
                    }
                }
            }
        },
        set_first_bill: function(first_bill){
            this.first_bill = first_bill;
            this.trigger('change', this);
        },
        get_chair_count: function(){
            return this.chair_count;
        },
        set_chair_count: function(count) {
            this.chair_count = Math.max(count,0);
            this.trigger('change');
        },
        set_order_chairs: function(chairs) {
            this.order_chairs = chairs;
            this.trigger('change');
        },
        set_send_to_kitchen: function(is_send_to_kitchen) {
            this.is_send_to_kitchen = is_send_to_kitchen;
            this.trigger('change');
        },

        
    });

    //START TAKE AWAY AND DILIVER ORDER WIIDGET WITH BUTTON AND ORDER
    floors.FloorScreenWidget.include({
        renderElement: function(){
            var self = this;
            this._super();
            this.$('#take_away_btn').click(function(event){
                self.pos.table = null;
                var order = new models.Order({},{pos: self.pos});
                order.set_order_type('take_away');
                self.pos.get('orders').add(order);
                self.pos.set('selectedOrder',order);
            });
            this.$('#delivery_btn').click(function(event){
                self.pos.table = null;
                var order = new models.Order({},{pos: self.pos});
                order.set_order_type('delivery');
                self.pos.get('orders').add(order);
                self.pos.set('selectedOrder',order);
            });
            this.$('#order_screen').click(function(event){
                window.location.href = '/orderscreen';
            });
            this.$('#kitchen_screen').click(function(event){
                window.location.href = '/kitchenscreen';
            });
        },
    });

    //CHANGE FLOOR(TABLE) VIEW BY PARTITION OF ALOCATED CHAIRS
    floors.TableWidget.include({
        // Status for display color code for pending payment
        get_table_order_status: function(table) {
           
            return true;
    },
        // The table's positioning is handled via css absolute positioning,
        // which is handled here.
        table_style: function(){
            var table = this.table;
            function unit(val){ return '' + val + 'px'; }
            var style = {
                'width':        unit(table.width),
                'height':       unit(table.height),
                'line-height':  unit(table.height),
                'margin-left':  unit(-table.width/2),
                'margin-top':   unit(-table.height/2),
                'top':          unit(table.position_v + table.height/2),
                'left':         unit(table.position_h + table.width/2),
                'border-radius': table.shape === 'round' ?
                        unit(Math.max(table.width,table.height)/2) : '3px',
            };
            if (table.color) {
                style.background = table.color;
            }
            if (table.height >= 150 && table.width >= 150) {
                style['font-size'] = '32px';
            }

            return style;
        },
        renderElement: function(){
            var self = this;
            var orders = this.pos.get_table_orders(this.table);
            this.order_count    = orders.length;
            this.chairs_list    = orders;
            this.customer_count = this.pos.get_customer_count(this.table);
            this.shape          = this.table.shape;
            this.fill           = Math.min(1,Math.max(0,this.customer_count / this.table.seats));
            this.chair_count = this.pos.get_chair_count(this.table);
            this.chair_fill = Math.min(1,Math.max(0,this.chair_count / this.table.seats));
            this.notifications  = this.get_notifications();
            this._super();

            this.update_click_handlers();

            this.$el.on('dragstart', function(event,drag){ self.dragstart_handler(event,$(this),drag); });
            this.$el.on('drag',      function(event,drag){ self.dragmove_handler(event,$(this),drag); });
            this.$el.on('dragend',   function(event,drag){ self.dragend_handler(event,$(this),drag); });

            var handles = this.$el.find('.table-handle');
            handles.on('dragstart',  function(event,drag){ self.handle_dragstart_handler(event,$(this),drag); });
            handles.on('drag',       function(event,drag){ self.handle_dragmove_handler(event,$(this),drag); });
            handles.on('dragend',    function(event,drag){ self.handle_dragend_handler(event,$(this),drag); });
    },
    });

    var UnpaidDeliveryOrdersScreenWidget = ScreenWidget.extend({
        template: 'UnpaidDeliveryOrdersScreenWidget',

        init: function(parent, options){
            this._super(parent, options);
        },

        show: function(){
            var self = this;
            this._super();

            this.renderElement();

            this.$('.back').click(function(){
                self.pos.set_table(null);
            });

            var orders = this.pos.get_order_list()
            this.render_list(orders);

            this.$('.unpaid-do-list-contents').delegate('.unpaid_do_id','click',function(event){
                self.payment_click(event,$(this),$(this).data('uid'));
            });
        },

        render_list: function(orders){
            var contents = this.$el[0].querySelector('.unpaid-do-list-contents');
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
                if (orders[i].order_type === 'delivery'){
                    var orderline_html = QWeb.render('UnpaidDOLine',{widget: this, order:orders[i]});
                    var orderline = document.createElement('tbody');
                    orderline.innerHTML = orderline_html;
                    orderline = orderline.childNodes[1];
                    contents.appendChild(orderline);
                }
            }
        },

        payment_click: function(event,$line,uid){
            var order = this.get_order_by_uid(uid)
            this.pos.set('selectedOrder', order);
            this.pos.gui.show_screen('payment');
        },

        get_order_by_uid: function(uid) {
            var orders = this.pos.get_order_list();
            for (var i = 0; i < orders.length; i++) {
                if (orders[i].uid === uid) {
                    return orders[i];
                }
            }
            return undefined;
        },

        close: function(){
            this._super();
        },
    });

    gui.define_screen({name:'unpaid_deliveryorders', widget: UnpaidDeliveryOrdersScreenWidget});

    function isInArray(value, array) {  return array.indexOf(value) > -1;}

    var ChairPopupWidget = PopupWidget.extend({
        template: 'ChairPopupWidget',
        init: function (parent, options) {
            this._super(parent, options);
            this.chairs = [];
        },

        start: function(options) {
            var self = this;
            this._super();
            var matched_chairs = [];
            var selected_chairs = this.pos.get_selected_chairs(this.pos.table);
            if(options){
                var chairs = options.chairs;
                var order_chairs = this.pos.get_order().order_chairs;
                this.chairs = [];
                
                for(var i in chairs.sort()) {   
                    if(selected_chairs.sort().indexOf( chairs.sort()[i] ) > -1){
                        matched_chairs.push(chairs.sort()[i] );
                    }
                }
                
                for(var i=0; i<chairs.length;i++){
                    if(isInArray(chairs[i], matched_chairs)){
                        if(isInArray(chairs[i], order_chairs)){
                            this.chairs.push({
                                'label':chairs[i],
                                'selected':true,
                                'order_chair': true,
                            })
                        }
                        else{
                            this.chairs.push({
                                'label':chairs[i],
                                'selected':true,
                                'order_chair': false,
                            })   
                        }
                    }
                    else{
                        this.chairs.push({
                            'label':chairs[i],
                            'selected':false,
                            'order_chair': false,
                        })   
                    }
                }
            }
        },

        show: function(options){
            var self = this;
            
            this._super(options);
            this.inputbuffer = options.value;
            
            this.start(options);
            
            this.order_chairs = this.pos.get_order().order_chairs;
            var val1 = this.inputbuffer;
            var val2 = this.order_chairs;
            this.renderElement();
            this.$(".chair-button").click(function(){
                $(this).toggleClass('select')
                var total_chairs = $(".chair-button").length;
                var selected_chairs = $(".select").length;
                if($(this).hasClass('select')){
                    val1 += 1;
                    val2.push($(this).val())
                }
                else{
                    val1 -= 1;
                    val2.splice( $.inArray($(this).val(), val2), 1 );
                }
                self.set_value(val1, val2)
            });
            this.$(".select-all").click(function(){
                val1 = 0;
                val2 = [];
                $(this).toggleClass('all_selected')
                if($(this).hasClass('all_selected')){
                    $(this).text('Clear')
                    $(".not-select").addClass('select');
                }
                else{
                    $(this).text('All')
                    $(".not-select").removeClass('select');
                    $(".select").addClass('not-select');
                    $(".select").removeClass('select'); 
                }
                for(var i = 0; i < $(".select").length; i++){
                    val1 += 1;
                    val2.push($(".select")[i].value)
                }
                self.set_value(val1, val2)
            });
        },

        set_value: function(val1, val2){
            this.$('.value').text(val1);
            this.inputbuffer = val1;
            this.order_chairs = val2;
        },

        click_confirm: function(){
            this.gui.close_popup();
            if( this.options.confirm ){
                this.options.confirm.call(this,this.inputbuffer,this.order_chairs);
            }
            this.gui.screen_instances.floors.renderElement();
        },

    });

    gui.define_popup({name:'chairs', widget: ChairPopupWidget});

    floors.TableGuestsButton.include({
        chairs: function() {
            if (this.pos.get_order()) {
                return this.pos.get_order().chair_count;
            } else {
                return 0;
            }
        },
        button_click: function() {
            var self = this;
            var total_seats = this.pos.table.seats
            var chairs = [];
            for(var i = 0; i < total_seats; i++){
                var chr = String.fromCharCode(65 + i);
                chairs.push(chr)
            }
            
            this.gui.show_popup('chairs', {
                'title':  _t('Chair Selection'),
                'value':  this.pos.get_order().chair_count,
                'chairs': chairs,
                'confirm': function(value,order_chairs) {
                    self.pos.get_order().set_chair_count(value);
                    self.pos.get_order().set_order_chairs(order_chairs)
                    self.renderElement();
                    var order = self.pos.get_order();
                    if (order){
                        new Model('pos.order').call('update_chair', [order.name, value])
                    }
                },
            });
        }
    });

    chrome.OrderSelectorWidget.include({
        neworder_click_handler: function(){
            if(this.pos.table)
            {
                if(this.pos.table.seats == this.pos.get_chair_count(this.pos.table)){
                this.gui.show_popup('error',{
                    'title': _t('No free chairs are available'),
                });}
                else{this.pos.add_new_order();}
            }else{
                this.pos.set_table(null);
            }
        },
        renderElement: function(){
            var self = this;
            var order = this.pos.get_order();
            this._super();
            this.$('.get_unpaid_delivery').click(function(){
                self.pos.set('selectedOrder',false);
                self.pos.gui.show_screen('unpaid_deliveryorders');
            });
            if (this.pos.config.iface_floorplan) {
                if (order) {
                    if (this.pos.table == null && order.order_type != false) {
                        this.$('.orders').prepend(QWeb.render('BackToFloorScreen'));
                        this.$('.floor-button').click(function(){
                            self.pos.set_table(null);
                        });
                    }
                    this.$el.removeClass('oe_invisible');
                }else {
                    this.$el.addClass('oe_invisible');
                }
            }
        }
    });

    //END TAKE AWAY AND DILIVER ORDER WIIDGET WITH BUTTON AND ORDER

    // START ADD DELIVERY BOY OF ORDER
    screens.PaymentScreenWidget.include({

        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            setInterval(function () {
                self.renderElement();
            }, 1000);
        },


        click_set_delivery_boy: function(){
            var self = this;
            var user_list = [];
            for (var i in self.pos.users){
                var user = self.pos.users[i];
                if (self.pos.users[i].is_delivery_boy){
                    user_list.push({
                        'label':user.name,
                        'item':user.id
                    });
                }
            };
            self.pos.gui.show_popup('selection',{
                'title': 'Select Delivery Boy',
                list: user_list,
                confirm: function(user){
                    var order = this.posmodel.get_order();
                    order.set_delivery_boy(user);
                    self.renderElement();
                },
            });
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.js_set_delivery_boy').click(function(){
                self.click_set_delivery_boy();
            });
        },
        order_is_valid: function(force_validation) {
           var validate  = this._super(force_validation);
           var order = this.pos.get_order()
           if (order.order_type == 'delivery' && (!this.pos.get_order().delivery_boy)){
                validate = false;
                this.gui.show_popup('error',{
                    'title': _t('Please Add Delivery Boy'),
                    'body': _t('You need to select the deliveryboy before validate delivery order.'),
                });
           }
           return validate
        },
    })
    // END ADD DELIVERY BOY OF ORDER

    //START VALIDATION OF ADD CUSTOMER
    screens.ClientListScreenWidget.include({
        save_client_details: function(partner) {
            var self = this;
            var fields = {};
            this.$('.client-details-contents .detail').each(function(idx,el){
                    fields[el.name] = el.value || false;
            });
            if (!fields.street) {
                this.gui.show_popup('error',_t('A Customer street Is Required'));
                return;
            } 
            if(!fields.city){
                this.gui.show_popup('error',_t('A Customer City Is Required'));
                return;
            }
            if(!fields.country_id){
                this.gui.show_popup('error',_t('A Customer Country Is Required'));
                return;
            }
            if (!fields.phone){
                this.gui.show_popup('error',_t('A Customer Phone No. Is Required'));
                return;
            }
            self._super(partner)
        },
    });
    //END VALIDATION OF ADD CUSTOMER

    // START VALIDATION ON REDIRECT PAYMENT PAGE
    screens.ActionpadWidget.include({
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.pay').click(function(){
                var order = self.pos.get_order()
				new Model('pos.order').call('check_payment', [order.name]).then(function (payment) {
                    if(payment === true){
                        order.finalized = true;
                        order.pos.gui.show_screen('receipt');
                    }
                });
                if((order.order_type == 'take_away' || order.order_type == 'delivery')&& !order.get_client()){
                    self.gui.show_popup('error',{
                        'title': _t('Please select the Customer'),
                        'body':  _t('You need to select the customer before proceed for the payment.'),
                        cancel: function(){
                            self.gui.back()
                        },
                    });
                }
            });
        }
    }); 
    // END VALIDATION ON REDIRECT PAYMENT PAGE

    //START DISABLE CHANGE CASHIER
    chrome.UsernameWidget.include({
    template: 'UsernameWidget',
        click_username: function(){
            console.log("Override Set Cashier And Disable Change Cahier Functionality....")
        },
    });
    // END DISBAL CHANGE CASHIER

    // SET DELIVERY BOY ON POS SCREEN
    screens.ActionpadWidget.include({
        click_set_delivery_boy: function(){
            var self = this;
            var user_list = [];
            var order = self.pos.get_order();
            for (var i in self.pos.users){
                var user = self.pos.users[i];
                if (self.pos.users[i].is_delivery_boy){
                    user_list.push({
                        'label':user.name,
                        'item':user.id
                    });
                }
            };
            if (order.order_type && order.order_type === 'delivery'){
                self.pos.gui.show_popup('selection',{
                    'title': 'Select Delivery Boy',
                    list: user_list,
                    confirm: function(user){
                        order.set_delivery_boy(user)
                        setInterval(function () {
                            self.renderElement();
                        }, 1000);
                    },
                });
            }
            else {
                self.pos.gui.show_popup('error',{
                'title': _t('Error: Could not Set Delivery Boy'),
                'body': _t('Please set Order Type as Delivery to select Delivery Boy'),
            });}
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.set-delivery-boy').click(function(){
                self.click_set_delivery_boy();
            });
        },
    });
    // END DELIVERY BOY ON POS SCREEN
});
