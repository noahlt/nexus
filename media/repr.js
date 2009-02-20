var DATE_MIN = 100001;
var DATE_MAX = 300001;
var DEFAULT_PAGE = 1;
var DEFAULT_URL = '';
var FS = ',';
var FS2 = '.';

if (location.pathname != "/") {
	var page_match = location.pathname.match(/^\/[0-9]+$/);
	if (page_match)
		DEFAULT_PAGE = page_match.toString().substring(1);
	else {
		DEFAULT_URL = location.pathname;
		if (DEFAULT_URL.charAt(DEFAULT_URL.length-1) == '/')
			DEFAULT_URL = DEFAULT_URL.substring(0, DEFAULT_URL.length-1);
	}
} else if (STATIC_FRONTPAGE)
	DEFAULT_URL = '/cover';

function Repr(dict) {
	this.query = '';
	this.url = '';
	this.page = 0;
	this.tags = [];
	this.date_min = DATE_MIN;
	this.date_max = DATE_MAX;

	if (this.page == 1 && this.tags.length === 0 && this.date_min == DATE_MIN && this.date_max == DATE_MAX && !this.query)
		this.page = DEFAULT_PAGE;

	for (var i in dict)
		this[i] = dict[i];

	if (!this.url && this.tags.length === 0 && this.date_min == DATE_MIN && this.date_max == DATE_MAX && !this.page && !this.query)
		this.url = DEFAULT_URL;

	if (!this.page)
		this.page = 1;

	this.toString = function() {
		return 'Repr Object ' + this.serialize();
	};

	this.serialize = function(nav_attrs_only) {
		var output = [];
		var have_embed = false;
		if (!nav_attrs_only && this.url) {
			if (this.url != DEFAULT_URL)
				output[output.length] = this.url;
			have_embed = true;
		}
		if (this.tags.length > 0)
			output[output.length] = 'tags=' + this.tags.join(FS2);
		if (this.date_min == this.date_max)
			output[output.length] = 'month=' + this.date_min;
		else {
			if (this.date_min != DATE_MIN)
				output[output.length] = 'min=' + this.date_min;
			if (this.date_max != DATE_MAX)
				output[output.length] = 'max=' + this.date_max;
		}
		if (!nav_attrs_only && !have_embed) {
			if (this.query)
				output[output.length] = 'query=' + this.query;
			else if (output.length === 0)
				output[output.length] = 'page=' + this.page;
		}
		return '#' + output.join(FS);
	};
}

Repr.deserialize = function(hash) {
	var attrs = {};
	if (hash.charAt(0) == '#')
		hash = hash.substring(1);
	var chunks = hash.split(FS);
	for (var i in chunks) {
		var chunk = chunks[i];
		if (attrs['query'])
			attrs['query'] += ',' + chunk;
		else if (chunk.substring(0,1) == '/')
			attrs['url'] = chunk;
		else if (chunk.substring(0,5) == 'tags=')
			attrs['tags'] = chunk.substring(5).split(FS2);
		else if (chunk.substring(0,5) == 'page=')
			attrs['page'] = chunk.substring(5);
		else if (chunk.substring(0,6) == 'month=')
			attrs['date_min'] = attrs['date_max'] = chunk.substring(6);
		else if (chunk.substring(0,4) == 'min=')
			attrs['date_min'] = chunk.substring(4);
		else if (chunk.substring(0,4) == 'max=')
			attrs['date_max'] = chunk.substring(4);
		else if (chunk.substring(0,6) == 'query=')
			attrs['query'] = chunk.substring(6);
	}
	return new Repr(attrs);
};
