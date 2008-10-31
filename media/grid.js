$(document).ready(function() {

	if (!dump) function dump() {}

	var DATE_MIN = 100001;
	var DATE_MAX = 300001;
	var TAG_NORMAL = $("#alltags").width();
	var TAG_EXPANDED = TAG_NORMAL + 13;
	var FS = ",", FS2 = ".";
	var IFRAME = $("iframe").size() > 0;

	// takes (#serializedstate) or (/path/to/url, [[tags],page,dmin,dmax])
	// for the second any nulls will be replaced by default values
	function State(arg1, sel) {
        dump("New state created: " + arg1 + " " + sel + "\n");
		change_hash = true;
		url = '';
		selection = [[], 1, DATE_MIN, DATE_MAX];
		if (arg1 && arg1.charAt(0) == "#") {
			dump("Deserialization: " + arg1 + "\n");
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
			if (url)
				url = arg1;
			if (sel)
				selection = sel;
		}
		this.page = function(num) {
            dump("Set page " + num + "\n");
			selection[1] = num;
			return this;
		};
		this.enter = function(link) {
            dump("Entering: " + (link ? link.attr("href") : 'null') + "\n");
			State.acquire_request();
			if (link) {
				State.activelink = link.addClass("active");
				url = link.attr("href");
				if (url && url.match("http://")) { // make relative
					url = url.substring(7);
					url = url.substring(url.indexOf("/"));
				}
			}
			if (change_hash || IFRAME) { // always do this on IE6/7
				window.location.hash = State.hash = this.toString();
				if (change_hash && IFRAME) {
					var doc = document.getElementById("iFrame").contentWindow.document;
					doc.open();
					doc.write(this);
					doc.close();
				}
			} else
				State.hash = window.location.hash.substring(1);
			State.select_tags(selection[0]);
			State.select_dates(selection[2], selection[3]);
			if (url) {
				State.load_url(url);
				State.load_selection(selection, true);
			} else
				State.load_selection(selection);
		};
		this.toString = function() {
			var output = [];
			if (url)
				output[output.length] = url;
			if (selection[0] && selection[0].length > 0)
				output[output.length] = "tags=" + selection[0].join(FS2);
			if (selection[1] != 1)
				output[output.length] = "page=" + selection[1];
			if (selection[2] == selection[3]) {
				output[output.length] = "month=" + selection[2];
			} else {
				if (selection[2] != DATE_MIN)
					output[output.length] = "min=" + selection[2];
				if (selection[3] != DATE_MAX)
					output[output.length] = "max=" + selection[3];
			}
			if (output.length == 0)
				return '#';
			else
				return output.join(FS);
		};
		this.keep_hash = function() {
            dump("Hash change inhibited.\n");
			change_hash = false;
			return this;
		};
	}
	State.scroll_flag = false;
	State.init_ms = new Date().getTime();
	State.disabled = false;
	State.request_count = 0;
	State.cached = new Object();
	State.activelink = null;
	State.hash = window.location.hash.substring(1);
	State.check_and_incr = function() {
        if (State.disabled)
            throw "ProbablyStuckInLoop";
		var dt = new Date().getTime() - State.init_ms;
		if (State.request_count++ / (10+(dt/1000)) > 1) {
			alert("This script appears to be stuck in an infinite loop.\n("
			+ State.request_count + " requests in " + (dt/1000)
			+ " seconds)\n\nPlease report this bug.");
            State.disabled = true;
        }
	};
	State.scrollup = function() {
		State.scroll_flag = true;
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
        dump("GET " + url + "\n");
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
	State.load_selection = function(selection, just_url_update) {
		var hit = State.cached[selection];
        dump("getJSON\n");
		function load(data) {
			State.read_json_tags(data['tags']);
			State.read_json_dates(data['dates']);
			if (!just_url_update) {
				State.read_json_results(data['results']);
				State.read_json_paginator(data['pages'], selection);
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
			dump("Cache hit!\n");
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
				 "date_min": selection[2], "date_max": selection[3]}, load);
			else
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
			dump("Aborted request " + State.request + "\n");
			State.scrollup = false;
			State.request.abort();
			State.request = null;
		}
		if (State.request2) {
			dump("Aborted secondary request " + State.request + "\n");
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
        dump("\n");
		window.status = "Done";
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
	State.grab_links = function() {
		$("a").filter(".embeddable").unbind().click(function(event) {
			if (event.ctrlKey || event.shiftKey)
				return;
			event.preventDefault();
			State.current().enter($(this));
			State.scrollup();
		});
		$("#paginator .pagelink").unbind().click(function(event) {
			event.preventDefault();
			State.current().page($(this).attr("id").substring(2)).enter();
			State.scrollup();
		});
		$("#goto_top").unbind().click(function() {
			window.scroll(0,0);
		});
	};

	// redirect to hash id if possible for better functionality
	if (window.location.pathname != "/")
		location.replace("/#" + new State(window.location.pathname));

	var selecting_dates = false;
	var down = false;
	$("#tags #alltags").width(TAG_EXPANDED);
	$("#tags").disableTextSelect();
	$("#dates").disableTextSelect();
	State.grab_links();

	if (window.location.hash.length > 1) // permalink and not lone '#'
		new State(window.location.hash).enter();

	function different(framehtml, hash) {
		if (framehtml == hash || (!framehtml && hash == new State()))
			return false;
		return true;
	}

	setInterval(function() {
		if (window.location.hash.substring(1) != State.hash) {
			State.check_and_incr();
			new State(window.location.hash).keep_hash().enter();
		} else if (IFRAME && window["iFrame"].document.body && different(window["iFrame"].document.body.innerHTML, State.hash)) {
			State.check_and_incr();
			new State("#" + window["iFrame"].document.body.innerHTML).keep_hash().enter();
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
		State.current().page(1).enter();
		State.scrollup();
	});

	$("#tags #alltags").click(function(event) {
        event.preventDefault();
		$("#dates li").removeClass("activedate");
		selecting_dates = false;
		$("#tags li").removeClass("useless");
		$("#tags .activetag").removeClass("activetag");
		State.current().enter();
		State.scrollup();
	});

	$("#tags li a").click(function(event) {
        if (event.ctrlKey || event.shiftKey)
            return;
		event.preventDefault();
	});

	$("#dates h3").click(function(event) {
        event.preventDefault();
		var min = ($(this).text().substring(5) - 1) + "08";
		var max = $(this).text().substring(5) + "07"; // year_
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

	if ($("#IE6_PLACEHOLDER").size() > 0) {
		$('#tags li').animate({'width':'+=0'}); // hover only works after this...
		$('#tags li').hover(function() {
			if (!$(this).hasClass("useless"))
				$(this).css('filter','alpha(opacity=80)');
		}, function() {
			$(this).css('filter','alpha(opacity=100)');
		});
	}
});
