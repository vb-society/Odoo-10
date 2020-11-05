// pos_multi_session_odoo js
console.log("pos_multi_session_odoo.pos callleddddddddddddddddddddd")
odoo.define('pos_multi_session_odoo', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var session = require('web.session');
    var core = require('web.core');
    var Backbone = window.Backbone;
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var bus = require('bus.bus');
    var Model = require('web.DataModel');
    
    var exports = {};

    var QWeb = core.qweb;
	var _t = core._t;
	var is_new_order = true;

	var utils = require('web.utils');
	var round_di = utils.round_decimals;
	var round_pr = utils.round_precision;	


    /*
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            return json;
        },
    });
    */	



   // Load Models

   models.load_models({
        model: 'pos.multi.session',
        fields: ['name','pos_session_ids'],
        domain: null,
        loaded: function(self, pos_multi_session_sync) {
            //console.log("111111111111loadedddddddddddddddddddddddddddddddddddd",models);
            self.pos_multi_session_sync = pos_multi_session_sync;
            //console.log("***************self.pos_orderrrrrrrrrrrrrrrr", self.pos_multi_session_sync);
        },
    });
    
    
    // ProductListWidget start
    screens.ProductListWidget.include({
		init: function(parent, options) {
		    var self = this;
		    this._super(parent,options);
		    this.model = options.model;
		    this.productwidgets = [];
		    this.weight = options.weight || 0;
		    this.show_scale = options.show_scale || false;
		    this.next_screen = options.next_screen || false;

		    this.click_product_handler = function(){
		        var product = self.pos.db.get_product_by_id(this.dataset.productId);
		        console.log("clickeeeddddddddddddddddddddddddddddd",product);
		        options.click_product_action(product);
		    };

		},
   
	});
    // End ProductListWidget start


    // Orderline start
    var OrderlineSuper = models.Orderline;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options){
            var self = this;
            OrderlineSuper.prototype.initialize.apply(this, arguments);
            this.pos   = options.pos;
    		this.order = options.order;

			//this.product = options.product;
        	//this.price   = options.product.price;
        	    		
            this.sync_user = {}
            if (!this.order)
                //this.product = options.product;
                return;
            if (this.order.sync_test()){
                //this.product = options.product;
                this.sync_user['created'] = this.order.pos.sync_user_detail();
            }
            this.bind('change', function(line){
                if(this.order.just_printed){
                    //this.product = options.product;
                    line.order.trigger('change:sync')
                    return
                }
                if (self.order.sync_test() && !line.sync_selected_orderline){
                    line.sync_user['changed'] = line.order.pos.sync_user_detail();
                    //this.product = options.product;
                    line.order.sync_user['changed'] = line.order.pos.sync_user_detail();
                    var orderLines = line.order.orderlines;
                    //console.log("orderlinesssssssssssssssss",orderLines);
                    orderLines.trigger('change', orderLines); 
                    //console.log("changeeeeeeeeee orderlinesssssssssssssssss",orderLines);
                    line.order.trigger('change:sync')
                }
            })
            this.uid = this.order.generate_unique_id() + '-' + this.id;
        },

		clone: function(){
		    var orderline = new exports.Orderline({},{
		        pos: this.pos,
		        order: this.order,
		        product: this.product,
		        price: this.price,
		    });
		    orderline.order = null;
		    orderline.quantity = this.quantity;
		    orderline.quantityStr = this.quantityStr;
		    orderline.discount = this.discount;
		    orderline.price = this.price;
		    orderline.type = this.type;
		    orderline.selected = false;
		    return orderline;
		},

		/*set_custom_discount: function(discount){
		  this.stayStr = discount[0].discount;
		  console.log('SSSSSSSSSSTTTTTTTTTTTAAAAAAAAAAYYYYYYYYYYYY', this.stayStr)
		  this.trigger('change',this);
		},
		
		get_to_stay: function(){
		    console.log("2222222222222222 SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSs", this.stayStr)
		    return this.stayStr;
		},*/
    
		// returns the discount [0,100]%
		get_discount: function(){
		    return this.discount;
		},

		// changes the base price of the product for this orderline
		//set_unit_price: function(price){
		//    this.order.assert_editable();
		    //console.log("22222222222 priceeeeeeeeeeeeee", price);
		 //   this.price = round_di(parseFloat(price) || 0, this.pos.dp['Product Price']);
		    //console.log("22222222222 priceeeeeeeeeeeee", price);
		 //   this.trigger('change',this);
		//},
    
		// selects or deselects this orderline
        set_selected: function(){
            this.sync_selected_orderline = true;
            //console.log("22222222222 selectedddddddddddddddddddddddd");
            OrderlineSuper.prototype.set_selected.apply(this, arguments);
            //console.log("22222222222 selecteddddddddddddddddddddddd");
            this.sync_selected_orderline = false;
        },
            
        export_as_JSON: function(){
            var loaded = OrderlineSuper.prototype.export_as_JSON.apply(this, arguments);
            //console.log("111111111111 loadeddddddddddddddddddddddd", loaded);
            loaded.uid = this.uid;
            loaded.sync_user = this.sync_user;
            //console.log("22222222222 loadeddddddddddddddddddddddd", loaded);
            return loaded;
        }
    });
    // End Orderline start
    
        
    // Order start

   // exports.Orderline = Backbone.Model.extend ...
   /*
   var OrderSuper = models.Order;
    models.Order = models.Order.extend({

		init: function(parent, options) {
		    var self = this;
		    this._super(parent,options);

		    //this.set_staystr();

		},
		
    
    export_as_JSON: function() {
            var self = this;
            var loaded = OrderSuper.prototype.export_as_JSON.call(this);
            //loaded.service_charge = self.get_service_charge();
            //loaded.amount_total = self.get_service_charge() + self.get_total_with_tax();
            return loaded;
        },
   
    
    });
    */
    var OrderSuper = models.Order;
    models.Order = models.Order.extend({
        initialize: function(attributes, options){
            var self = this;
            options = options || {}
            //console.log("optionsssssssssssssssssssssssssssssssssssssss",options);
            OrderSuper.prototype.initialize.apply(this, arguments);
            this.sync_user = {}
            if (!_.isEmpty(options.sync_user)){
                this.sync_user = options.sync_user;
            } else if (this.pos.pos_multi_session){
                this.sync_user['created'] = this.pos.sync_user_detail();
            }
            this.sync_empty_order = is_new_order;
            //console.log("remove orderlineeeeeeeeeeeeeeeeeeeeeeeeeeee",is_new_order);
            is_new_order = false;
            this.bind('change:sync', function(){
                self.sync_migrate();
            })
        },
        
        add_product: function(){
            OrderSuper.prototype.add_product.apply(this, arguments);
            console.log("add productttttttttttttttttttttttttttttttttttttt");
            this.trigger('change:sync');
        },
        
        set_client: function(client){
            OrderSuper.prototype.set_client.apply(this,arguments);
            //console.log("clienttttttttttttttttttttttttttttttttttttttttt",client);
            this.trigger('change:sync');
        },     
           
        sync_remove_order: function(){
            if (!this.sync_test())
                return;
            this.done_sync_remove_order();
        },
        
        sync_test: function(){
            if (! this.pos.pos_multi_session )
                return;
            if (this.pos.my_sync_is_in_progress)
                return;
            return true;
        },
        
        sync_migrate: function(){
            var self = this;
            //console.log("thisssssssssssssssssssssss",this);
            if (!this.sync_test())
                return;
            if (this.sync_migrate_contribute)
                // restart timeout
                clearTimeout(this.sync_migrate_contribute)
            this.sync_migrate_contribute = setTimeout(
                function(){
                    self.sync_migrate_contribute = false;
                    self.sync_migration();
                }, 300)
        },

        remove_orderline: function(line){
            OrderSuper.prototype.remove_orderline.apply(this, arguments);
            console.log("remove orderlineeeeeeeeeeeeeeeeeeeeeeeeeeee",line);
            line.order.trigger('change:sync');
        },
                
        sync_migration: function(){
            var data = this.export_as_JSON();
            //console.log("dataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",data);
            this.pos.pos_multi_session.update(data);
            //console.log("thisssssssssssssssssssssss",this);
            this.just_printed = false;
        },
        
        done_sync_remove_order: function(){
            //console.log("remove orderlineeeeeeeeeeeeeeeeeeeeeeeeeeee",this);
            this.pos.pos_multi_session.remove_order({'uid': this.uid});
        },

    	/*
    	export_as_JSON: function() {
            var self = this;
            var loaded = OrderSuper.prototype.export_as_JSON.call(this);
            //loaded.service_charge = self.get_service_charge();
            //loaded.amount_total = self.get_service_charge() + self.get_total_with_tax();
            return loaded;
        },
        */        
        export_as_JSON: function(){
            var self = this;
            var loaded = OrderSuper.prototype.export_as_JSON.apply(this, arguments);
            loaded.sync_user = this.sync_user;
            //console.log("loadedeeeeeeeeeeeeeeeeeeeeeeeeedddddddddddddddddddddddddd",loaded);
            return loaded;
        },
        
    });
    // End Order start
    	    
    // PosModel start
    
   /* var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var partner_model = _.find(this.models, function(model){ return model.model === 'res.partner'; });
            partner_model.fields.push('property_product_pricelist');
            //console.log("partner_modellllllllllllllllllllllllllllllllllll",partner_model)
            
            var pricelist_model = _.find(this.models, function(model){ return model.model === 'product.pricelist'; });
            pricelist_model.fields.push('id','name','currency_id','symbol');
            //console.log("pricelist_modellllllllllllllllllllllllll",pricelist_model)
            
            return _super_posmodel.initialize.call(this, session, attributes);
        },
        
    	push_order: function(order, opts){
            var self = this;
            var pushed = _super_posmodel.push_order.call(this, order, opts);
            
            var currentOrder = this.get_order();
            console.log("currentOrder   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", currentOrder);
            var client = order && order.get_client();
            console.log("selected_clientttttttttttttttttttttttttttt",client,order);
            return pushed;
        }
    });*/
    var _super_posmodel = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function(){
            var self = this;
            _super_posmodel.prototype.initialize.apply(this, arguments)
            //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",this);
            this.pos_multi_session = false;
            this.my_sync_is_in_progress = false;
            this.get('orders').bind('remove', function(order,_unused_,options){ 
                order.sync_remove_order();
            });
            this.get('orders').bind('add', function(order,_unused_,options){ 
                if (!self.my_sync_is_in_progress && self.pos_multi_session){
                    self.pos_multi_session.sync_sequence_number();
                }
            });

        },
        sync_user_detail: function(){
            var user = this.cashier || this.user;
            //return this.db.get_cashier() || this.cashier || this.user;
            return {'user': { 'id': user.id,'name': user.name,},'pos': { 'id': this.config.id, 'name': this.config.name,}}
        },

		// releases ressources holds by the model at the end of life of the posmodel
		//destroy: function(){
		    // FIXME, should wait for flushing, return a deferred to indicate successfull destruction
		    // this.flush();
		    //this.proxy.close();
		    //this.barcode_reader.disconnect();
		    //this.barcode_reader.disconnect_from_proxy();
		//},       
		 
        on_removed_order: function(removed_order, index, reason){
            if (this.pos_multi_session){
                //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",reason);
                if (reason === 'finishOrder'){
                    if (this.get('orders').size() > 0){
                        return this.set({'selectedOrder' : this.get('orders').at(index) || this.get('orders').first()});
                    }
                    this.add_new_order();
                    this.get('selectedOrder').sync_empty_order = true;
                    return;
                } else if (this.my_sync_is_in_progress){
                    //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",this);
                    if (this.get('orders').size() == 0){
                        this.add_new_order();
                    }
                    return;
                }
            }
            var self = this;
            return _super_posmodel.prototype.on_removed_order.apply(this, arguments)
        },
        orders_to_sync: function(){
            //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",this);
            return this.get('orders').models;
        },        
        sync_add_order: function (current_order) {
            //console.log("current_orderrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",current_order);
            if (!current_order) {
                return
            }
            var sync_empty = current_order.sync_empty;
            var sync_frozen = !current_order.sync_empty_order;
            //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",sync_frozen);
            if (sync_empty && !sync_frozen) {
                current_order.destroy({'reason': 'abandon'})
            } else if (sync_frozen || !sync_empty) {
                //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",sync_frozen,sync_empty);
                this.set('selectedOrder', current_order);
            }
        },
        sync_updation: function(message){
            this.my_sync_is_in_progress = true; // don't broadcast updates made from this message
            var error = false;
            //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",error,message);
            try{
                //console.log('on_update', message.action)
                var action = message.action;
                var data = message.data || {}
                //console.error(data);
                var order = false;
                if (data.uid){
                    order = this.get('orders').find(function(order){
                                return order.uid == data.uid;
                            })
                }
                if (order && action == 'remove_order'){
                    order.destroy({'reason': 'abandon'})
                } else if (action == 'update') {
                    this.sync_order_migrate(order, data);
                }
            }catch(err){
                error = err;
                //console.error(err);
            }
            this.my_sync_is_in_progress = false;
            //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",this);
            if (error){
                throw(error)
            }

            if (action == 'sync_sequence_number'){
                //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",this);
                this.my_sync_sequence_number(data);
            } else if (action == 'send_sync_request_all'){
                //don't executing sync_sequence_number, because new POS sync sequence_number on start, because new order is created automatically
                //this.pos_multi_session.sync_sequence_number();
                _.each(this.orders_to_sync(), function(r){
                    //console.log("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",r);
                    if (!r.sync_empty){
                        r.sync_migrate();
                    }
                })
            }
        },

        sync_create_order: function(options){
            options = _.extend({pos: this}, options || {});
            //console.log("optionssssssssssssssssssssssssssssssssss",options);
            return new models.Order({}, options);
        },
        my_sync_sequence_number: function(data){
            if (data.sequence_number < this.pos_session.sequence_number){
                //console.log("dataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",data);
                this.pos_multi_session.sync_sequence_number(this.pos_session.sequence_number);
            } else {
                //console.log("dataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",data);
                this.pos_session.sequence_number = data.sequence_number;
            }
            /*
            this.get('orders').each(function(r){
                var sn = data[r.uid];
                if (sn != r.sequence_number){
                    r.sequence_number = sn;
                }
            })
             */
        },
        sync_order_migrate: function(order, data){
            var pos = this;
            var sequence_number = data.sequence_number;
            //console.log("orderrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr calledddddddddd",order, data);
            if (!order){
                var create_new_order = pos.config.pos_accept_orders || !(data.sync_user && data.sync_user.created.user.id != pos.sync_user_detail().user.id)
                //console.log("thisssssssssssssssssssssssssssssssssssssss",this);
                if (sequence_number == this.pos_session.sequence_number){
                    //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",this);
                } else if (sequence_number > this.pos_session.sequence_number){
                    //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",this);
                    this.pos_session.sequence_number = sequence_number;
                } else if (sequence_number < this.pos_session.sequence_number){
                    //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",this);
                    pos.pos_multi_session.sync_sequence_number();
                    if (create_new_order)
                        this.pos_session.sequence_number--; //console.log("productttttttttttttttttttttttttttttttttttttttttttttttttttt",this);
                }
                if (!create_new_order){
                    return;
                }
                var json = {
                    sequence_number: data.sequence_number,
                    uid: data.uid,
                    pos_session_id: this.pos_session.id,
                    statement_ids: false,
                    lines: false,
                    multiprint_resume: data.multiprint_resume,
                }
                //console.log("jsonnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn",json);
                order = this.sync_create_order({sync_user:data.sync_user,data:data,json:json})
                //order.uid = data.uid;
                //order.sequence_number = data.sequence_number
                var current_order = this.get_order();
                //console.log("orderrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",current_order);
                this.get('orders').add(order);
                //console.log("orderrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",order);
                this.sync_add_order(current_order);
            } else {
                order.sync_user = data.sync_user;
            }
            var not_available = order.orderlines.map(function(r){
                                return r.uid;
                            })
            if(data.partner_id!=false)
            {
                var client = order.pos.db.get_partner_by_id(data.partner_id);
                //console.log("clientttttttttttttttttttttttttttttttttttttttttt",client);
                if(!client)
                {

                    $.when(this.load_new_partners_by_id(data.partner_id))
                                    .then(function(client){client = order.pos.db.get_partner_by_id(data.partner_id);
                             order.set_client(client);},function(){});
                }
                order.set_client(client);
            }
            else
            {
                order.set_client(null);
            }

            _.each(data.lines, function(dline){
                dline = dline[2];
                var line = order.orderlines.find(function(r){
                    //console.log("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",r);
                    return dline.uid == r.uid
                })
                //console.log("lineeeeeeeeeeeeeeeeeeeeeeeeeeeee",line);
                not_available = _.without(not_available, dline.uid);
                var product = pos.db.get_product_by_id(dline.product_id);
                //console.log("producttttttttttttttttttttttttttttttttttttt",product);
                if (!line){
                    line = new models.Orderline({}, {pos: pos, order: order, product: product});
                    line.uid = dline.uid
                }
                line.sync_user = dline.sync_user || {}
                if(dline.qty !== undefined){
                    //console.log("************ lineeeeeeeeeeeeeeeeeeeeeeeeeeeeee",line);
                    line.set_quantity(dline.qty);
                }
                if(dline.price_unit !== undefined){
                    //console.log("11111111111111 lineeeeeeeeeeeeeeeeeeeeeeeeeeeeee",line);
                    line.set_unit_price(dline.price_unit);
                }
                if(dline.discount !== undefined){
                    //console.log("22222222222222222 lineeeeeeeeeeeeeeeeeeeeeeeeeeeeee",line);
                    line.set_discount(dline.discount);
                }
                if(dline.mp_dirty !== undefined){
                    //console.log("3333333333333333 lineeeeeeeeeeeeeeeeeeeeeeeeeeeeee",line);
                    line.set_dirty(dline.mp_dirty);
                }
                if(dline.mp_skip !== undefined){
                    //console.log("44444444444444 lineeeeeeeeeeeeeeeeeeeeeeeeeeeeee",line);
                    line.set_skip(dline.mp_skip);
                }
                if(dline.note !== undefined){
                    //console.log("5555555555555 lineeeeeeeeeeeeeeeeeeeeeeeeeeeeee",line);
                    line.set_note(dline.note);
                }
                order.orderlines.add(line)
            })

            _.each(not_available, function(uid){
                var line = order.orderlines.find(function(r){
                               return uid == r.uid;
                           })
                //console.log("2222222222222 lineeeeeeeeeeeeeeeeeeeeeeeeeeeeee",line);
                order.orderlines.remove(line);
            })

        },
        load_new_partners_by_id: function(partner_id){
		    var self = this;
		    var def  = new $.Deferred();
		    var client;
		    var fields = _.find(this.models,function(model){ return model.model === 'res.partner'; }).fields;
		    //console.log("fieldsssssssssssssssssssssssssssssssssss",fields);
				new Model('res.partner')
				    .query(fields)
				    .filter([['id','=',partner_id]])
				    .all({'timeout':3000, 'shadow': true})
				    .then(function(partners){
				        if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
				            def.resolve();
				        } else {
				            def.reject();
				        }
				    }, function(err,event){ event.preventDefault(); def.reject(); });
				return def;
    	},
        load_server_data: function () {
            var res = _super_posmodel.prototype.load_server_data.apply(this, arguments);
		    var self = this;
		    var loaded = new $.Deferred();
		    //var progress = 0;
		    var tmp = {}; // this is used to share a temporary state between models loaders
            return res.then(function(){
                             if (self.config.pos_multi_session_id){
                                 //console.log("loadddddddddddddddddddddddddddddddddddddddddddddd",exports);
                                 self.pos_multi_session = new exports.SyncSession(self);
                                 self.pos_multi_session.start();
                                 // catching exceptions in model.loaded(...)
                                 self.pos_multi_session.send_sync_request_all();
                             }
                         })
        },
    });
    // End PosModel start

     

    // exports.OrderWidget = Backbone.Model.extend ...
    var OrderWidgetExtended = screens.OrderWidget.include({
        /*
		update_summary: function(){
		    var order = this.pos.get_order();
		    if (!order.get_orderlines().length) {
		        return;
		    }

		    var total     = order ? order.get_total_with_tax() : 0;
		    var taxes     = order ? total - order.get_total_without_tax() : 0;

		    this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
		    this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);

		},
		*/
		
        rerender_orderline: function(order_line){
            if (order_line.node)
                //console.log("order_lineeeeeeeeeeeeeeeeeeeeeeeee",order_line);
                return this._super(order_line);
        },
        remove_orderline: function(order_line){
            //console.log("22222222222222222 order_lineeeeeeeeeeeeeeeeeeeeeeeee",order_line);
            if (!this.pos.get_order())
                return;
            this._super(order_line)
        },
    });
    // End OrderWidget start

    // SyncButtonWidget start
    
    /*var SyncButtonWidget = screens.ActionButtonWidget.extend({
        template: 'SyncButtonWidget',
        button_click: function() {
            var order = this.pos.get_order();
            var self = this;
            this.gui.show_popup('select_existing_popup_widget', {});
        },
    });

    screens.define_action_button({
        'name': 'Sync Button Widget',
        'widget': SyncButtonWidget,
        'condition': function() {
            return true;
        },
    });
    */
    // End SyncButtonWidget start
       
    
    // exports.SyncSession start
    exports.SyncSession = Backbone.Model.extend({
        /*
        initialize: function(order){
            Backbone.Model.prototype.initialize.apply(this, order);
            this.set({
                'order_name':  order.name,
                'order_id': order.id,
                'partner_id': order.partner_id[0],
                'move_lines': order.move_lines,
            });
        },
        */
        
        initialize: function(pos){
            //Backbone.Model.prototype.initialize.apply(this, order);

            //this.pos   = options.pos;
    		//this.order = options.order;

			//this.product = options.product;
        	//this.price   = options.product.price;
        	
            this.pos = pos;
            console.log("initializeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",this.pos);
        },
        start: function(){
            var self = this;
            console.log("starttttttttttttttttttttttttttttttttttttttt");
            //this.pos   = options.pos;
    		//this.order = options.order;

			//this.product = options.product;
        	//this.price   = options.product.price;
            this.bus = bus.bus;
            this.bus.last = this.pos.db.load('bus_last', 0);
            //console.log("initializeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",this.bus);
            this.bus.on("notification", this, this.sync_notification);
            //console.log("initializeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",this.bus);
            this.bus.start_polling();

            //return done;
        },
        send_sync_request_all: function(){
            //console.log("initializeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",this.bus);
            this.send({'action': 'send_sync_request_all'})
        },
        sync_sequence_number: function(){
            var orders = {};
            this.pos.get('orders').each(function(r){
                //console.log("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",r);
                orders[r.uid] = r.sequence_number;
            })
            var data = {
                'sequence_number': this.pos.pos_session.sequence_number,
                //'orders': orders,
            }
            this.send({action: 'sync_sequence_number', data: data})
        },
        remove_order: function(data){
            //console.log("dataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",data);
            this.send({action: 'remove_order', data: data})
        },
        update: function(data){
            //console.log("dataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",data);
            this.send({action: 'update', data: data})
        },
        send: function(message){
            //console.log('send:', message.action)
            var self = this;
            console.log("senddddddddddddddddddddddddddddddddddddddddddddddddddd",self,message)
            var send_it = function() {
                return session.rpc("/pos_sync_multi_session/sync", {pos_multi_session_id: self.pos.config.pos_multi_session_id[0], message: message});
            };
            var tries = 0;
            send_it().fail(function(error, e) {
                e.preventDefault();
                tries += 1;
                if (tries < 3)
                    return send_it();
            });
        },
        sync_notification: function(notification) {
            var self = this;
            if (typeof notification[0][0] === 'string') {
                notification = [notification]
            }
            //console.log("notificationnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn",notification);
            for (var i = 0; i < notification.length; i++) {
                //console.log("notificationnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn",notification[i]);
                var channel = notification[i][0];
                var message = notification[i][1];
                //console.log("notificationnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn",channel,message);
                this.sync_notification_do(channel, message);
            }
        },
        sync_notification_do: function (channel, message) {
            //console.log("senddddddddddddddddddddddddddddddddddddddddddddddddddd",channel, message);
            if(Array.isArray(channel) && channel[1] === 'pos.multi.session'){
                try{
                    this.pos.sync_updation(message)
                }catch(err){
                    this.pos.chrome.gui.show_popup('error',{
                        'title': _t('Error'),
                        'body': err,
                    })
                }
            }
            this.pos.db.save('bus_last', this.bus.last)
        }
    })
    return exports;
})
