from flask import Blueprint, request
from src.core.models.rss import OutputRss

rss_bp = Blueprint("rss", __name__, url_prefix="/rss")

@rss_bp.route('/', methods=['GET'])
def GetRss():
    return OutputRss()
