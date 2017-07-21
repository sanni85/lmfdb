# -*- coding: utf-8 -*-
from lmfdb.base import app
from lmfdb.utils import make_logger
from flask import Blueprint

paramodular_page = Blueprint("paramodular", __name__, template_folder='templates', static_folder="static")
paramodular_logger = make_logger(paramodular_page)


@paramodular_page.context_processor
def body_class():
    return {'body_class': 'paramodular'}

import main
assert main

app.register_blueprint(paramodular_page, url_prefix="/ModularForm/GSp/Paramodular/")

