# -*- coding: utf-8 -*-
r""" Check presence if the first 150 coefficients of the q expansion of the theta series attached to an integral lattice are stored, and adds them otherwise.
     Check if the group structure is stored, otherwise computes it.
Initial version: Samuele Anni
"""
import os
from sage.all import matrix, Magma, QuadraticForm


from pymongo.mongo_client import MongoClient
C= MongoClient(port=37010)
import yaml
pw_dict = yaml.load(open(os.path.join(os.getcwd(), "passwords.yaml")))
username = pw_dict['data']['username']
password = pw_dict['data']['password']
C['Lattices'].authenticate('editor', password)
lat = C.Lattices.lat_new


def check_add_qexp(dim, min_det=1, max_det=None, fix=False):
    query = {}
    query['dim'] = int(dim)
    query['det'] = {'$gte' : int(min_det)}
    if max_det:
        query['det']['$lte'] = int(max_det)
    else:
        max_det = "infinity"
    lat_set = lat.find(query)
    print("%s lattices to examine of dimension %s and determinant between %s and %s."
          % (lat_set.count(), dim, min_det, max_det))
    if lat_set.count() == 0:
        return None
    print("checking whether the q expansion is stored...")
    for l in lat_set:
        print("Testing lattice %s" % l['label'])
        if l['theta_series'] == "":
            print("q expansion NOT stored")
            if fix:
                M=l['gram']
                exp=sage_eval(magma.eval("Coefficients(PowerSeries(ThetaSeriesModularForm(LatticeWithGram(Matrix(%s))), 150));\n" %M).split('\n',1)[0])
                lat.update({'label': l['label']}, {"$set": {'theta_series': exp}}, upsert=True)
                print("Fixed lattice %s" % l['label'])
        else:
            print("q expansion stored")


def check_add_group_str(dim, min_det=1, max_det=None, fix=False):
    query = {}
    query['dim'] = int(dim)
    query['det'] = {'$gte' : int(min_det)}
    if max_det:
        query['det']['$lte'] = int(max_det)
    else:
        max_det = "infinity"
    lat_set = lat.find(query)
    print("%s lattices to examine of dimension %s and determinant between %s and %s."
          % (lat_set.count(), dim, min_det, max_det))
    if lat_set.count() == 0:
        return None
    print("checking whether the automorphism group structure is stored...")
    for l in lat_set:
        print("Testing lattice %s" % l['label'])
        if l['aut'][3]== "":
            print("group structure NOT stored")
            if fix:
                M=l['gram']
                G=QuadraticForm(2*M).automorphism_group()
                if G.oder()!=l['aut'][0]:
                    print "data do not match"
                else:
                    try:
                        structure=.structure_description()
                    except RuntimeError
                        print "RuntimeError"
                        structure="not available"
                    new_aut=l['aut']
                    new_aut[3]= structure
                l.update({'aut': new_aut})
                print("Fixed lattice %s" % l['label'])
        else:
            print("automorphism group structure stored")


