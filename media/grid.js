$(document).ready(function() {

	// for handling concurrency
	var request = null;
	var activelink = null;

	var cached = new Object();
	var selecting_dates = false;
	var down;
	var manual_click = true; // false if we don't want the hash to be generated again
	var DATE_MIN = 100001;
	var DATE_MAX = 300001;
	var TAG_NORMAL = $("#alltags").width();
	var TAG_EXPANDED = TAG_NORMAL + 13;
	var FS = ".", FS2 = ","; // remember to change in paginator/frontpage template too
	$("#tags #alltags").width(TAG_EXPANDED);

	var IFRAME = $("iframe").size() > 0;

	// takes (#serializedstate) or (/path/to/url, [[tags],page,dmin,dmax])
	// for the second any nulls will be replaced by default values
	function State(arg1, selection) {
		if (arg1 && arg1.charAt(0) == "#") {
			var hash = arg1.substring(1).split(FS);
			this.url = hash[0];
			var tags = hash[1] ? hash[1].split(FS2) : '';
			var page = hash[2] ? hash[2] : 1;
			var date_min = hash[3] ? hash[3] : DATE_MIN;
			var date_max = hash[4] ? hash[4] : DATE_MAX;
			this.selection = [tags, page, date_min, date_max];
		} else {
			this.url = arg1 ? arg1 : '';
			this.selection = selection ? selection : [[], 1, DATE_MIN, DATE_MAX];
		}
		this.load = function() {
			acquire_request();
			select_tags(this.selection[0]);
			select_dates(this.selection[2], this.selection[3]);
			if (this.url)
				load_url(this.url);
			else
				load_selection(this.selection);
		};
		this.toString = function() {
			var tags = (this.selection && this.selection[0]) ? this.selection[0].join(FS2) : '';
			var sel = this.selection ? this.selection.slice(1).join(FS) : '';
			return this.url + FS + tags + FS + sel;
		};
		this.set = function() {
			window.location.hash = State.hash = this.toString();
			if (IFRAME) {
				window["iFrame"].document.body.innerHTML = this;
				$("#iFrame").attr("src", "/echo/" + this);
			}
		};
	}
	State.hash = window.location.hash.substring(1);

	if (window.location.hash) // permalink
		new State(window.location.hash).load();

	setInterval(function() {
		var state;
		if (window.location.hash.substring(1) != State.hash) {
			manual_click = false;
			state = new State(window.location.hash);
			state.set();
			state.load();
		} else if (IFRAME && window["iFrame"].document.body.innerHTML != State.hash) {
			state = new State("#" + window["iFrame"].document.body.innerHTML);
			state.set();
			state.load();
		}
	}, 100);

	// change page number
	function click_page(event) {
		event.preventDefault();
		activelink = $(this).addClass("active");
		update($(this).attr("id").substring(2)); // n_
	}

	// load link into center column
	function click_embed(event) {
        if (event.ctrlKey || event.shiftKey)
            return;
		event.preventDefault();
		acquire_request();
		activelink = $(this).addClass("active");
		load_url(relative($(this).attr("href")));
	}

	function update(page) {
		acquire_request();
		__redraw_showall();
		load_selection(current_selection(page));
	}

	$("#paginator .pagelink").click(click_page);

	$("#tags li").not("#alltags").click(function(event) {
        if (event.ctrlKey || event.shiftKey)
            return;
        event.preventDefault();
		if ($(this).hasClass("useless") && !$(this).hasClass("activetag"))
			$("#tags .activetag").not("#alltags")
				.removeClass("activetag")
				.width(TAG_NORMAL);
		tagslug = $(this).attr("id");
		$(this).removeClass("useless").toggleClass("activetag");
		if ($(this).hasClass("activetag"))
			$(this).animate({"width":TAG_EXPANDED});
		else
			$(this).animate({"width":TAG_NORMAL});
		update(1);
	});

	$("#tags #alltags").click(function(event) {
        event.preventDefault();
		$("#dates li").removeClass("activedate");
		selecting_dates = false;
		$("#tags li").removeClass("useless");
		$("#tags .activetag").not("#alltags")
			.removeClass("activetag")
			.width(TAG_NORMAL);
		update(1);
	});

	$("#tags li a").click(function(event) {
        if (event.ctrlKey || event.shiftKey)
            return;
		event.preventDefault();
	});

	grab_links();

	$("#dates h3").click(function(event) {
        event.preventDefault();
		var min = ($(this).text() - 1) + "08";
		var max = $(this).text() + "07";
		if (!select_dates(min, max)[0])
			$("#dates li").removeClass("activedate");
		update(1);
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
			update(1);
		}
	});

	$("#tags").disableTextSelect();
	$("#dates").disableTextSelect();

	$(document).mouseup(function(event) {
		if (selecting_dates) {
			selecting_dates = false;
			update(1);
		}
	});

	// url = /relative/path/from/root
	function load_url(url) {
		if (manual_click)
			new State(url, current_selection()).set();
		request = $.ajax({
			type: "GET",
			url: "/ajax/embed" + url,
			success: function(responseData) {
				$("#embedded_content").html(responseData);
			},
			error: function(xhr) {
				$("#embedded_content").html(xhr.responseText);
			},
			complete: function() {
				grab_links();
				$(".results").hide();
				$(".embed").show();
				release_request();
			}
		});
	}

	// data = [tags, page, datemin, datemax]
	function load_selection(selection) {
		if (manual_click)
			new State(null, selection).set();
		var hit = cached[selection];
		function load(data) {
			read_json_tags(data['tags']);
			read_json_dates(data['dates']);
			read_json_results(data['results']);
			read_json_paginator(data['pages'], selection);
			if (!hit) {
				data['results']['new'] = null;
				cached[selection] = data;
			}
			release_request();
		}
		if (hit) {
			load(hit);
		} else {
			var have_articles = $("#results li")
				.not("#IE6_PLACEHOLDER")
				.map(function() {
						return $(this).attr("id").substring(4); // art_
					}).get();
			request = $.getJSON("/ajax/paginator",
				{"tags": selection[0], "page": selection[1], "have_articles": have_articles,
				 "date_min": selection[2], "date_max": selection[3]}, load);
		}
	}

	// call after new stuff is loaded to bind javascript functions
	function grab_links() {
		$(".embeddable").click(click_embed);
	}

	function select_tags(tags) {
		$("#tags li").removeClass("activetag").not("#alltags").width(TAG_NORMAL);
		if (tags.length > 0) {
			$("#alltags").removeClass("activetag");
			for (var i in tags)
				$("#tag_" + tags[i]).addClass("activetag").width(TAG_EXPANDED);
		} else {
			$("#alltags").addClass("activetag");
		}
	}

	function select_dates(min, max) {
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
	}


	// call before ajax request; aborts previous ones
	// set request/activelink AFTER calling
	function acquire_request() {
		if (request) {
			request.abort();
			request = null;
		}
		if (activelink) {
			activelink.removeClass("active");
			activelink = null;
		}
		window.status = "Sent XMLHttpRequest...";
	}

	// call at end of dom update
	function release_request() {
		window.status = "Done";
		request = null;
		if (activelink)
			activelink.removeClass("active");
		activelink = null;
		if (manual_click)
			window.scroll(0,0);
		manual_click = true;
	}

	function __redraw_showall() {
		if (!$("#tags li").not("#alltags").hasClass("activetag") && !$("#dates li").hasClass("activedate"))
			$("#tags #alltags").addClass("activetag");
		else
			$("#tags #alltags").removeClass("activetag");
	}

	function read_json_tags(taginfo) {
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
	}

	function read_json_dates(dates) {
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
	}

	function read_json_results(results) {
		$("#results li").not("#IE6_PLACEHOLDER").hide();
		var visible = results['all'];
		var data = results['new'];
		for (var i in visible)
			$("#results li").filter("#art_" + visible[i]).show();
		for (var j in data)
			$("#results").append(data[j]);
		grab_links();
		$(".embed").hide();
		$(".results").show();
		if (visible.length === 0)
			$("#none-visible").show();
		else
			$("#none-visible").hide();
	}

	function read_json_paginator(pages, data) {
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
		$("#paginator .pagelink").click(click_page);
	}

	function relative(url) {
		if (url.match("http://")) { // oops, make it relative again
			url = url.substring(7);
			url = url.substring(url.indexOf("/"));
		}
		return url;
	}

	function current_selection(page) {
		if (!page)
			page = Number($("#thispage").text());
		var min = DATE_MIN, max = DATE_MAX;
		var selected_dates = $("#dates .activedate").map(function() {
				return $(this).attr('id').substring(3); // ym_
			}).get();
		if (selected_dates.length > 0) {
			min = Math.min.apply(null, selected_dates);
			max = Math.max.apply(null, selected_dates);
			select_dates(min, max); // ensure ui consistency
		}
		var selectedtags = $("#tags li").filter(".activetag").not("#alltags")
			.map(function() {
					return $(this).attr("id").substring(4); // tag_
				}).get();
		return [selectedtags, page, min, max];
	}
});
