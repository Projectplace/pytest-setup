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
from setuptools import setup

setup(name='pytest-setup',
      use_scm_version=True,
      description='pytest plugin for test session data',
      long_description=open('README.rst').read(),
      author='Bijwen Aziz',
      author_email='baziz@planview.com',
      url='https://github.com/Projectplace/pytest-setup',
      packages=['pytest_setup'],
      entry_points={'pytest11': ['setup = pytest_setup.pytest_setup']},
      setup_requires=['setuptools_scm'],
      install_requires=['pytest>=2.9.0'],
      license='Mozilla Public License 2.0 (MPL 2.0)',
      keywords='py.test pytest setup data',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Framework :: Pytest',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
          'Operating System :: POSIX',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: MacOS :: MacOS X',
          'Topic :: Software Development :: Quality Assurance',
          'Topic :: Software Development :: Testing',
          'Topic :: Utilities',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.7'])
