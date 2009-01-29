function History() {}

/**
 *	init(iframe, empty, callback)
 *	queue(hash)
 *	commit()
 *	sync()
 */

History.hash = window.location.hash;
History.queued = undefined;
History.iframe = undefined;

History.init = function(iframe, empty, callback) {
	History.iframe = iframe;
	function different(a, b) {
		return a != b && !((!a || a == empty) && (!b || b == empty));
	}
	function assertEqual(a, b) {
		if (a != b) {
			alert("DEBUG: [" + a + "] vs [" + b + "]");
			clearInterval(poll);
		}
	}
	var poll = setInterval(function() {
		if (different(window.location.hash, History.hash)) {
			callback(window.location.hash);
			assertEqual(window.location.hash, History.hash);
		} else if (iframe && window["iFrame"].document.body && different(window["iFrame"].document.body.innerHTML, History.hash)) {
			callback(window["iFrame"].document.body.innerHTML);
			assertEqual(window["iFrame"].document.body.innerHTML, History.hash);
		}
	}, 100);
};

History.sync = function() {
	History.hash = window.location.hash;
};

History.queue = function(hash) {
	History.queued = function() {
		window.location.hash = History.hash = hash;
		if (History.iframe) {
			var doc = document.getElementById("iFrame").contentWindow.document;
			doc.open();
			doc.write(hash);
			doc.close();
		}
	};
};

History.commit = function() {
	if (History.queued) {
		History.queued();
		History.queued = undefined;
	}
};
