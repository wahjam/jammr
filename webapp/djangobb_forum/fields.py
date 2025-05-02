"""
Details about AutoOneToOneField:
    http://softwaremaniacs.org/blog/2007/03/07/auto-one-to-one-field/
"""
from io import BytesIO
import random
from hashlib import sha1
import json

from django.db.models import OneToOneField
from django.db.models.fields.related_descriptors import ReverseOneToOneDescriptor
from django.db import models
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings


class AutoSingleRelatedObjectDescriptor(ReverseOneToOneDescriptor):
    def __get__(self, instance, instance_type=None):
        try:
            return super(AutoSingleRelatedObjectDescriptor, self).__get__(instance, instance_type)
        except self.RelatedObjectDoesNotExist:
            obj = self.related.related_model(**{self.related.field.name: instance})
            obj.save()
            return obj


class AutoOneToOneField(OneToOneField):
    """
    OneToOneField creates dependent object on first request from parent object
    if dependent oject has not created yet.
    """

    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(), AutoSingleRelatedObjectDescriptor(related))
        #if not cls._meta.one_to_one_field:
        #    cls._meta.one_to_one_field = self


class ExtendedImageField(models.ImageField):
    """
    Extended ImageField that can resize image before saving it.
    """

    def __init__(self, *args, **kwargs):
        self.width = kwargs.pop('width', None)
        self.height = kwargs.pop('height', None)
        super(ExtendedImageField, self).__init__(*args, **kwargs)

    def save_form_data(self, instance, data):
        if data and self.width and self.height:
            content = self.resize_image(data.read(), width=self.width, height=self.height)
            salt = sha1(str(random.random()).encode('utf-8')).hexdigest()[:5]
            fname = sha1((salt + settings.SECRET_KEY).encode('utf-8')).hexdigest() + '.png'
            data = SimpleUploadedFile(fname, content, content_type='image/png')
        super(ExtendedImageField, self).save_form_data(instance, data)

    def resize_image(self, rawdata, width, height):
        """
        Resize image to fit it into (width, height) box.
        """
        try:
            import Image
        except ImportError:
            from PIL import Image
        image = Image.open(BytesIO(rawdata))
        oldw, oldh = image.size
        if oldw >= oldh:
            x = int(round((oldw - oldh) / 2.0))
            image = image.crop((x, 0, (x + oldh) - 1, oldh - 1))
        else:
            y = int(round((oldh - oldw) / 2.0))
            image = image.crop((0, y, oldw - 1, (y + oldw) - 1))
        image = image.resize((width, height), resample=Image.ANTIALIAS)


        content = BytesIO()
        image.save(content, format='PNG')
        return content.getvalue()


class JSONField(models.TextField):
    """
    JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.
    """

    def from_db_value(self, value, expression, connection, context):
        if value is not None:
            try:
                value = json.loads(value)
            except ValueError:
                pass
        return value

    def to_python(self, value):
        if value is None:
            return None
        if value == '':
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                pass
        return value

    def get_prep_value(self, value):
        if value is None:
            return ''
        return json.dumps(value, cls=DjangoJSONEncoder)
