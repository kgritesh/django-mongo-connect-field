from django.db import models

# Create your models here.
from django.db.models.constants import LOOKUP_SEP
from .fields import MongoField


class MongoQuerySet(models.query.QuerySet):

    def __init__(self, *args, **kwargs):
        super(MongoQuerySet, self).__init__(*args, **kwargs)
        if not issubclass(self.model, MongoConnectionModel):
            return

        self._mongo_field_map = self.model.get_mongo_field_map()

        self._known_mongo_objects = {}
        for field in self._mongo_field_map.keys():
            self._known_mongo_objects[field] = {}

    def _clone(self, klass=None, setup=False, **kwargs):
        clone = super(MongoQuerySet, self)._clone(klass, setup, **kwargs)
        clone._known_mongo_objects = self._known_mongo_objects
        return clone


    def apply_mongo_filter(self, fieldname, value, mongofield):
        parts = fieldname.split(LOOKUP_SEP)
        field = self._mongo_field_map[parts[0]]
        if len(parts) == 1:
            self._known_mongo_objects[field.name][str(value.id)] = value
            return [str(value.id)]
        else:
            filter_expr = LOOKUP_SEP.join(fieldname.split(LOOKUP_SEP)[1:])
            idlist = []
            for doc in mongofield.mongodoc.objects.filter(**{filter_expr: value}):
                self._known_mongo_objects[field.name][str(doc.id)] = doc
                idlist.append(str(doc.id))

            return idlist

    def _filter_or_exclude(self, negate, *args, **kwargs):
        filter_map = dict((k.split(LOOKUP_SEP)[0], (k, v)) for k, v in kwargs.iteritems())
        mongo_filters = [flt for flt in filter_map if flt in self._mongo_field_map]

        for flt in mongo_filters:
            mongofield = self._mongo_field_map[flt]
            actual_filter, value = filter_map[flt]
            objectids = self.apply_mongo_filter(actual_filter, value, mongofield)
            del kwargs[actual_filter]
            filter_expr = "%s__in" % mongofield.get_attname()
            kwargs[filter_expr] = objectids

        return super(MongoQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)

    def iterator(self):
        for obj in super(MongoQuerySet, self).iterator():
            for fieldname, field in self._mongo_field_map.iteritems():
                rel_objs = self._known_mongo_objects[fieldname]
                object_id = getattr(obj, field.get_attname())
                if object_id:
                    try:
                        rel_obj = rel_objs[object_id]
                    except KeyError:
                        pass
                    else:
                        setattr(obj, field.name, rel_obj)

                yield obj


class MongoManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        """Returns a new QuerySet object.  Subclasses can override this method
        to easily customize the behavior of the Manager.
        """
        return MongoQuerySet(self.model, using=self._db)


class MongoConnectionModel(models.Model):

    class Meta:
        abstract = True

    @classmethod
    def get_mongo_field_map(cls):
        return dict((field.name, field) for field in cls._meta.fields
                    if isinstance(field, MongoField))

    def __init__(self, *args, **kwargs):
        for field in self.__class__.get_mongo_field_map().values():
            value = kwargs.pop(field.name, None)
            if value:
                kwargs[field.attname] = str(value.id)
                setattr(self, field.name, value)

        super(MongoConnectionModel, self).__init__(*args, **kwargs)

    objects = MongoManager()
