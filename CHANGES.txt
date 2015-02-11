Changelog
=========

2.1.5 (unreleased)
------------------

- Nothing changed yet.


2.1.4 (2015-02-11)
------------------

- Ported tests to plone.app.testing
  [tomgross]


2.1.3 (2014-04-16)
------------------

- Remove duplicate code which is already available from Products.Archetypes
  and add deprecation warnings about it.
  [tomgross]


2.1.2 (2013-01-13)
------------------

- Unicode export text is not supported since GS 1.7.0.
  [rossp]

2.1.1 - 2011-07-20
------------------

- Fixed typo which prevents the deserializing of multiValued fields.
  [matth]

2.1 - 2011-01-03
----------------

- Use plone.uuid to look up content UUIDs.
  [toutpt, davisagli]

2.0 - 2010-07-18
----------------

- No changes.

2.0b2 - 2010-04-20
------------------

- atmxl: Export / import mimetype of Archetypes IObjectFields so the right
  content type will be set in Plone 4. Ported from quintagroup.transmogrifier.
  [csenger]

- atxml: Encode/decode strings with control characters that breaks common xml
  parsers in base64. This can be turned off by calling the marshaller with
  'encode_with_ctrlchars=False'.
  [csenger]

- Make sure DateTime fields are constructed properly in atns.py
  by explicitly constructing a DateTime instance for input values
  that would result in a DateTime value of `None` otherwise.
  [tomster]

- Deprecationfix: Use DateTime.ISO8601() instead of DateTime.ISO
  [tomster]

2.0b1 - 2009-12-27
------------------

- Removed BBB code for guess_content_type and fixed package dependencies.
  [hannosch]

2.0a1 - 2009-11-13
------------------

- Replaced a simple logging call with the standard logging module.
  [hannosch]

- Changed the config.py check for ElementTree to accept xml.etree.
  [hannosch]

- Get tests to work with `xml.etree` and Plone trunk. We have to use the ATCT
  test cases as a base to get the expected content types.
  [hannosch]

- Downgrade warning about missing `libxml2-python` to debug level.
  [hannosch]

- Avoid a test dependency on quick installer.
  [hannosch]

- Updated package metadata and cleaned up a bit.
  [hannosch]

- Declare package dependencies and fixed deprecation warnings for use
  of Globals.
  [hannosch]

- Made test runs that require libxml2 dependent on the availability of it.
  [hannosch]

- Made the dependency on elementree conditional on the Python version. For
  Python 2.5 and later, we use the xml.etree modules.
  [hannosch]

- Purged old Zope 2 Interface interfaces for Zope 2.12 compatibility.
  [elro]

1.2.2 - unreleased
------------------

1.2.1 - 2009-05-29
------------------

- Register atxml and namespaces even if libxml2 isn't present, but test for
  elementtree.
  [csenger]

1.2.0 - 2008-09-30
------------------

- Intial egg release.

1.0.0 - 2007-11-07
------------------

- Made demarshall of SchemaAttributes more verbose. Now it raises its
  own Exception with information on which attribute and value it fails.
  [jensens]

- Demote libxml2-python missing log message from "warning" to "info".
  This warning has been a common source of confusion for new users
  trying to track down real errors.
  [smcmahon]

1.0.0-b1 - 2007-04-28
---------------------

- In the ATNS marshaller, preserve the field order by not using
  set.
  [nouri]

1.0.0-a1 - 2006-10-25
---------------------

- Fixed some deprecation warnings for guess_content_type.
  [hannosch]

- Updated a test for generated XML export format.
  [hannosch]

- Initial version, see README.txt for details.
  [lots of people]

