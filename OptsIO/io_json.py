import json, inspect
import base64
from django.db.models.fields.files import ImageFieldFile, FieldFile, ImageField
from django.contrib.auth.models import User
from django.http import HttpRequest
import datetime
import arrow
from django.utils.timezone import is_aware
from decimal import Decimal
import uuid
from urllib.request import unquote

def quote_todict(data):
    return json.loads(unquote(data))

def to_json(data):
    return json.dumps(data, cls=WebJSONEncoder)

def from_json(data):
    return json.loads(data)

class WebJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types and UUIDs.
    """
    def default(self, o):
        if isinstance(o, User):
            return ''
        if isinstance(o, HttpRequest):
            return ''
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.strftime('%Y-%m-%d %H:%M:%S')
            return r
        elif isinstance(o, datetime.date):
            try:
                return o.strftime('%Y-%m-%d')
            except:
                return datetime.date.today().strftime('%Y-%m-%d')
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, arrow.arrow.Arrow):
            try:
                return o.strftime('%Y-%m-%d')
            except:
                return datetime.date.today().strftime('%Y-%m-%d')
        elif isinstance(o, Decimal):
            return float(o)
        elif isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, ImageFieldFile):
            try:
                #return base64.b64encode(o.read())
                return o.url
            except Exception as e:
                return ''
        elif isinstance(o, ImageField):
            try:
                #return base64.b64encode(o.read())
                return o.url
            except Exception as e:
                return ''            
        elif isinstance(o, FieldFile):
            try:
                #return base64.b64encode(o.read())
                return o.url
            except Exception as e:
                return ''
        else:
            return super(WebJSONEncoder, self).default(o)
