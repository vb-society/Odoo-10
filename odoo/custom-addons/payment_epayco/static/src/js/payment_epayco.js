odoo.define('payment_epayco.checkout', function (require) {
    "use strict";
    var core = require('web.core');

    var EpaycoCheckout = core.Class.extend({
        init: function(form,data){
          this.$form = $(form);
          this.fields =  this.$form.find('input[type="hidden"]');

          this.data = _.defaults(data || {}, {
            //Parametros compra (obligatorio)
            name: "",description: "",invoice: "",currency: "",amount: "",
            tax_base: "",tax: "",country: "",lang: "",
            //Onpage="false" - Standard="true"
            external: "",
            //Atributos opcionales
            extra1: "",extra2: "",extra3: "",confirmation: "",response: "",rejected: "",
            //Atributos cliente
            email_billing: "",name_billing: "",address_billing: "",city_billing: "",
            type_doc_billing: "",mobilephone_billing: "", number_doc_billing: "",
            //atributo deshabilitación metodo de pago: ["TDC", "PSE","SP","CASH","DP"] 
            methodsDisable: []
          });

        },
        load_checkout: function(form){
          var configure = this.get_tx_values(["p_key","env_test"]);
          this.data = this.get_tx_values(_.keys(this.data));
          if(this.toType(this.data.methodsDisable) != 'array')
            this.data.methodsDisable = eval(this.data.methodsDisable)

          var handler = ePayco.checkout.configure({
            key: configure.p_key,
            test: configure.env_test,
          });
          
          handler.open(this.data);

          return false;
        },
        get_tx_values: function (listFields){
          var self = this;
          var result = {};

          _.each(listFields, function(fieldName) {
            var input = _.findWhere(self.fields,{'name': fieldName});
            if(input){
              result[fieldName] = input.value;
            }
          });

          return result;
        },
        toType: function(obj) {
          return ({}).toString.call(obj).match(/\s([a-z|A-Z]+)/)[1].toLowerCase()
        }
    });
    
    $(document).ready(function () {
        // When choosing an acquirer, display its Pay Now button
        var $payment = $("#payment_method");
        
        // When clicking on payment button: create the tx using json then continue to the acquirer
        $payment.on("click", 'button[type="submit"], button[name="submit"]', function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          var $form = $('form.epayco_acquirer_button');
          if($form.length > 0){
              $form.remove();
          }
          
          return false;
        });    
    });


    return EpaycoCheckout;
    
});