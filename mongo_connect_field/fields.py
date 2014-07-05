from django.db import models
from mongoengine import Document


class MongoField(models.Field):

    description = "A Foreign Key to Mongo Document"

    def __init__(self, to, *args, **kwargs):
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
            return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return json.dumps(value.to_mongo)

    def get_attname(self):
        return '%s_id' % self.name

    def contribute_to_class(self, cls, name):
        super(MongoField, self).contribute_to_class(cls, name)

rules = [
    (
        (MongoField,),
        [],
        {},
    )
]

from south.modelsinspector import add_introspection_rules
add_introspection_rules(rules, ["utils\.customfields\.MongoField"])

