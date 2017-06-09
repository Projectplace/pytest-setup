pytest-setup
============

The pytest-setup plugin provides a way to mark your tests with data required
to run the tests. It moves the data creation out of the actual test-function
in an effort to keep the test clean and specific.

There are a lot of moving parts, but hopefully this user guide will help you
get up and running.

It also provides a simple test database to manage all the created data.

Getting started
***************

In your project you'll need a directory that contains the different artifacts
that you'll be creating. This directory needs to be a python package, ie. it
needs to contain an ``__init__.py`` file. Also, that __init__-file needs to contain
all the imports to the individual representations.

.. code-block:: python

    from .user import User
    from .project import Project

In our examples we'll call the directory ``representations``.

The relative path to ``representations`` needs to go into a pytest INI-style
file.
For details refer to the `pytest documentation
<http://pytest.org/en/latest/customize.html#command-line-options-and-configuration-file-settings>`_.

.. code-block:: ini

  [pytest]
  representation_path = <from project root relative path to>/representations

Next we need to create a class for the artifact we want to create using our marker.
Let's create a ``user`` artifact.

Requirements
------------

There are a couple of requirements for the plugin to work.

SIGNATURE
_________

This is a dictionary containing the parameter-names of the create-function. The names are the keys and the type of the
name are the values. For example our ``User`` has a name, this is ``basestring`` (that will handle both unicode and str).

Note: SIGNATURE is a keyword and so must be in all caps.

Property identifier
___________________

Each class/artifact needs to provide a property called ``identifier``, this is used to get data from the test
database and is also used by the database to make sure there are no duplicates.

create()
________

This is the create-function of our user-artifact. It has to be a ``@classmethod`` and has to be called ``create``.
Furthermore it has to return an instantiated object of the artifact.

Example:

.. code-block:: python

    import .representations.project as project

    class User(object):

        def __init__(self, user_name):
            self._user_name = user_name

        @property
        def identifier(self):
            return self._user_name

        SIGNATURE = {'name': basestring, 'project': project.Project}

        @classmethod
        def create(cls, name, project):
            # Whatever code is needed to setup the user and add him to the project
            return cls(name)

Usage
-----

When the ``User`` artifact is in place you can now use the marker to create as many users as you want.
There is currently two ways of creating objects: on the module level and on the function level.

Module level
____________

Objects created on the module level will be available for every test function in the module.
The syntax is:

.. code-block:: python

  module_setup_data = [{'Class Name1': [{'key': 'value', 'key': 'value'},  # Class Name1 obj one
                                        {'key': 'value', 'key': 'value'}]},  # Class Name2 obj one
                       {'Class Name2': [{'key': 'value'}]}]

This will create two objects of type ``Class Name1`` and one object of type ``Class Name2``.

Function level
______________

Objects created on the function level will be available for *only* that decorated test function.
The syntax is:

.. code-block:: python

  @pytest.mark.setup_data({'Class Name1': [{'key': 'value', 'key': 'value'},  # Class Name1 obj one
                                           {'key': 'value', 'key': 'value'}]},  # Class Name2 obj one
                          {'Class Name2': [{'key': 'value'}]})

This will create two objects of type ``Class Name1`` and one object of type ``Class Name2``.

Example of using both:

.. code-block:: python

    import pytest

    module_setup_data = [{'Project': [{'name': 'MyProject'}]}]

    @pytest.mark.setup_data({'User': [{'name': 'Tom Jones', 'project': 'MyProject'}]})
    def test_login(test_db):
        login_user(user=test_db.get('User', 'Tom Jones',
                   password='111111',
                   project=test_db.get('Project', 'MyProject'))

Test Database
*************

To easily manage all the created data the plugin provides a simple key-value database.

The database is accessed via the pytest fixture ``test_db``.

.. code-block:: python

    def test_login(test_db):
        user = test_db.get('User', 'Tommy')

The first argument to ``get`` is the object as a string you want to get, the second argument is the
identifier mentioned earlier.

If you so wish, you can also ``add`` to the database. The first argument is the object you wish to add
and the second, optional, argument is the time-to-live (ttl) which can be either "function" or "module".

The ttl corresponds to the scope of the setup-data. For "function" that data is only available during the scope
of that decorated test function. For "module" it's available for all the test functions within that module.

Advanced Usage
**************

In some cases an object you create in turn creates its own objects. If you want those objects available
in the test database, you need to provide the creating object with a ``default _representations`` property.

Let's say we have an account object that also creates a user object.

.. code-block:: python

    from .representations.user import User

    class Account(object):

        def __init__(self, account_name):
            self._account_name = account_name
            self._user = User.create("Account Owner")

        @property
        def identifier(self):
            return self._account_name

        @property
        def default_representations
            return [self._user]

The ``default_representations`` property has to return a list with the object(s) it creates.
