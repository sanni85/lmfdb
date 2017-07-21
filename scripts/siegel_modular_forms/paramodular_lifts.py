# -*- coding: utf-8 -*-
r""" Import mod l modular forms.  

Note: This code can be run on all files in any order. Even if you 
rerun this code on previously entered files, it should have no affect.  
This code checks if the entry exists, if so returns that and updates 
with new information. If the entry does not exist then it creates it 
and returns that.

"""

import sys
import re
import json
import os
import gzip

from pymongo.mongo_client import MongoClient
C= MongoClient(port=37010)
import yaml
pw_dict = yaml.load(open(os.path.join(os.getcwd(), "passwords.yaml")))
username = pw_dict['data']['username']
password = pw_dict['data']['password']
C['siegel_modular_forms'].authenticate('editor', password)
para = C.siegel_modular_forms.paramodular_lifts

saving = True 

def sd(f):
  for k in f.keys():
    print '%s ---> %s'%(k, f[k])

def makels(li):
  li2 = [str(x) for x in li]
  return ','.join(li2)

def string2list(s):
  s = str(s)
  if s=='': return []
  return [int(a) for a in s.split(',')]

# The following create_index command checks if there is an index on
# label, dimension, determinant and level. 


para.create_index('level')
para.create_index('weight')

print "finished indices"

## Main importing function

label_dict={}

def base_label_yoshida_trivial(degree,level, weight):  #trivial character, only Yoshida lifts
    return ".".join([str(degree),str(level),str(weight),"1","yo"])

def last_label(base_label, n):
    return ".".join([str(base_label),str(n)])
    
def label_lookup(base_label):
    if base_label in label_dict:
        n=label_dict[base_label]+1
        label_dict[base_label]=n
        return n
    label_dict[base_label]=1
    return 1

def do_import(ll):
    degree,level,weight,character,gritsenko,yoshida,eigenvalues,al_eigen = ll
    mykeys =['degree','level','weight','character','gritsenko','yoshida','eigenvalues','al_eigen']
    data = {}
    for j in range(len(mykeys)):
        data[mykeys[j]] = ll[j]

    blabel = base_label_yoshida_trivial(data['degree'],data['level'], data['weight'])
    data['base_label'] = blabel
    data['index'] = label_lookup(blabel)
    label= last_label(blabel, data['index'])
    data['label'] = label
    # we need still to organize this better with respect to tie breaks, in particular better use ordering of hecke eigenvalues

    para_search = para.find_one({'label': label})

    if para_search is None:
        print "new paramodular form"
        para_search = data
    else:
        print "paramodular form already in the database"
        para_search.update(data)
    if saving:
        para.update({'label': label} , {"$set": para_search}, upsert=True)


# Loop over files

for path in sys.argv[1:]:
    print path
    filename = os.path.basename(path)
    fn = gzip.open(path) if filename[-3:] == '.gz' else open(path)
    for line in fn.readlines():
        line.strip()
        if re.match(r'\S',line):
            l = json.loads(line)
            do_import(l)
