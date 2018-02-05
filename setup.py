from setuptools import setup, find_packages

version = '2.3.1.dev0'

setup(
    name='Products.Marshall',
    version=version,
    description="Configurable Marshallers for Archetypes",
    long_description=(open("README.rst").read() + "\n" +
                      open("CHANGES.rst").read()),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Zope2",
        "Framework :: Plone",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
    ],
    keywords='web zope application server webdav ftp',
    license="GPL",
    author='Sidnei da Silve and others',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.python.org/pypi/Products.Marshall',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
      test=[
          'Products.ATContentTypes',
      ]
    ),
    install_requires=[
        'setuptools',
        'six',
        'transaction',
        'plone.uuid',
        'zope.contenttype',
        'zope.deprecation',
        'zope.interface',
        'Products.Archetypes',
        'Products.CMFCore',
        'Products.GenericSetup',
        'Acquisition',
        'DateTime',
        'ExtensionClass',
        'Zope2',
    ],
    )
