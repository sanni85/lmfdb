# -*- coding: utf-8 -*-
from lmfdb.base import app
from lmfdb.utils import make_logger
from flask import Blueprint

characters_ModL_page = Blueprint("characters_ModL", __name__, template_folder='templates',
    static_folder="static")
logger = make_logger(characters_ModL_page)


@characters_ModL_page.context_processor
def body_class():
    return {'body_class': 'characters_ModL'}

import main
assert main # silence pyflakes

app.register_blueprint(characters_ModL_page, url_prefix="/Character/ModL")
