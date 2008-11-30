import os
import sys
from setuptools import setup, find_packages

version = '1.1'

install_requires=[
  'setuptools',
  'Products.CMFCore',
],

if sys.version_info[:3] < (2,5,0):
    install_requires.append('elementtree')


setup(name='Products.Marshall',
      version=version,
      description="framework for pluggable marshalling policies",
      long_description=open("README.txt").read() + "\n" + \
              open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        ],
      keywords='Zope marshall',
      license="GPL",
      author='Sidnei da Silve and others',
      author_email='plone-developers@lists.sourceforge.net',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      )
