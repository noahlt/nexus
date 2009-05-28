/**
 * Copyright (c) 2006 Taku Sano (Mikage Sawatari)
 * Licensed under the MIT License.
 *
 * Adapted by Eric Liang to work with existing code.
 *
 * History.init(callback('#serialized-history-state'))
 * History.put('#serialized-history-state')
 */

function History() {}

History.historyCurrentHash = undefined;
History.historyCallback = undefined;
History.useIframe = undefined;
History.poller = undefined;

function strip(input) {
	if (input) {
		if (input.charAt(0) == '#')
			input = input.substring(1);
	}
	return input;
}

History.callCallback = function(hash) {
	History.historyCallback('#' + hash.replace(/^#/, ''));
	fail = false;
	var a = '', b = '';
	if (History.useIframe) {
		var ihistory = $("#jQuery_history")[0];
		var iframe = ihistory.contentWindow.document;
		if (strip(iframe.location.hash) != strip(History.historyCurrentHash)) {
			a = iframe.location.hash;
			b = History.historyCurrentHash;
			fail = true;
		}
	} else {
		if (strip(location.hash) != strip(History.historyCurrentHash)) {
			a = location.hash;
			b = History.historyCurrentHash;
			fail = true;
		}
	}
	if (fail) {
		clearInterval(History.poller);
		alert("Assertion failed: hash values changed:\n'" + a + "' '" + b + "'");
	}
};

History.init = function(callback) {
	History.historyCallback = callback;
	History.useIframe = $.browser.msie && $.browser.version < 8;

	var current_hash = location.hash;
	History.historyCurrentHash = current_hash;

	if (History.useIframe) {
		// IE quirk?
		if (History.historyCurrentHash === '')
			History.historyCurrentHash = '#';

		// add hidden iframe for IE
		$("body").prepend('<iframe id="jQuery_history" style="display: none;"></iframe>');
		var ihistory = $("#jQuery_history")[0];
		var iframe = ihistory.contentWindow.document;
		iframe.open();
		iframe.close();
		iframe.location.hash = current_hash;
	}
	History.poller = setInterval(History.historyCheck, 100);
};

History.historyCheck = function() {
	var current_hash;
	if (History.useIframe) {
		var ihistory = $("#jQuery_history")[0];
		var iframe = ihistory.contentDocument || ihistory.contentWindow.document;
		current_hash = iframe.location.hash;
		if (current_hash != History.historyCurrentHash) {
			location.hash = current_hash;
			History.historyCurrentHash = current_hash;
			History.callCallback(current_hash);
			return;
		}
	}
	current_hash = location.hash;
	if (current_hash != History.historyCurrentHash) {
		History.historyCurrentHash = current_hash;
		History.callCallback(current_hash);
	}
};

History.put = function(hash) {
	location.hash = hash;
	History.historyCurrentHash = hash;
	if (History.useIframe) {
		var ihistory = $("#jQuery_history")[0];
		var iframe = ihistory.contentWindow.document;
		iframe.open();
		iframe.close();
		iframe.location.hash = hash;
	}
};
