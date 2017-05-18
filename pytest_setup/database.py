from .pytest_setup import basestring


class TestDataCollection(object):
    """
    Collection to hold all the data representation objects.

    DB model:
    db = {'User': {'kalle': <object>}}
    """
    db = {}

    def add(self, obj, ttl='module'):
        """
        Add data representation object to the collection.

        :param obj: data representation object
        :param ttl: time to live for object (default: function)
        :return: the object added
        """
        import inspect

        for category in inspect.getmro(type(obj)):
            if category == object:
                continue

            category_db = self.db.setdefault(category.__name__, {})
            if obj.identifier in category_db:
                raise KeyError(
                    "Duplicate identifier <{}> in category <{}> for object <{}>".format(obj.identifier, category.__name__, obj))
            category_db[obj.identifier] = obj
        obj.ttl = ttl
        return obj

    def get(self, category, identifier):
        """
        Get data representation object from the collection.

        :param category: Class of the data representation object
        :param identifier: name to identify the obj
        :return: data representation object
        """
        if not isinstance(category, basestring):
            category = category.__name__
        category_db = self.db.get(category, {})
        return category_db.get(identifier, None)

    def clear(self, ttl=None):
        """
        Clear the DB and all its references.

        :param ttl: If set, db will only be cleared from objects with specifid ttl
        :return: None
        """
        if ttl:
            for category in self.categories:
                current = self.db[category]
                for identifier in list(current.keys()):
                    if current[identifier].ttl == ttl:
                        del current[identifier]
        else:
            self.db.clear()

    def dump_db(self):
        """
        Dump (print) the entire contents of DB.

        :return: None
        """
        print("DUMPING DB:")
        print(self.db)

    @property
    def categories(self):
        """
        Return a sorted list of all categories in the DB.

        :return: sorted list of categories
        """
        return sorted(self.db.keys())
