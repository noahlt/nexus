$(document).ready(function() {

	var current_page; // not quite the same as the last history item
	var history = [];
	var cached = new Object();
	history.push(current_page = 1);

	// for handling concurrency
	var request = null;
	var activelink = null;
	var oldtag = null; // active but to be superceded by another
	// special case since tag-width changing is done BEFORE the request completes
	var newtag = null;

	var selecting_dates = false;
	var down;
	var DATE_MIN = 100001;
	var DATE_MAX = 300001;
	var TAG_NORMAL = $("#alltags").width();
	var TAG_EXPANDED = TAG_NORMAL + 13;
	$("#tags #alltags").width(TAG_EXPANDED);

	function click_page(event) {
		event.preventDefault();
		activelink = $(this).addClass("active");
		update($(this).attr("id").substring(2)); // n_
	}

	// call before ajax request; aborts previous ones
	// set request/activelink AFTER calling
	// set newtag BEFORE calling
	function acquire_request() {
		if (request) {
			request.abort();
			request = null;
		}
		if (activelink) {
			activelink.removeClass("active");
			activelink = null;
		}
		if (oldtag) { // abort the old tag
			if (!newtag || newtag.attr("id") != "alltags") // because alltags deactivates them all
				oldtag.toggleClass("activetag");
			if (oldtag.attr("id") != "alltags") {
				if (oldtag.hasClass("activetag"))
					oldtag.width(TAG_EXPANDED);
				else
					oldtag.width(TAG_NORMAL);
			}
			oldtag = null;
		}
		oldtag = newtag; // set this as the old one now
		newtag = null;
		window.status = "Sent XMLHttpRequest...";
	}

	// call at end of dom update
	function release_request() {
		window.status = null;
		window.scroll(0,0); // misc
		request = null;
		if (activelink)
			activelink.removeClass("active");
		activelink = null;
		oldtag = null;
	}

	// back to previous page
	function go_back() {
		if (current_page != 1 && history.length > 0) {
			var i = history.pop();
			while (current_page == i && history.length > 0)
				i = history.pop();
			update(i);
			return false;
		} else if (!$("#alltags").hasClass("activetag")) {
			$("#alltags").click();
			return false;
		}
	}

	// load link into center column
	function click_embed(event) {
		event.preventDefault();
		acquire_request();
		history.push(current_page = null);
		activelink = $(this).addClass("active");
		url = $(this).attr("href");
		if (url.match("http://")) { // whatever IE is doing, undo it
			url = url.substring(7);
			url = url.substring(url.indexOf("/"));
		}
		request = $.get("/ajax/embed" + url, function(responseData) {
			$("#embedded_content").html(responseData);
			grab_links();
			$(".results").hide();
			$(".embed").show();
			release_request();
		}, "html");
	}

	function click_tag(event) {
		event.preventDefault();
		$("#alltags").click();
		slug = $(this).attr("href").substring(5); // XXX strip /tag/
		$("#tag_" + slug).click();
		update(1);
	}

	// call after new stuff is loaded to bind javascript functions
	function grab_links() {
		$(".articlelink").click(click_embed);
		$(".taglink").click(click_tag);
		$("a[@href*=/author/]").click(click_embed); // .authorlink
		$("a[@href*=/info/]").click(click_embed); // .infolink
		$("a[@href*=/image/]").click(click_embed); // .imagelink
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
	}

	function __update_paginator(pages) {
		$("#paginator").empty();
		if (pages['num_pages'] > 1) {
			for (var i = 1; i <= pages['num_pages']; i++) {
				if (i == pages['this_page'])
					$("#paginator").append(" <li>" + i + "</li>");
				else
					$("#paginator").append(" <li id=\"n_"
					+ i + "\" class=\"pagelink\" href=\"#paginator\"><a>"
					+ i + "</a></li>");
			}
		}
		$("#paginator .pagelink").click(click_page);
	}

	function update(page) {
		acquire_request();
		history.push(current_page = page);
		__redraw_showall();
		var min = DATE_MIN, max = DATE_MAX;
		var selected_dates = $("#dates .activedate").map(function() {
				return $(this).attr('id').substring(3); // ym_
			}).get();
		if (selected_dates.length > 0) {
			min = Math.min.apply(null, selected_dates);
			max = Math.max.apply(null, selected_dates);
			$("#dates li li").not(".activedate").map(function() {
				var date = $(this).attr('id').substring(3); // ym_
				if (date > min && date < max)
					$(this).addClass("activedate");
			});
		}
		var selectedtags = $("#tags li").filter(".activetag").not("#alltags")
			.map(function() {
					return $(this).attr("id").substring(4); // tag_
				}).get();
		var have_articles = $("#results li")
			.not("#IE6_PLACEHOLDER")
			.map(function() {
					return $(this).attr("id").substring(4); // art_
				}).get();
		var responseData = cached[[selectedtags, page, min, max]];
		if (responseData) {
			__update_tags(responseData['tags']);
			__update_dates(responseData['dates']);
			__update_results(responseData['results']);
			__update_paginator(responseData['pages']);
			release_request();
		} else {
			request = $.get("/ajax/paginator",
				{"tags": selectedtags, "page": page, "have_articles": have_articles,
				 "date_min": min, "date_max": max},
				function(responseData) {
					__update_tags(responseData['tags']);
					__update_dates(responseData['dates']);
					__update_results(responseData['results']);
					__update_paginator(responseData['pages']);
					responseData['results']['new'] = null;
					cached[[selectedtags, page, min, max]] = responseData;
					release_request();
				}, "json");
		}
	}

	$("#paginator .pagelink").click(click_page);

	$("#tags li").not("#alltags").click(function() {
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
		newtag = $(this);
		update(1);
	});

	$("#tags #alltags").click(function() {
		$("#dates li").removeClass("activedate");
		selecting_dates = false;
		$("#tags li").removeClass("useless");
		$("#tags .activetag").not("#alltags")
			.removeClass("activetag")
			.width(TAG_NORMAL);
		newtag = $(this);
		update(1);
	});

	$("#tags li a").click(function(event) {
		event.preventDefault();
	});

	$("#back_button a").click(go_back);
	grab_links();

	$("#dates h3").click(function() {
		var min = ($(this).text() - 1) + "08";
		var max = $(this).text() + "07";
		var deselect = true;
		$("#dates li li").map(function() {
			var date = $(this).attr('id').substring(3); // ym_
			if (date >= min && date <= max) {
				if (!$(this).hasClass("activedate"))
					deselect = false;
				$(this).addClass("activedate");
			} else {
				$(this).removeClass("activedate");
			}
		});
		if (deselect)
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

	document.onmouseup = function() {
		if (selecting_dates) {
			selecting_dates = false;
			update(1);
		}
	};

	document.onkeypress = function(x) {
		var e = window.event || x;
		var keyunicode = e.charCode || e.keyCode;
		return keyunicode == 8 ? go_back() : true;
	};
});

// vim:noexpandtab
