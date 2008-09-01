$(document).ready(function() {
	$(".articlelink").click(function(event) {
		event.preventDefault();
		var target = $("." + $(this).attr("id")).filter("div");
		if (!target.hasClass("visible")) {
			$(".hidden-snippet").removeClass("visible").hide();
			target.show();
		} else {
			target.hide();
		}
		target.toggleClass("visible");
	});
});
