"""
Copyright (C) 2017 Planview, Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import pytest
import importlib
import logging
import sys
import re


# Syntax sugar.
_ver = sys.version_info

#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)


if is_py2:
    basestring = basestring

if is_py3:
    basestring = (str, bytes)


LOGGER = logging.getLogger(__name__)


def retry_on_error(error):
    """ Decorator rerunning wrapped method upon caught error """

    def wrapper(func):
        def exc_handler(*args, **kwargs):
            import time
            import random

            for i in range(10):
                try:
                    return func(*args, **kwargs)
                except error as e:
                    LOGGER.warning("Retry failed with error: {}".format(e))
                    if i == 9:
                        LOGGER.exception("Retrying failed, re-raising")
                        raise error("Retrying failed!")
                    time.sleep(0.5 + random.random())
                    continue
        return exc_handler
    return wrapper


def pytest_configure(config):
    """
    py.test hook for test session configurations.

    :param config: py.test config module
    :return: None
    """

    # Object data setup marker
    config.addinivalue_line("markers",
                            "setup_data: test data for object creation")


def _get_representation(class_name, request):
    base = request.config.getini('representation_path').lower()
    module = importlib.import_module(re.sub(r"\\|/", ".", base))
    return getattr(module, class_name)


def _get_base_representation(request):
    base_repr_class_name = request.config.getini('base_repr_class_name')
    if base_repr_class_name:
        return _get_representation(base_repr_class_name, request)


def _get_representation2(class_name, request):
    """ optional solution to importing representation modules """
    import os

    base = request.config.getini('representation_path').lower()
    if base == '.':
        repr_path = os.getcwd()
        base = repr_path.split(os.sep).pop()
    else:
        repr_path = os.path.join(os.getcwd(), base)
        base = re.sub(r"\\|/", ".", base)

    if not base.endswith('.'):
        base += '.'

    for root, dirs, files in os.walk(repr_path):
        for each in files:
            if each.endswith('.py'):
                try:
                    module = importlib.import_module(base + each[:-3])
                    return getattr(module, class_name)
                except (AttributeError, ImportError):
                    continue
    return "FAIL"


def pytest_addoption(parser):
    parser.addini('representation_path',
                  help='directory for representations')
    parser.addini('base_repr_class_name',
                  help='class name of the base representation')


@pytest.fixture(scope='module')
def test_db(request):
    """
    Creates a TestDataCollection instance which houses all the data
    representation objects.

    :param request: py.test request module
    :return: TestDataCollection instance
    """
    from . import database

    base_representation_class = _get_base_representation(request)
    tdc = database.TestDataCollection(base_representation_class)

    yield tdc

    tdc.clear()


@pytest.fixture(scope='function', autouse=True)
def clean_test_db(request, test_db):
    """
    This will clear the TestDataCollection from all objects with a ttl of
    'function'.

    :param request: py.test request module
    :param test_db: fixture test_db
    :return: None
    """
    yield

    test_db.clear(request.scope)


@pytest.fixture(scope='function')
def test_name(request):
    """
    Returns the current tests name

    :param request: py.test request module
    :return: current tests name
    """
    return request.function.__name__


@pytest.fixture(scope='function')
def user(request, test_db):
    """
    Creates user in designated account or project.
    Example:
        @pytest.mark.user(name='Tim', account='acc_name')

    :param request: py.test request module
    :param test_db: fixture test_db
    :return: None
    """
    user_data = request.node.get_closest_marker("user")

    if not user_data:
        return
    # We must work on a copy of the data or else rerunfailures/flaky fails
    user_data = user_data.kwargs.copy()
    _create_user(request, test_db, user_data)


@pytest.fixture(scope="function")
def users(request, test_db):
    """
    Creates several users in designated account(s) or project(s).
    Example:
        @pytest.mark.users([
            {'name': 'Tim', 'account': 'acc_name'},
            {'name': 'Rush', 'project': 'acc_name'}
        ])

    :param request: py.test request module
    :param test_db: fixture test_db
    :return: None
    """
    user_data = request.node.get_closest_marker("users")

    if not user_data:
        return
    # We must work on a copy of the data or else rerunfailures/flaky fails
    user_data = tuple(user_data.args)
    for each in user_data[0]:
        _create_user(request, test_db, each)


def _create_user(request, test_db, user_data):
    account = user_data.pop("account", None)
    project = user_data.pop("project", None)
    site_index = user_data.pop('site_index', None)

    data = [{'User': [user_data]}]
    _setup(data, test_db, request)

    _user = test_db.get("User", user_data['name'])

    if account:
        account = test_db.get("Account", account)
        account.add_member(account.owner, _user, site_index=site_index)

    if project:
        project = test_db.get("Project", project)
        project.add_member(project.head_admin, _user.email, site_index=site_index)


@pytest.fixture(scope='module', autouse=True)
def setup_module(request, test_db):
    """
    Module level object factory.

    This fixture sets up test data with a ttl of 'module'.

    :param request: py.test request module
    :param test_db: fixture test_db
    :return: None
    """
    if hasattr(request.module, 'module_setup_data'):
        _setup(request.module.module_setup_data, test_db, request)


@pytest.fixture(scope='function', autouse=True)
def setup_function(request, test_db, user, users):
    """
    Function level object factory.

    This fixture sets up test data with a ttl of 'function'.

    :param request: py.test request module
    :param test_db: fixture test_db
    :return: None
    """
    setup_data = request.node.get_closest_marker("setup_data")

    if not setup_data:
        return

    _setup(setup_data.args, test_db, request)


def _setup(test_data, test_db, request):
    """
    Setup test data and add to test DB.

    :param test_data: test data for object creation
    :param test_db: test DB
    :param scope: ttl for created object(s)
    :return: None
    """
    def _add():
        test_db.add(created_obj, request.scope)
        # This adds objects created within an object creation to the test_db
        if hasattr(created_obj, 'default_representations'):
            representations = created_obj.default_representations
            if not isinstance(representations, list):
                raise RuntimeError(
                    "default_representations must return a list!")
            for each in _flatten_list(representations):
                test_db.add(each, request.scope)

    for data in test_data:
        for obj, params in data.items():
            obj_to_create = _get_representation(obj, request)
            # if params is a list, that means we have multiple objects to
            # create
            if isinstance(params, list):
                for sig in params:
                    # We must work on a copy of the data or else
                    # rerunfailures/flaky fails
                    created_obj = _create(obj_to_create, sig.copy(),
                                          test_db, request)
                    _add()
            else:
                created_obj = _create(obj_to_create, params.copy(),
                                      test_db, request)
                _add()


@retry_on_error(IndexError)
def _create(obj_to_create, test_params, test_db, request):
    """
    Create test data object (real object representation).

    :param obj_to_create: type of representation to create
    :param test_params: creation parameters
    :param test_db: test DB
    :param request: py.test request module
    :return: instance of created object
    """

    # object_param is the name of the param from representation objects
    # create-function
    for object_param in obj_to_create.SIGNATURE.keys():

        # get the value from the signature provided by parametrize
        # (by the test), if no value was specified the value will be None
        test_param_value = test_params.get(object_param, None)

        # get the type of the param (object_param) from the signature
        object_param_type = obj_to_create.SIGNATURE[object_param]

        # if test_param_value and object_param_type is of the same type,
        # usually (base)string, we continue
        if isinstance(test_param_value, object_param_type):
            continue
        # elif test_param_value is of type basestring, we get the object
        # represented by object_param_type and test_param_value
        elif isinstance(test_param_value, basestring):
            test_params[object_param] = _find_object(test_db,
                                                     object_param_type,
                                                     test_param_value)
        # else we remove the parameter because object_param defaults to None
        else:
            test_params.pop(object_param, None)

    try:
        return obj_to_create.create(**test_params)
    except IndexError:
        # Sometimes we get a 'Failue to persist' which causes a IndexError,
        # so we retry once.
        from time import sleep
        sleep(5)
        return obj_to_create.create(**test_params)


def _find_object(test_db, object_type, value):
    """
    Due to some representations having an inheritance structure this
    functions finds the correct type in the test DB.

    :param test_db: test DB
    :param object_type:
    :param value: test DB object identifier
    :return: object representation instance from test DB
    """
    obj = test_db.get(object_type.__name__, value)
    if obj:
        return obj
    for class_type in object_type.__subclasses__():
        obj = test_db.get(class_type.__name__, value)
        if obj:
            return obj
    raise RuntimeError(
        "Failed to find object of type {} with name {}".format(
            object_type.__name__, value
        )
    )


def _flatten_list(representations):
    """
    The default_representation can sometimes be a list of lists,
    this flattens that list.

    :param representations: list of object representations
    :return: flattened list of representations
    """
    def flatten(l):
        for el in l:
            if isinstance(el, list):
                for sub in flatten(el):
                    yield sub
            else:
                yield el
    return list(flatten(representations))
