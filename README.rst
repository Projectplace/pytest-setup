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
needs to contain an ``__init__.py`` file.

In our examples we'll call the directory ``representations``.

The relative path to ``representations`` needs to go into a pytest INI-style
file.
For details refer to the `pytest documentation <http://pytest.org/en/latest/customize.html#command-line-options-and-configuration-file-settings>`_.

.. code-block:: ini

  [pytest]
  representation_path = <from project root relative path to>/representations

Next we need to create a class for the artifact we want to create using our marker.
Let's create a ``user`` artifact.

There are two requirements for our class:

* *SIGNATURE* This is a dictionary containing the names of the parameters for the ``create()`` function.
* *create()* This is the create-function of the artifact called by the plugin.

SIGNATURE
_________

This is a dictionary containing the parameter-names of the create-function. The names are the keys and the type of the
name are the values. For example our ``User`` has a name, this is ``basestring` (that will handle both unicode and str).

Note: SIGNATURE is a keyword and so must be in all caps.

create()
________

This is the create-function of our user-artifact. It has to be a ``@classmethod`` and has to be called ``create``.
Furthermore it has to return an instantiated object of the artifact.

Example:

.. code-block:: python

    import .representations.project as project

    class User(object):

        def __init__(self, user_name):
            self.user_name = user_name

        SIGNATURE = {'name': basestring, 'project': project.Project}

        @classmethod
        def create(cls, name, project):
            # Whatever code is needed to setup the user and add him to the project
            return cls(name)

Usage
*****

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




scope
signature
default representations
test_db fixture
test_db scope
test_db duplicates

