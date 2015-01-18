import json
from django.db import models, Error
from django.db.models.fields.subclassing import Creator
from mongoengine import Document
from . import utils


class RelatedObjectDescriptor(Creator):
    def __init__(self, field, attr_type):
        super(RelatedObjectDescriptor, self).__init__(field)
        self.attr_type = attr_type

    def __get__(self, obj, type=None):
        if obj is None:
            return self

        if self.attr_type == 'attname':
            return obj.__dict__[self.field.attname]

        try:
            return obj.__dict__[self.field.name]
        except KeyError:
            try:
                object_id = getattr(obj, self.field.attname)
            except KeyError:
                return None
            else:
                obj.__dict__[self.field.name] = self.field.to_python(object_id)
                return obj.__dict__[self.field.name]

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)
        obj.__dict__[self.field.attname] = self.field.get_prep_value(value)


class MongoField(models.Field):
    description = "A Foreign Key to Mongo Document"

    def __init__(self, to, *args, **kwargs):
        if isinstance(to, basestring):
            to = utils.import_class(to)

        if not issubclass(to, Document):
            raise Error(
                "To Field must be a document class or a path to Document class")

        self.mongodoc = to
        kwargs['max_length'] = 24
        super(MongoField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return "char(24)"

    def to_python(self, value):
        if isinstance(value, Document):
            return value
        else:
            return self.mongodoc.objects.get(id=value)

    def get_prep_value(self, value):
        if isinstance(value, Document):
            return str(value.pk)
        else:
            return str(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, Document):
            return str(value.pk)
        else:
            return str(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return json.dumps(value.to_mongo)

    def contribute_to_class(self, cls, name, virtual_only=False):
        super(MongoField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, RelatedObjectDescriptor(self, 'name'))
        setattr(cls, self.attname, RelatedObjectDescriptor(self, 'attname'))

    def get_attname(self):
        return '%s_id' % self.name

    def deconstruct(self):
        name, path, args, kwargs = super(MongoField, self).deconstruct()
        del kwargs["max_length"]
        args.insert(1, "%s.%s" % (self.mongodoc.__module__,
                                  self.mongodoc.__name__))
        return name, path, args, kwargs


