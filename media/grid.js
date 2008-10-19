$(document).ready(function() {

	var DATE_MIN = 100001;
	var DATE_MAX = 300001;
	var TAG_NORMAL = $("#alltags").width();
	var TAG_EXPANDED = TAG_NORMAL + 13;
	var FS = ".", FS2 = ","; // remember to change in paginator/frontpage template too
	var IFRAME = $("iframe").size() > 0;
	var EMPTY_SELECTION = [[], 1, DATE_MIN, DATE_MAX];

	// takes (#serializedstate) or (/path/to/url, [[tags],page,dmin,dmax])
	// for the second any nulls will be replaced by default values
	function State(arg1, sel) {
		change_hash = true;
		if (arg1 && arg1.charAt(0) == "#") {
			var hash = arg1.substring(1).split(FS);
			url = hash[0];
			var tags = hash[1] ? hash[1].split(FS2) : '';
			var page = hash[2] ? hash[2] : 1;
			var date_min = hash[3] ? hash[3] : DATE_MIN;
			var date_max = hash[4] ? hash[4] : DATE_MAX;
			selection = [tags, page, date_min, date_max];
		} else {
			url = arg1 ? arg1 : '';
			selection = sel ? sel : EMPTY_SELECTION;
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
				if (url && url.match("http://")) { // make relative
					url = url.substring(7);
					url = url.substring(url.indexOf("/"));
				}
			}
			if (change_hash || IFRAME) { // ignore on IE6/7
				window.location.hash = State.hash = this.toString();
				if (IFRAME) {
					window["iFrame"].document.body.innerHTML = this;
					$("#iFrame").attr("src", "/echo/" + this);
				}
			} else {
				State.hash = window.location.hash.substring(1);
				if (IFRAME)
					window["iFrame"].document.body.innerHTML = this;
			}
			State.select_tags(selection[0]);
			State.select_dates(selection[2], selection[3]);
			if (url)
				State.load_url(url);
			else
				State.load_selection(selection);
		};
		this.toString = function() {
			var tags = (selection && selection[0]) ? selection[0].join(FS2) : '';
			var sel = selection ? selection.slice(1).join(FS) : '';
			return url + FS + tags + FS + sel;
		};
		this.keep_hash = function() {
			change_hash = false;
			return this;
		};
	}
	State.init_ms = new Date().getTime();
	State.disabled = false;
	State.request_count = 0;
	State.cached = new Object();
	State.activelink = null;
	State.hash = window.location.hash.substring(1);
	State.increment_threshold = function() {
		var dt = new Date().getTime() - State.init_ms;
		if (State.request_count++ / (3+(dt/1000)) > 1)
			alert("This script appears to be stuck in an infinite loop.\n("
			+ State.request_count + " requests in " + (dt/1000)
			+ " seconds)\n\nPlease report this bug.");
		State.disabled = true;
	};
	State.current = function() {
		var page = Number($("#thispage").text());
		if (!page) page = 1;
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
		return new State(null, [selectedtags, page, min, max]);
	};
	State.load_url = function(url) {
		State.request = $.ajax({
			type: "GET",
			url: "/ajax/embed" + url,
			success: function(responseData) {
				$("#embedded_content").html(responseData);
			},
			error: function(xhr) {
				$("#embedded_content").html(xhr.responseText);
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
	State.load_selection = function(selection) {
		var hit = State.cached[selection];
		function load(data) {
			State.read_json_tags(data['tags']);
			State.read_json_dates(data['dates']);
			State.read_json_results(data['results']);
			State.read_json_paginator(data['pages'], selection);
			if (!hit) {
				data['results']['new'] = null;
				State.cached[selection] = data;
			}
			State.grab_links();
			$(".embed").hide();
			$(".results").show();
			State.release_request();
		}
		if (hit) {
			load(hit);
		} else {
			var have_articles = $("#results li")
				.not("#IE6_PLACEHOLDER")
				.map(function() {
						return $(this).attr("id").substring(4); // art_
					}).get();
			State.request = $.getJSON("/ajax/paginator",
				{"tags": selection[0], "page": selection[1], "have_articles": have_articles,
				 "date_min": selection[2], "date_max": selection[3]}, load);
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
	State.read_json_paginator = function(pages, data) {
		$("#paginator").empty();
		if (pages['num_pages'] > 1) {
			for (var i = 1; i <= pages['num_pages']; i++) {
				if (i == pages['this_page'])
					$("#paginator").append(" <li id=\"thispage\">" + i + "</li>");
				else
					$("#paginator").append(" <li id=\"n_"
					+ i + "\" class=\"pagelink\"><a href=\"#"
					+ new State(null, [data[0],i,data[2],data[3]])
					+ "\">"
					+ i + "</a></li>");
			}
		}
	};
	State.acquire_request = function() {
		if (State.request) {
			State.request.abort();
			State.request = null;
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
		State.request = null;
		if (State.activelink)
			State.activelink.removeClass("active");
		State.activelink = null;
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
	State.grab_links = function() {
		$(".embeddable").click(function(event) {
			if (event.ctrlKey || event.shiftKey)
				return;
			event.preventDefault();
			State.current().enter($(this));
			window.scroll(0,0);
		});
		$("#paginator .pagelink").click(function(event) {
			event.preventDefault();
			State.current().page($(this).attr("id").substring(2)).enter();
			window.scroll(0,0);
		});
		$("#goto_top").click(function() {
			window.scroll(0,0);
		});
	};

	var selecting_dates = false;
	var down = false;
	$("#tags #alltags").width(TAG_EXPANDED);
	$("#tags").disableTextSelect();
	$("#dates").disableTextSelect();
	State.grab_links();
	if (window.location.hash.length > 1) // permalink and not lone '#'
		new State(window.location.hash).enter();

	// XXX backspace-disabling redirect ok only
	// because this runs for new windows
	if (window.location.pathname != "/")
		window.location = "/#" + window.location.pathname;

	setInterval(function() {
		if (State.disabled)
			return; // polling has exceeeded threshold
		if (window.location.hash.substring(1) != State.hash) {
			State.increment_threshold();
			new State(window.location.hash).keep_hash().enter();
		} else if (IFRAME && window["iFrame"].document.body.innerHTML != State.hash) {
			State.increment_threshold(); // no keep_hash:
			new State("#" + window["iFrame"].document.body.innerHTML).enter();
		}
	}, 100);

	$("#tags li").not("#alltags").click(function(event) {
        if (event.ctrlKey || event.shiftKey)
            return;
        event.preventDefault();
		if ($(this).hasClass("useless") && !$(this).hasClass("activetag"))
			$("#tags .activetag").not("#alltags").removeClass("activetag");
		tagslug = $(this).attr("id");
		$(this).removeClass("useless").toggleClass("activetag");
		State.current().enter();
		window.scroll(0,0);
	});

	$("#tags #alltags").click(function(event) {
        event.preventDefault();
		$("#dates li").removeClass("activedate");
		selecting_dates = false;
		$("#tags li").removeClass("useless");
		$("#tags .activetag").removeClass("activetag");
		State.current().enter();
		window.scroll(0,0);
	});

	$("#tags li a").click(function(event) {
        if (event.ctrlKey || event.shiftKey)
            return;
		event.preventDefault();
	});

	$("#dates h3").click(function(event) {
        event.preventDefault();
		var min = ($(this).text() - 1) + "08";
		var max = $(this).text() + "07";
		var some_newly_selected = false;
		if (!State.select_dates(min, max)[0])
			$("#dates li").removeClass("activedate");
		State.current().enter();
	});

	$("#dates li li").mousedown(function() {
		if (!selecting_dates) {
			if ($(this).hasClass("activedate"))
				down = $(this).attr("id");
			else
				down = false;
			$("#dates li").removeClass("activedate");
			$(this).addClass("activedate");
			selecting_dates = true;
		}
	});

	$("#dates li li").mousemove(function() {
		if (selecting_dates)
			$(this).addClass("activedate");
	});

	$("#dates li").mouseup(function() {
		if (down == $(this).attr("id")) {
			$(this).removeClass("activedate");
		} else if (selecting_dates) {
			$(this).addClass("activedate");
		}
		if (selecting_dates) {
			selecting_dates = false;
			State.current().enter();
		}
	});

	$(document).mouseup(function(event) {
		if (selecting_dates) {
			selecting_dates = false;
			State.current().enter();
		}
	});
});
