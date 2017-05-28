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

from lmfdb.base import getDBConnection

C= getDBConnection()
import yaml
pw_dict = yaml.load(open(os.path.join(os.getcwd(), "passwords.yaml")))
username = pw_dict['data']['username']
password = pw_dict['data']['password']
C['mod_l_eigenvalues'].authenticate('editor', password)
Dirichlet_gps = C['mod_l_eigenvalues'].Dirichlet_gp_modl

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


Dirichlet_gps.create_index('characteristic')
Dirichlet_gps.create_index('modulus')
Dirichlet_gps.create_index('order')


print "indices updated"


## Main importing function


def do_import(ll):
    characteristic,modulus,order,gens_modulus,gens_gp,elements = ll
    mykeys =['characteristic','modulus','order','gens_modulus','gens_gp','elements']
    data = {}
    for j in range(len(mykeys)):
        data[mykeys[j]] = ll[j]
    data['label'] = '-'.join([str(data['characteristic']),str(data['modulus'])])

    Dirichlet_gp = Dirichlet_gps.find_one({'label': data['label']})

    if Dirichlet_gp is None:
        print "new Dirichlet group mod l"
        Dirichlet_gp = data
    else:
        print "Dirichlet group mod l already in the database"
        Dirichlet_gp.update(data)
    if saving:
        Dirichlet_gps.update({'label': data['label']} , {"$set": Dirichlet_gp}, upsert=True)



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
