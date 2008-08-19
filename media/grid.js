$(document).ready(function() {
    var have_articles = $("#results li h3").map(function() {
        return $(this).attr("className");
        }).get();

    $("#toggleprint").click(function(event) {
        event.preventDefault();
        if ($(this).text()[0] == 'c') {
            $(this).html("expand &darr;");
            $("#print p").hide("fast");
        } else {
            $(this).html("collapse &uarr;");
            $("#print p").show("fast");
        }
        });

    function get_articles(selectedtags) {
        $.get("/ajax/more_articles",
              {"tagslugs":  selectedtags, "have_articles": have_articles},
              function (responseData) {
                  for (var i in responseData) {
                      var article = responseData[i];
                      $("#results").append(article['html']);
                      have_articles[have_articles.length] = article['slug'];
                  }
                  $(".new-article")
                      .show("fast")
                      .removeClass("new-article");
              },
              "json");
    }

    // this selector may have to be changed to be more specific
    $("#grid .controllink").click(function(event) {
        event.preventDefault();
        var selectedtags = $("#tags li").filter(".activetag").not("#alltags")
            .map(function() {
                    return $(this).attr("id");
                }).get();
        get_articles(selectedtags);
        });

    $("#tags li")
        .not("#alltags")
        .click(function() {
            tagslug = $(this).attr("id");
            $(this).toggleClass("activetag");
            var selectedtags = $("#tags li").filter(".activetag")
                .map(function() {
                        return $(this).attr("id");
                    }).get();

            if ($(this).hasClass("activetag")) {
                $(this).animate({width: "+=1em", }, 200);
                $("#results li")
                    .not("."+tagslug)
                    .hide("fast");
                $("#tags #alltags").removeClass("activetag");
                get_articles(selectedtags);

            } else {
                $(this).animate({width: "-=1em", }, 200);
                $("#results li")
                    .not("."+tagslug)
                    .filter(function(i) {
                            for (var j in selectedtags) {
                                if (!$(this).hasClass(selectedtags[j])) {
                                    return false;
                                }
                            }
                            return true;
                        })
                    .show("fast");
                if (!$("#tags li").hasClass("activetag")) {
                    $("#tags #alltags").addClass("activetag");
                }
            }
            });
    
    $("#tags #alltags").click(function() {
        $(this).addClass("activetag");
        $("#tags .activetag").not("#alltags")
            .removeClass("activetag")
            .animate({width: "-=1em",}, 200);
        $("#results li").show("fast");
        });
    
    $("#tags li a").click(function(event) {
            event.preventDefault();
        });

    });
