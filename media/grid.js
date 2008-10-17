$(document).ready(function() {

	// for handling concurrency
	var request = null;
	var activelink = null;

	var selecting_dates = false;
	var down;
	var autoclick = false;
	var DATE_MIN = 100001;
	var DATE_MAX = 300001;
	var TAG_NORMAL = $("#alltags").width();
	var TAG_EXPANDED = TAG_NORMAL + 13;
	$("#tags #alltags").width(TAG_EXPANDED);

	var cached = new Object();
	var history = [];
	history.push([[], 1, DATE_MIN, DATE_MAX]);

	var hash = window.location.hash.substring(1);
	setInterval(function() {
		if (window.location.hash.substring(1) != hash) {
			if (window.location.hash.substring(1)) {
				autoclick = true;
				load_hash(window.location.hash);
				hash = window.location.hash.substring(1);
			}
		}
	}, 100);

	if (window.location.hash) {
		load_hash(window.location.hash);
	}

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
		url = relative($(this).attr("href"));
		history.push(url);
		load_url(url);
	}

	// with the #
	function load_hash(hash) {
		var target = hash ? deserialize(hash.substring(1)) : [[],1,DATE_MIN,DATE_MAX];
		acquire_request();
		if (target instanceof Array) {
			select_tags(target[0]);
			select_dates(target[2], target[3]);
			load_selection(target);
		} else {
			load_url(target);
		}
	}

	function update(page) {
		acquire_request();
		__redraw_showall();
		var min = DATE_MIN, max = DATE_MAX;
		var selected_dates = $("#dates .activedate").map(function() {
				return $(this).attr('id').substring(3); // ym_
			}).get();
		if (selected_dates.length > 0) {
			min = Math.min.apply(null, selected_dates);
			max = Math.max.apply(null, selected_dates);
			select_dates(min, max);
		}
		var selectedtags = $("#tags li").filter(".activetag").not("#alltags")
			.map(function() {
					return $(this).attr("id").substring(4); // tag_
				}).get();
		var selection = [selectedtags, page, min, max];
		load_selection(selection);
		history.push(selection);
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
			$(this).width(TAG_EXPANDED);
		else
			$(this).width(TAG_NORMAL);
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

	// url = /path/from/root
	function load_url(url) {
		if (!autoclick)
			window.location.hash = hash = url;
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
	function load_selection(data) {
		if (!autoclick)
			window.location.hash = hash = serialize(data);
		var responseData = cached[data];
		if (responseData) {
			__update_tags(responseData['tags']);
			__update_dates(responseData['dates']);
			__update_results(responseData['results']);
			__update_paginator(responseData['pages'], data);
			release_request();
		} else {
			var have_articles = $("#results li")
				.not("#IE6_PLACEHOLDER")
				.map(function() {
						return $(this).attr("id").substring(4); // art_
					}).get();
			request = $.getJSON("/ajax/paginator",
				{"tags": data[0], "page": data[1], "have_articles": have_articles,
				 "date_min": data[2], "date_max": data[3]},
				function(responseData) {
					__update_tags(responseData['tags']);
					__update_dates(responseData['dates']);
					__update_results(responseData['results']);
					__update_paginator(responseData['pages'], data);
					responseData['results']['new'] = null;
					cached[data] = responseData;
					release_request();
				});
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
		window.status = null;
		request = null;
		if (activelink)
			activelink.removeClass("active");
		activelink = null;
		if (!autoclick) {
			window.scroll(0,0);
		}
		autoclick = false;
	}

	function __redraw_showall() {
		if (!$("#tags li").not("#alltags").hasClass("activetag") && !$("#dates li").hasClass("activedate"))
			$("#tags #alltags").addClass("activetag");
		else
			$("#tags #alltags").removeClass("activetag");
	}

	function __update_tags(taginfo) {
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

	function __update_dates(dates) {
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

	function __update_results(results) {
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

	function __update_paginator(pages, data) {
		$("#paginator").empty();
		if (pages['num_pages'] > 1) {
			for (var i = 1; i <= pages['num_pages']; i++) {
				if (i == pages['this_page'])
					$("#paginator").append(" <li>" + i + "</li>");
				else
					$("#paginator").append(" <li id=\"n_"
					+ i + "\" class=\"pagelink\"><a href=\"#"
					+ serialize([data[0],i,data[2],data[3]])
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

	// without the #
	function deserialize(hash) {
		if (!(hash instanceof Array) && hash.substring(0,1) != "/") {
			hash = hash.split(",");
			hash[0] = hash[0].split(";");
		}
		return hash;
	}

	function serialize(selection) {
		return selection[0].join(";") + "," + selection.slice(1);
	}
});
