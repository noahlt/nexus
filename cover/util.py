# resolves circular imports from archive/cover,
# which really should be merged into one giant app

from datetime import date
from django.http import HttpResponse
from django.template import Context
from django.template.loader import get_template
import simplejson as json

def visible(x):
    return x.filter(date__lte=date.today())

def pagesof(page, pages, adjacent_pages=3):
    ret = [n for n in range(page - adjacent_pages, page + adjacent_pages + 1) if n > 0 and n <= pages]
    while len(ret) < adjacent_pages*2+1 and ret[-1] < pages:
        ret.append(ret[-1]+1)
    while len(ret) < adjacent_pages*2+1 and ret[0] > 1:
        ret.insert(0,ret[0]-1)
    jump_forward = False
    jump_back = False
    if ret[0] > 1:
        jump_back = True
        ret[0] = 1
    if ret[-1] < pages:
        jump_forward = True
        ret[-1] = pages
    return (ret,jump_forward,jump_back)

def render_json(title, template, vars):
    return HttpResponse(
        json.dumps({'html': get_template(template).render(Context(vars)), 'title': 'Nexus | %s' % title})
    )

class SchoolYear(list):
    def __init__(self, year):
        self.year = year;
    def __str__(self):
        return '%s-%s' % (self.year-1, self.year)

def what_school_year(date):
    if date.month <= 7:
        return date.year
    return date.year + 1

def parse_date(input):
    '''Turns an integer date like 200801 into a datetime object like
    datetime.date(2008, 1, 1)'''
    strdate = str(input)
    year = int(strdate[0:4])
    month = int(strdate[4:6])
    return date(year, month, 1)
