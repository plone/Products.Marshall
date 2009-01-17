import os
import sys
from setuptools import setup, find_packages

version = '2.0'

install_requires=[
    'setuptools',
    'zope.contenttype',
    'zope.interface',
    'Products.Archetypes',
    'Products.CMFCore',
    'Products.GenericSetup',
    'Acquisition',
    'DateTime',
    'ExtensionClass',
    'Zope2',
]

if sys.version_info[:3] < (2,5,0):
    install_requires.append('elementtree')


setup(name='Products.Marshall',
      version=version,
      description="Configurable Marshallers for Archetypes",
      long_description=open("README.txt").read() + "\n" + \
              open("CHANGES.txt").read(),
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        ],
      keywords='web zope application server webdav ftp',
      license="GPL",
      author='Sidnei da Silve and others',
      author_email='plone-developers@lists.sourceforge.net',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      extras_require=dict(
        test=[
            'zope.schema',
            'Products.ATContentTypes',
        ]
      ),
      install_requires=install_requires,
      )
