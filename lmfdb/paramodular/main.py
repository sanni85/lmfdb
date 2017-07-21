# -*- coding: utf-8 -*-
import re
import pymongo
ASC = pymongo.ASCENDING
LIST_RE = re.compile(r'^(\d+|(\d+-\d+))(,(\d+|(\d+-\d+)))*$')

from flask import render_template, request, url_for, make_response, redirect, flash, send_file

from lmfdb.base import getDBConnection
from lmfdb.utils import to_dict, random_object_from_collection, web_latex_split_on_pm

from sage.all import QQ, PolynomialRing, PowerSeriesRing, conway_polynomial, prime_range, latex

from lmfdb.paramodular import paramodular_page
#from lmfdb.paramodular.paramodular_stats import get_stats    #needs to be done
from lmfdb.search_parsing import parse_ints, parse_count, parse_start

from markupsafe import Markup

import time
import ast
import StringIO

paramodular_credit = 'Samuele Anni, Malcolm Rupert'


#breadcrumbs and links for data quality entries

def get_bread(breads=[]):
    bc = [("Paramodular Forms", url_for(".index"))]
    for b in breads:
        bc.append(b)
    return bc

def learnmore_list():
    return [('Completeness of the data', url_for(".completeness_page")),
            ('Source of the data', url_for(".how_computed_page")),
            ('Labels', url_for(".labels_page"))]

# Return the learnmore list with the matchstring entry removed
def learnmore_list_remove(matchstring):
    return filter(lambda t:t[0].find(matchstring) <0, learnmore_list())


# webpages: main, random and search results
@paramodular_page.route("/")
def paramodular_render_webpage():
    args = request.args
    if len(args) == 0:
        info=[]
        credit = paramodular_credit
        t = 'Paramodular Forms'
        bread = [('Modular Forms', "/ModularForm"),('Paramodular Forms', url_for(".paramodular_render_webpage"))]
        return render_template("paramodular-index.html", info=info, credit=credit, title=t, learnmore=learnmore_list_remove('Completeness'), bread=bread)
    else:
        return paramodular_search(**args)


# Random paramodular
@paramodular_page.route("/random")
def random_paramodular():
    res = random_object_from_collection( getDBConnection().siegel_modular_forms.paramodular_lifts )
    return redirect(url_for(".render_paramodular_webpage", label=res['label']))

paramodular_label_regex = re.compile(r'(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d*)')

def split_paramodular_label(lab):
    return paramodular_label_regex.match(lab).groups()

def paramodular_by_label(lab, C):
    if C.mod_l_eigenvalues.paramodular.find({'label': lab}).limit(1).count() > 0:
        return render_paramodular_webpage(label=lab)
    if paramodular_label_regex.match(lab):
        flash(Markup("The mod &#x2113; modular form <span style='color:black'>%s</span> is not recorded in the database or the label is invalid" % lab), "error")
    else:
        flash(Markup("No mod &#x2113; modular form in the database has label <span style='color:black'>%s</span>" % lab), "error")
    return redirect(url_for(".paramodular_render_webpage"))


def paramodular_search(**args):
    C = getDBConnection()
    info = to_dict(args)  # what has been entered in the search boxes

    if 'download' in info:
        return download_search(info)

    if 'label' in info and info.get('label'):
        return paramodular_by_label(info.get('label'), C)
    query = {}
    try:
        for field, name in (('characteristic','Field characteristic'),('deg','Field degree'),('level', 'Level'),
                            ('conductor','Conductor'), ('weight_grading', 'Weight grading')):
            parse_ints(info, query, field, name)
    except ValueError as err:
        info['err'] = str(err)
        return search_input_error(info)

# miss search by character, search up to twists and gamma0, gamma1

    count = parse_count(info,50)
    start = parse_start(info)

    info['query'] = dict(query)
    res = C.mod_l_eigenvalues.paramodular.find(query).sort([('characteristic', ASC), ('deg', ASC), ('level', ASC), ('weight_grading', ASC)]).skip(start).limit(count)
    nres = res.count()

    if(start >= nres):
        start -= (1 + (start - nres) / count) * count
    if(start < 0):
        start = 0

    info['number'] = nres
    info['start'] = int(start)
    info['more'] = int(start + count < nres)
    if nres == 1:
        info['report'] = 'unique match'
    else:
        if nres == 0:
            info['report'] = 'no matches'
        else:
            if nres > count or start != 0:
                info['report'] = 'displaying matches %s-%s of %s' % (start + 1, min(nres, start + count), nres)
            else:
                info['report'] = 'displaying all %s matches' % nres

    res_clean = []
    for v in res:
        v_clean = {}
        for m in ['label','characteristic','deg','level','weight_grading']:
            v_clean[m]=v[m]
        res_clean.append(v_clean)

    info['paramodulars'] = res_clean
    t = 'Mod &#x2113; Modular Forms Search Results'
    bread=[('Modular Forms', "/ModularForm"),('mod &#x2113;', url_for(".paramodular_render_webpage")),('Search Results', ' ')]
    properties = []
    return render_template("paramodular-search.html", info=info, title=t, properties=properties, bread=bread, learnmore=learnmore_list())

def search_input_error(info, bread=None):
    t = 'mod &#x2113; Modular Forms Search Error'
    if bread is None:
        bread=[('Modular Forms', "/ModularForm"),('mod &#x2113;', url_for(".paramodular_render_webpage")),('Search Results', ' ')]
    return render_template("paramodular-search.html", info=info, title=t, properties=[], bread=bread, learnmore=learnmore_list())



@paramodular_page.route('/<label>')
def render_paramodular_webpage(**args):
    C = getDBConnection()
    data = None
    if 'label' in args:
        lab = args.get('label')
        data = C.mod_l_eigenvalues.paramodular.find_one({'label': lab })
    if data is None:
        t = "Mod &#x2113; modular form search error"
        bread = [('mod &#x2113; Modular Forms', url_for(".paramodular_render_webpage"))]
        flash(Markup("Error: <span style='color:black'>%s</span> is not a valid label for a mod &#x2113; modular form in the database." % (lab)),"error")
        return render_template("paramodular-error.html", title=t, properties=[], bread=bread, learnmore=learnmore_list())
    info = {}
    info.update(data)

    info['friends'] = []

    bread=[('Modular Forms', "/ModularForm"),('mod &#x2113;', url_for(".paramodular_render_webpage")), ('%s' % data['label'], ' ')]
    credit = paramodular_credit

    f = C.mod_l_eigenvalues.paramodular.find_one({'characteristic':data['characteristic'], 'deg' : data['deg'], 'level' : data['level'],'weight_grading': data['weight_grading'], 'reducible' : data['reducible'], 'cuspidal_lift': data['cuspidal_lift'], 'dirchar' : data['dirchar'], 'atkinlehner': data['atkinlehner'],'n_coeffs': data['n_coeffs'],'coeffs': data['coeffs'], 'ordinary': data['ordinary'],'min_theta_weight': data['min_theta_weight'], 'theta_cycle' : data['theta_cycle']})

    for m in ['characteristic','deg','level','weight_grading', 'n_coeffs', 'min_theta_weight', 'ordinary']:
        info[m]=int(f[m])
    info['atkinlehner']=f['atkinlehner']
    info['dirchar']=str(f['dirchar'])
    info['label']=str(f['label'])
    if f['reducible']:
        info['reducible']=f['reducible']
    info['cuspidal_lift']=f['cuspidal_lift']
    info['cuspidal_lift_weight']=int(f['cuspidal_lift'][0])
    info['cuspidal_lift_orbit']=str(f['cuspidal_lift'][1])

    if f['cuspidal_lift'][2]=='x':
        info['cuspidal_hecke_field']=1
    else:
        info['cuspidal_hecke_field']=latex(f['cuspidal_lift'][2])

    info['cuspidal_lift_gen']=f['cuspidal_lift'][3]

    if f['theta_cycle']:
        info['theta_cycle']=f['theta_cycle']

    info['coeffs']=[str(s).replace('x','a').replace('*','') for s in f['coeffs']]

    if f['deg'] != int(1):
        try:
            pol=str(conway_polynomial(f['characteristic'], f['deg'])).replace('x','a').replace('*','')
            info['field']= pol
        except:
            info['field']=""


    ncoeff=int(round(20/f['deg']))
    av_coeffs=min(f['n_coeffs'],100)
    info['av_coeffs']=int(av_coeffs)
    if f['coeffs'] != "":
        coeff=[info['coeffs'][i] for i in range(ncoeff+1)]
        info['q_exp']=my_latex(print_q_expansion(coeff))
        info['q_exp_display'] = url_for(".q_exp_display", label=f['label'], number="")
        p_range=prime_range(av_coeffs)
        info['table_list']=[[p_range[i], info['coeffs'][p_range[i]]] for i in range(len(p_range))]
        info['download_q_exp'] = [
            (i, url_for(".render_paramodular_webpage_download", label=info['label'], lang=i)) for i in ['gp', 'magma','sage']]

        t = "Mod "+str(info['characteristic'])+" Modular Form "+info['label']
    info['properties'] = [
        ('Label', '%s' %info['label']),
        ('Field characteristic', '%s' %info['characteristic']),
        ('Field degree', '%s' %info['deg']),
        ('Level', '%s' %info['level']),
        ('Weight grading', '%s' %info['weight_grading'])]
    return render_template("paramodular-single.html", info=info, credit=credit, title=t, bread=bread, properties2=info['properties'], learnmore=learnmore_list())



#auxiliary function for displaying more coefficients of the theta series
@paramodular_page.route('/q_exp_display/<label>/<number>')
def q_exp_display(label, number):
    try:
        number = int(number)
    except:
        number = 20
    if number < 20:
        number = 20
    if number > 150:
        number = 150
    C = getDBConnection()
    data = C.mod_l_eigenvalues.paramodular.find_one({'label': label})
    coeff=[data['coeffs'][i] for i in range(number+1)]
    return print_q_expansion(coeff)


#data quality pages
@paramodular_page.route("/Completeness")
def completeness_page():
    t = 'Completeness of the mod &#8467; modular form data'
    bread=[('Modular Forms', "/ModularForm"),('mod &#x2113;', url_for(".paramodular_render_webpage")),('Completeness', '')]
    credit = paramodular_credit
    return render_template("single.html", kid='dq.paramodular.extent',
                           credit=credit, title=t, bread=bread, learnmore=learnmore_list_remove('Completeness'))

@paramodular_page.route("/Source")
def how_computed_page():
    t = 'Source of the mod &#8467; modular form data'
    bread=[('Modular Forms', "/ModularForm"),('mod &#x2113;', url_for(".paramodular_render_webpage")),('Source', '')]
    credit = paramodular_credit
    return render_template("single.html", kid='dq.paramodular.source',
                           credit=credit, title=t, bread=bread, learnmore=learnmore_list_remove('Source'))

@paramodular_page.route("/Labels")
def labels_page():
    t = 'Label of a mod &#x2113; modular forms'

    bread=[('Modular Forms', "/ModularForm"),('mod &#x2113;', url_for(".paramodular_render_webpage")), ('Labels', '')]
    credit = paramodular_credit
    return render_template("single.html", kid='paramodular.label',
                           credit=credit, title=t, bread=bread, learnmore=learnmore_list_remove('Labels'))

#download
download_comment_prefix = {'magma':'//','sage':'#','gp':'\\\\'}
download_assignment_start = {'magma':'data := ','sage':'data = ','gp':'data = '}
download_assignment_end = {'magma':';','sage':'','gp':''}
download_file_suffix = {'magma':'.m','sage':'.sage','gp':'.gp'}

def download_search(info):
    lang = info["submit"]
    filename = 'mod_l_modular_forms' + download_file_suffix[lang]
    mydate = time.strftime("%d %B %Y")
    # reissue saved query here

    res = getDBConnection().mod_l_eigenvalues.paramodulars.find(ast.literal_eval(info["query"]))

    c = download_comment_prefix[lang]
    s =  '\n'
    s += c + ' Mod l modular forms downloaded from the LMFDB on %s. Found %s mod l modular forms.\n\n'%(mydate, res.count())
    s += ' Each entry is given in the following format: field characteristic, field degree, level, minimal weight, conductor.\n\n'
    list_start = '[*' if lang=='magma' else '['
    list_end = '*]' if lang=='magma' else ']'
    s += download_assignment_start[lang] + list_start + '\\\n'
    for r in res:
        for m in ['characteristic', 'deg', 'level', 'min_weight', 'conductor']:
            s += ",\\\n".join(str(r[m]))
    s += list_end
    s += download_assignment_end[lang]
    s += '\n'
    strIO = StringIO.StringIO()
    strIO.write(s)
    strIO.seek(0)
    return send_file(strIO, attachment_filename=filename, as_attachment=True, add_etags=False)


@paramodular_page.route('/<label>/download/<lang>/')
def render_paramodular_webpage_download(**args):
    response = make_response(download_paramodular_full_lists(**args))
    response.headers['Content-type'] = 'text/plain'
    return response



def download_paramodular_full_lists(**args):
    C = getDBConnection()
    label = str(args['label'])
    res = C.mod_l_eigenvalues.paramodular.find_one({'label': label})
    mydate = time.strftime("%d %B %Y")
    if res is None:
        return "No such paramodular"
    lang = args['lang']
    c = download_comment_prefix[lang]
    outstr = c + ' List of q-expansion coefficients downloaded from the LMFDB on %s. \n\n'%(mydate)
    if lang == 'magma':
        outstr += 'F<x>:=FiniteField(%s,%s); \n' %(res['characteristic'], res['deg'])

    elif lang == 'sage':
        outstr += 'F.<x>=GF(%s^(%s), conway_polynomial(%s,%s)) \n'%(res['characteristic'], res['deg'], res['characteristic'], res['deg'])

    outstr += '\\\n'
    outstr += download_assignment_start[lang] + '\\\n'
    outstr += str(res['coeffs']).replace("'", "").replace("u", "")
    outstr += download_assignment_end[lang]
    outstr += '\n'
    return outstr
