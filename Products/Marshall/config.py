import os
from Globals import package_home
PACKAGE_HOME = package_home(globals())

TOOL_ID = 'marshaller_registry'
AT_NS = 'http://plone.org/ns/archetypes/'
CMF_NS = 'http://cmf.zope.org/namespaces/default/'
ATXML_SCHEMA = os.path.join(PACKAGE_HOME, 'validation', 'atxml')
