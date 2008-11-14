/* Grid state - ajax history and loading + google search tacked on.
 *
 * Static methods:
 *
 *	State.init(tag_width_normal, tag_width_expanded, iframe, ungrab_function)
 *		- run before using any other functions
 *	State.current()
 *		- returns current state of page with a page number of 1
 *	State.scrollup()
 *		- flags next page load for scrolling to top
 *	State.submit_poll(id)
 *		- renders response to poll of choice 'id'
 *	State.select_dates(min, max)
 *		- selects dates between min and max
 *		- returns (true if any were highlighted, true if any were unhighlighted)
 *
 * As object:
 *
 *	Construct by passing either of the two:
 *		"#/relative/url/path,page=1,tags=one.two,min=200801,max=200805,month=200805"
 *			(all args optional; url must be first if used)
 *		[[tag,tag], page#, min, max]
 *			(nulls will be replaced by default values)
 *	[State].enter()
 *		- loads new state, overriding any other enter() operations
 *	[State].page(n)
 *		- sets page to 'n'; returns self
 *	[State].keep_hash()
 *		- disables history tracking; returns self
 *  [State].toString()
 *		- returns serialized form to be used for reconstruction
 *
 * Uses identifiers:
 *
 *	#IE6_PLACEHOLDER
 *	#alltags
 *	#bottom_paginator
 *	#dates
 *	#embedded_content
 *	#none-visible
 *	#poll
 *	#results
 *	#tags
 *	#top_paginator
 *	.active
 *	.activedate
 *	.activetag
 *	.embed
 *	.month
 *	.results
 *	.useless
 *	.year
 */

google.load('search', '1.0');
var searchControl;
google.setOnLoadCallback(function() {
	searchControl = new google.search.SearchControl();
	var siteSearch = new google.search.WebSearch();
	siteSearch.setSiteRestriction("http://wvnexus.com");
	siteSearch.setUserDefinedLabel("The Nexus");
	options = new google.search.SearcherOptions();
	options.setRoot(document.getElementById("search_results"));
	options.setExpandMode(google.search.SearchControl.EXPAND_MODE_OPEN);
	searchControl.addSearcher(siteSearch, options);
	searchControl.setResultSetSize(google.search.Search.LARGE_RESULTSET);
	searchControl.draw(document.getElementById("searchcontrol"));
	searchControl.setSearchCompleteCallback(null, function(searchControl, searcher) {
		$("a.gs-title").unbind().click(function(event) {
			if (event.ctrlKey || event.shiftKey)
				return;
			if ($(this).attr("href").match(/\.[a-z]+$/)) {
				$(this).attr("target", null);
				return; // it's probably non-html
			}
			event.preventDefault();
			State.current().enter($(this));
			State.scrollup();
		});
	});
}, true);

var DATE_MIN = 100001;
var DATE_MAX = 300001;
var FS = ",", FS2 = ".";
var TAG_NORMAL, TAG_EXPANDED, IFRAME; // use State.init(a,b,c,grab_links)

function State(arg1, sel) {
	change_hash = true;
	url = '';
	selection = [[], 1, DATE_MIN, DATE_MAX];
	if (arg1 && arg1.charAt(0) == "#") {
		var args = arg1.substring(1).split(FS);
		for (var i in args) {
			var x = args[i];
			if (x.substring(0,1) == '/')
				url = x;
			else if (x.substring(0,5) == 'tags=')
				selection[0] = x.substring(5).split(FS2);
			else if (x.substring(0,5) == 'page=')
				selection[1] = x.substring(5);
			else if (x.substring(0,6) == 'month=')
				selection[2] = selection[3] = x.substring(6);
			else if (x.substring(0,4) == 'min=')
				selection[2] = x.substring(4);
			else if (x.substring(0,4) == 'max=')
				selection[3] = x.substring(4);
		}
	} else {
		if (arg1)
			url = arg1;
		if (sel)
			selection = sel;
	}

	this.page = function(num) {
		selection[1] = num;
		return this;
	};

	this.enter = function(link) {
		State.acquire_request();
		if (link) {
			State.activelink = link.addClass("active");
			url = link.attr("href");
			if (url.match(/#/))
				url = undefined;
			if (url && url.match("http://")) { // make relative
				url = url.substring(7);
				url = url.substring(url.indexOf("/"));
			}
		}
		if (change_hash || IFRAME) { // always do this on IE6/7
			var new_state_hash = this.toString();
			State.queued_history = function() {
				window.location.hash = State.hash = new_state_hash;
				if (change_hash && IFRAME) {
					var doc = document.getElementById("iFrame").contentWindow.document;
					doc.open();
					doc.write(new_state_hash);
					doc.close();
				}
			};
		} else
			State.hash = window.location.hash;
		State.select_tags(selection[0]);
		State.select_dates(selection[2], selection[3]);
		if (url) {
			State.load_url(url);
			State.load_selection(selection, this.toString(true), true);
		} else
			State.load_selection(selection, this.toString(true));
	};

	this.toString = function(omit_page) {
		var output = [];
		if (url)
			output[output.length] = url;
		if (selection[0] && selection[0].length > 0)
			output[output.length] = "tags=" + selection[0].join(FS2);
		if (selection[2] == selection[3]) {
			output[output.length] = "month=" + selection[2];
		} else {
			if (selection[2] != DATE_MIN)
				output[output.length] = "min=" + selection[2];
			if (selection[3] != DATE_MAX)
				output[output.length] = "max=" + selection[3];
		}
		if (!omit_page && (output.length === 0 || selection[1] != 1))
			output[output.length] = "page=" + selection[1];
		return '#' + output.join(FS);
	};

	this.keep_hash = function() {
		change_hash = false;
		return this;
	};
}

State.init = function(tag_norm, tag_exp, iframe, grab) {
	TAG_NORMAL = tag_norm;
	TAG_EXPANDED = tag_exp;
	IFRAME = iframe;
	State.grab_links = grab;
	State.grab_links();
	// hashes
	EMPTY = new State().toString();
	function different(a, b) {
		return a != b && !((!a || a == EMPTY) && (!b || b == EMPTY));
	}

	setInterval(function() {
		if (different(window.location.hash, State.hash)) {
			State.check_and_incr(window.location.hash, State.hash);
			new State(window.location.hash).keep_hash().enter();
		} else if (IFRAME && window["iFrame"].document.body && different(window["iFrame"].document.body.innerHTML, State.hash)) {
			State.check_and_incr(window["iFrame"].document.body.innerHTML, State.hash);
			new State(window["iFrame"].document.body.innerHTML).keep_hash().enter();
		}
	}, 100);
};

State.title = 'NO TITLE YET';
State.scroll_flag = false;
State.init_ms = new Date().getTime();
State.disabled = false;
State.request_count = 0;
State.cached = new Object();
State.activelink = null;
State.hash = window.location.hash;

State.check_and_incr = function(a,b) {
	if (State.disabled)
		throw "ProbablyStuckInLoop";
	var dt = new Date().getTime() - State.init_ms;
	if (State.request_count++ / (1+(dt/1000)) > 1) {
		alert("This script appears to be stuck in an infinite loop.\n("
		+ State.request_count + " requests in " + (dt/1000)
		+ " seconds)\n\nPlease report this bug.");
		alert("DEBUG: " + a + " vs " + b);
		State.disabled = true;
	}
};

State.scrollup = function() {
	State.scroll_flag = true;
};

State.current = function() {
	var min = DATE_MIN, max = DATE_MAX;
	var selected_dates = $("#dates .activedate").map(function() {
			return $(this).attr('id').substring(3); // ym_
		}).get();
	if (selected_dates.length > 0) {
		min = Math.min.apply(null, selected_dates);
		max = Math.max.apply(null, selected_dates);
	}
	var selectedtags = $("#tags li").filter(".activetag").not("#alltags")
		.map(function() {
				return $(this).attr("id").substring(4); // tag_
			}).get();
	return new State(null, [selectedtags, 1, min, max]);
};

State.load_url = function(url) {
	State.request = $.ajax({
		type: "GET",
		dataType: "json",
		url: "/ajax/embed" + url,
		success: function(responseData) {
			$("#embedded_content").html(responseData['html']);
			State.title = responseData['title'];
		},
		error: function(xhr) {
			$("#embedded_content").html(xhr.responseText);
			State.title = "error";
		},
		complete: function() {
			State.grab_links();
			$(".results").hide();
			$(".embed").show();
			State.release_request();
		}
	});
};

// data = [tags, page, datemin, datemax]
// just_url_update means we don't want to hide the embedded content
State.load_selection = function(selection, hashstring, just_url_update) {
	var hit = State.cached[selection];
	function load(data) {
		State.read_json_tags(data['tags']);
		State.read_json_dates(data['dates']);
		if (!just_url_update) {
			State.title = data['title'];
			State.read_json_results(data['results']);
			$("#top_paginator").html(data['pages']);
			$("#bottom_paginator").html(data['pages2']);
		}
		if (!hit) {
			data['results']['new'] = null;
			State.cached[selection] = data;
		}
		if (!just_url_update) {
			State.grab_links();
			$(".embed").hide();
			$(".results").show();
			State.release_request();
		}
	}
	if (hit) {
		load(hit);
	} else {
		var have_articles = $("#results li")
			.not("#IE6_PLACEHOLDER")
			.not("#none-visible")
			.map(function() {
					return $(this).attr("id").substring(4); // art_
				}).get();
		if (just_url_update)
		State.request2 = $.getJSON("/ajax/paginator",
			{"tags": selection[0], "page": selection[1], "have_articles": have_articles,
			 "date_min": selection[2], "date_max": selection[3], "hash": hashstring}, load);
		else
		State.request = $.getJSON("/ajax/paginator",
			{"tags": selection[0], "page": selection[1], "have_articles": have_articles,
			 "date_min": selection[2], "date_max": selection[3], "hash": hashstring}, load);
	}
};

State.read_json_tags = function(taginfo) {
	$("#tags li").not("#alltags").map(
		function() {
			for (var i in taginfo) {
				if ($(this).attr("id").substring(4) == taginfo[i][0]) {
					if (!taginfo[i][1])
						$(this).addClass("useless");
					else
						$(this).removeClass("useless");
					return;
				}
			}
			$(this).addClass("useless");
		}
	);
};

State.read_json_dates = function(dates) {
	$("#dates li").not(".year").map(
		function() {
			for (var i in dates) {
				if ($(this).attr("id").substring(3) == dates[i]) { // ym_
					$(this).removeClass("useless");
					return;
				}
			}
			$(this).addClass("useless");
		}
	);
};

State.read_json_results = function(results) {
	$("#results li").not("#IE6_PLACEHOLDER").hide();
	var visible = results['all'];
	var data = results['new'];
	for (var i in visible)
		$("#results li").filter("#art_" + visible[i]).show();
	for (var j in data)
		$("#results").append(data[j]);
	if (visible.length === 0)
		$("#none-visible").show();
	else
		$("#none-visible").hide();
};

State.acquire_request = function() {
	if (searchControl) // callback hasn't fired yet
		searchControl.cancelSearch();
	if (State.request) {
		State.scroll_flag = false;
		State.request.abort();
		State.request = null;
	}
	if (State.request2) {
		State.request2.abort();
		State.request2 = null;
	}
	if (State.activelink) {
		State.activelink.removeClass("active");
		State.activelink = null;
	}
	window.status = "Sent XMLHttpRequest...";
};

// call at end of dom update
State.release_request = function() {
	window.status = "Done";
	if (searchControl) // callback hasn't fired yet
		searchControl.clearAllResults();
	if (State.queued_history) {
		State.queued_history();
		State.queued_history = null;
	}
	document.title = State.title;
	State.request = null;
	State.request2 = null;
	if (State.activelink)
		State.activelink.removeClass("active");
	State.activelink = null;
	if (State.scroll_flag)
		window.scroll(0,0);
	State.scroll_flag = false;
};

State.select_tags = function(tags) {
	$("#tags li").removeClass("activetag");
	$("#tags li").not("#alltags").map(function() {
		for (var i in tags) {
			if ($(this).attr("id").substring(4) == tags[i]) {
				$(this).addClass("activetag");
				if ($(this).width() < TAG_EXPANDED)
					$(this).animate({"width":TAG_EXPANDED});
				return;
			}
		}
		$(this).removeClass("activetag");
		if ($(this).width() > TAG_NORMAL)
			$(this).animate({"width":TAG_NORMAL});
	});
};

State.select_dates = function(min, max) {
	var added_some = false, removed_some = false;
	$("#dates li li").map(function() {
		var date = $(this).attr('id').substring(3); // ym_
		if (date >= min && date <= max) {
			if (!$(this).hasClass("activedate")) {
				$(this).addClass("activedate");
				added_some = true;
			}
		} else {
			if ($(this).hasClass("activedate")) {
				$(this).removeClass("activedate");
				removed_some = true;
			}
		}
	});
	if ($("#dates li li").filter(".activedate").size() == $("#dates li li").size())
		$("#dates li li").removeClass("activedate");
	return [added_some,removed_some];
};

State.submit_poll = function submit_poll(choice_id) {
	$.getJSON("/ajax/poll", {"choice": choice_id}, function(r) {
		$("#poll_" + r['poll_id']).html(r['html']);
	});
};