/**
 * Copyright (c) 2006 Taku Sano (Mikage Sawatari)
 * Licensed under the MIT License.
 *
 * Adapted by Eric Liang to work with existing code.
 *
 * History.init(callback('#serialized-history-state'))
 * History.queue('#serialized-history-state')
 * History.commit()
 */

function History() {}

History.historyCurrentHash = undefined;
History.historyCallback = undefined;
History.historyQueue = undefined;
History.useIframe = undefined;

History.callCallback = function(hash) {
	History.historyCallback('#' + hash.replace(/^#/, ''));
};

History.init = function(callback) {
	History.historyCallback = callback;
	History.useIframe = $.browser.msie && $.browser.version < 8;

	var current_hash = location.hash;
	History.historyCurrentHash = current_hash;

	if (History.useIframe) {
		// To stop the callback firing twice during initilization if no hash present
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
	History.callCallback(current_hash);
	setInterval(History.historyCheck, 100);
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
		}
	} else {
		current_hash = location.hash;
		if (current_hash != History.historyCurrentHash) {
			History.historyCurrentHash = current_hash;
			History.callCallback(current_hash);
		}
	}
};

History.queue = function(hash) {
	History.historyQueue = function() {
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
};

History.commit = function() {
	if (History.historyQueue) {
		History.historyQueue();
		History.historyQueue = undefined;
	}
};
