from lmfdb.base import getDBConnection
from data_mgt.utilities.rewrite import update_attribute_stats

def update_stats(new=False,verbose=True):
    L = getDBConnection().Lattices
    if new:
        l='lat_new'
    else:
        l='lat'
    update_attribute_stats(L,l,'class_number', nocounts=True)
    update_attribute_stats(L,l,'dim', nocounts=True)
    update_attribute_stats(L,l,'det', nocounts=True)


