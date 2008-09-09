$(document).ready(function() {

	var current_page; // not quite the same as the last history item
	var history = [];
	history.push(current_page = 1);

	var selecting_dates = false;
	var down;
	var DATE_MIN = 100001;
	var DATE_MAX = 300001;

	function click_page(event) {
		event.preventDefault();
		window.scroll(0,0);
		update($(this).attr("id"));
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
					if ($(this).attr("id") == dates[i]) {
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
	}

	function __update_paginator(pages) {
		$("#paginator").empty();
		if (pages['num_pages'] > 1) {
			for (var i = 1; i <= pages['num_pages']; i++) {
				if (i == pages['this_page'])
					$("#paginator").append("\n<li>" + i + "</li>");
				else
					$("#paginator").append("\n<li id=\""
					+ i + "\" class=\"pagelink\" href=\"#paginator\"><a>"
					+ i + "</a></li>");
			}
		}
		$("#paginator .pagelink").click(click_page);
	}

	function update(page) {
		history.push(current_page = page);
		var min = DATE_MIN, max = DATE_MAX;
		var selected_dates = $("#dates .activedate").map(function() {
				return $(this).attr('id');
			}).get();
		if (selected_dates.length > 0) {
			min = Math.min.apply(null, selected_dates);
			max = Math.max.apply(null, selected_dates);
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
		$.get("/ajax/paginator",
			{"tags": selectedtags, "page": page, "have_articles": have_articles,
			 "date_min": min, "date_max": max},
			function(responseData) {
				__update_tags(responseData['tags']);
				__update_dates(responseData['dates']);
				__update_results(responseData['results']);
				__update_paginator(responseData['pages']);
			}, "json");
	}

	$("#paginator .pagelink").click(click_page);

	$("#tags li").not("#alltags").click(function() {
		if ($(this).hasClass("useless"))
			$("#tags .activetag").not("#alltags")
				.removeClass("activetag")
				.width($(this).width());
		tagslug = $(this).attr("id");
		$(this).removeClass("useless");
		$(this).toggleClass("activetag");
		if ($(this).hasClass("activetag")) {
			$(this).width($(this).width() + 13);
			$("#tags #alltags").removeClass("activetag");
		} else {
			$(this).width($(this).width() - 13);
			if (!$("#tags li").hasClass("activetag"))
				$("#tags #alltags").addClass("activetag");
		}
		update(1);
	});

	$("#tags #alltags").click(function() {
		$("#dates li").removeClass("activedate");
		selecting_dates = false;
		$(this).addClass("activetag");
		$("#tags li").removeClass("useless");
		$("#tags .activetag").not("#alltags")
			.removeClass("activetag")
			.width($(this).width() - 13);
		update(1);
	});

	$("#tags li a").click(function(event) {
		event.preventDefault();
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
		if (selecting_dates) {
			$(this).addClass("activedate");
		}
	});

	$("#dates li li").mouseup(function() {
		if (down == $(this).attr("id")) {
			$(this).removeClass("activedate");
		} else if (selecting_dates) {
			$(this).addClass("activedate");
		}
		selecting_dates = false;
		update(1);
	});

	$("#tags").disableTextSelect();
	$("#dates").disableTextSelect();

	document.onkeypress = function(x) {
		var e = window.event || x;
		var keyunicode = e.charCode || e.keyCode;
		if (keyunicode == 8) {
			if (current_page != 1 && history.length > 0) {
				var i = history.pop();
				while (current_page == i && history.length > 0)
					i = history.pop();
				window.scroll(0,0);
				update(i);
				return false;
			} else if (!$("#alltags").hasClass("activetag")) {
				$("#alltags").click();
				return false;
			}
		}
		return true;
	};
});
