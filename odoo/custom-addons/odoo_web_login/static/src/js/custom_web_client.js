odoo.define('odoo_web_login.CustomWebClient', function (require) {"use strict";
    
	var WebClient = require('web.WebClient');
    
    WebClient.include({
        start: function() {
        	var _result;
        	this.set('title_part', {"zopenerp": "VBS"});
        	var _super = this._super.bind(this);
            setTimeout(function () {
            	_result = _super();
            }.bind(this), 0);
            return _result;
        },
    });
});