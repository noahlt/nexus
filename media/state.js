var NONE_VISIBLE="<li id=\"none-visible\"><h3>No matching articles.</h3>Select fewer tags to the left, or specify a wider range of dates.</li>";

// set by State.init(a,b,c,d)
var TAG_NORMAL, TAG_EXPANDED, STATIC_FRONTPAGE;

var google_ok = false;
try {
	google.load('search', '1.0');
	var searchControl;
	google.setOnLoadCallback(function() {
		searchControl = new google.search.SearchControl();
		var siteSearch = new google.search.WebSearch();
		siteSearch.setSiteRestriction("http://wvnexus.com");
		siteSearch.setUserDefinedLabel("The Nexus");
		var options = new google.search.SearcherOptions();
		options.setRoot(document.getElementById("search_results"));
		options.setExpandMode(google.search.SearchControl.EXPAND_MODE_OPEN);
		searchControl.addSearcher(siteSearch, options);
		searchControl.setResultSetSize(google.search.Search.LARGE_RESULTSET);
		searchControl.draw(document.getElementById("searchcontrol"));
		searchControl.setSearchStartingCallback(null, function(searchControl, searcher) {
			setVisible("search"); // called early because the search bar is drawn early
		});
		searchControl.setSearchCompleteCallback(null, function(searchControl, searcher) {
			// otherwise we'll loop
			if (State.query != searchControl.input.value) {
				State.query = searchControl.input.value;
				State.sync({'query': searchControl.input.value});
			}
		});
		if (State.query) // was queued from page hash
			searchControl.execute(State.query);
		google_ok = true;
	}, true);
} catch (e) { } // google_ok will then be false

function is_nonlocal(event) {
	return event.ctrlKey || event.shiftKey
	|| (!$.browser.msie && event.button == 1); // not IE; chrome fix
}

function setVisible(str) {
	var types = ['embed', 'search', 'results'];
	for (var i in types) {
		key = types[i];
		if (key == str)
			$('.' + key).show();
		else
			$('.' + key).hide();
	}
	if (google_ok && str != 'search')
		searchControl.clearAllResults();
}

function State(repr, config) {
	repr = repr ? repr : new Repr();
	config = config ? config : {};

	this.select_tags = function() {
		$("#tags li").removeClass("activetag");
		$("#tags li").not("#alltags").map(function() {
			for (var i in repr.tags) {
				if ($(this).attr("id").substring(4) == repr.tags[i]) {
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

	this.read_json_dates = function(dates) {
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

	this.read_json_tags = function(taginfo) {
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

	this.read_json_results = function(results, just_url_update) {
		var visible = results['all'];
		var data = results['new'];
		var info = results['info'];
		for (var i in data) {
			var slug = data[i][0];
			var html = data[i][1];
			State.have_articles[State.have_articles.length] = slug;
			State.article_data[slug] = html;
		}
		if (!just_url_update) {
			$("#results").empty();
			if (info)
				$("#results").html(info);
			if (visible.length === 0)
				$("#results").append(NONE_VISIBLE);
			else {
				for (var j in visible)
					$("#results").append(State.article_data[visible[j]]);
			}
		}
	};

	this.load_url = function() {
		State.request = $.ajax({
			type: "GET",
			dataType: "json",
			url: "/ajax/embed" + repr.url,
			success: function(responseData) {
				$("#embedded_content").html(responseData['html']);
				State.title = responseData['title'];
			},
			error: function(xhr) {
				$("#embedded_content").html(xhr.responseText);
				State.title = "error";
			},
			complete: function() {
				setVisible("embed");
				State.release_request();
			}
		});
	};

	// just_url_update means we don't want to hide the embedded content
	this.load_repr = function(just_url_update) {
		var hashstring = repr.serialize(true);
		var hit = State.cached[repr];
		var that = this;
		function load(data) {
			that.read_json_tags(data['tags']);
			that.read_json_dates(data['dates']);
			if (!just_url_update)
				State.title = data['title'];
			that.read_json_results(data['results'], just_url_update);
			if (!just_url_update) {
				$("#top_paginator").html(data['pages']);
				$("#bottom_paginator").html(data['pages2']);
			}
			if (!hit) {
				data['results']['new'] = null;
				State.cached[repr] = data;
			}
			if (!just_url_update) {
				setVisible("results");
				State.release_request();
			}
		}
		if (hit) {
			load(hit);
		} else {
			if (just_url_update)
			State.request2 = $.getJSON("/ajax/paginator",
				{"tags": repr.tags, "author": repr.author, "page": repr.page, "have_articles": State.have_articles,
				 "date_min": repr.date_min, "date_max": repr.date_max, "hash": hashstring}, load);
			else
			State.request = $.ajax({
				type: "GET",
				dataType: "json",
				data: {"tags": repr.tags, "author": repr.author, "page": repr.page, "have_articles": State.have_articles,
					   "date_min": repr.date_min, "date_max": repr.date_max, "hash": hashstring},
				url: "/ajax/paginator",
				success: load,
				error: function(xhr) {
					$("#embedded_content").html(xhr.responseText);
					setVisible("embed");
					State.release_request();
				}
			});
		}
	};

	State.acquire_request();
	if (config['link']) {
		State.activelink = config['link'].addClass("active");
		if (!config['nofollow']) {
			function make_relative(url) {
				if (url.match("http://")) {
					url = url.substring(7);
					url = url.substring(url.indexOf("/"));
				}
				return url.length < 2 ? null : url;
			}
			repr.url = make_relative(config['link'].attr("href"));

			if (repr.url) {
				if (repr.url.match(/#/)) // 'embeddable' or search result link
					repr.url = undefined;
				else {
					var page_match = repr.url.match(/^\/[0-9]+$/);
					if (page_match) { // paginated root
						repr.page = page_match.toString().substring(1);
						repr.url = undefined;
					}
				}
			}
		}
	}

	if (History.useIframe || !config['keep_hash']) {
		History.queue(repr.serialize());
		if (config['atomic'])
			History.commit();
	}

	this.select_tags();
	State.select_dates(repr.date_min, repr.date_max);
	if (repr.query) {
		if (google_ok)
			searchControl.execute(repr.query);
		else {
			// either google hasn't loaded
			// or this is a initial page load
			// in any case queue it for processing
			State.query = repr.query;
		}
		this.load_repr(true);
		setVisible("search");
		State.release_request();
	} else {
		if (google_ok)
			State.query = '';
		if (repr.url) {
			this.load_url();
			this.load_repr(true);
		} else
			this.load_repr(false);
	}
}

State.init = function(tag_norm, tag_exp, cover) {
	TAG_NORMAL = tag_norm;
	TAG_EXPANDED = tag_exp;
	STATIC_FRONTPAGE = cover;
	$.ajax({
		type: "GET",
		dataType: "html",
		url: "/ajax/poll/current",
		success: function(r) {
			$("div #poll").html(r);
		}
	});
};

State.title = 'The Nexus';
State.scroll_flag = false;
State.query = '';
State.cached = new Object();
State.activelink = null;
State.have_articles = [];
State.article_data = new Object();

State.init_history_monitor = function() {
	History.init(function(hist) {
		new State(Repr.deserialize(hist), {'keep_hash': true});
	});
};

State.scrollup = function() {
	State.scroll_flag = true;
};

State.sync = function(overrides, config) {
	var min = DATE_MIN, max = DATE_MAX;
	var author = $("#authorslug").html();
	var selected_dates = $("#dates .activedate").map(function() {
			return $(this).attr('id').substring(3); // ym_
		}).get();
	if (selected_dates.length > 0) {
		min = Math.min.apply(null, selected_dates);
		max = Math.max.apply(null, selected_dates);
	}
	var tags = $("#tags li").filter(".activetag").not("#alltags")
		.map(function() {
				return $(this).attr("id").substring(4); // tag_
			}).get();
	var dict = {'tags': tags, 'date_min': min, 'date_max': max, 'author': author};
	for (var i in overrides)
		dict[i] = overrides[i];
	return new State(new Repr(dict), config);
};

State.acquire_request = function() {
	if (google_ok)
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
	History.commit();
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

// grid.js calls this
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

// vim: noet ts=4
