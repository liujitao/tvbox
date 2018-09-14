# -*- coding: utf-8 -*-

from flask import Blueprint

main = Blueprint('main', __name__)

from . import views
from . import tvbox, tvbox_model, tvbox_software, tvbox_grouping
from . import channel, channel_category, channel_product
from . import customer, vip, partner
from . import live_node, location, file_upload, app, user