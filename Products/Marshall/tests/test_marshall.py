# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004 Enfold Systems, LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
$Id$
"""

import os, sys
import difflib
import glob
import re

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Load fixture
from Testing import ZopeTestCase
from Products.Archetypes.tests import ArchetypesTestCase

# Install our product
ZopeTestCase.installProduct('Marshall')
ZopeTestCase.installProduct('Archetypes')
ZopeTestCase.installProduct('ArchExample')
ZopeTestCase.installProduct('ATContentTypes')

from Products.CMFCore.utils import getToolByName
from Products.Marshall.registry import Registry, getRegisteredComponents
from Products.Marshall.registry import getComponent
from Products.Marshall.exceptions import MarshallingException
from Products.Marshall.tests import PACKAGE_HOME
from Products.Marshall.tests.examples import person
tool_id = Registry.id

def normalize_xml(s):
    s = re.sub(r"[ \t]+", " ", s)
    return s

class MarshallerTest(ArchetypesTestCase.ArcheSiteTestCase):

    def afterSetUp(self):
        super(ArchetypesTestCase.ArcheSiteTestCase, self).afterSetUp()
        self.loginPortalOwner()
        # Refresh ATContentTypes to avoid a minor bug on setup.
        cp = self.portal.Control_Panel['Products']
        self.qi = self.portal.portal_quickinstaller
        self.qi.installProduct('Marshall')
        self.qi.installProduct('ATContentTypes')
        # Needed so the one below works.
        get_transaction().commit(1)
        self.portal.switchCMF2ATCT(skip_rename=True)
        self.tool = getToolByName(self.portal, tool_id)
        self.infile = open(self.input, 'rb+')
        self.portal.invokeFactory(self.type_name, self.type_name.lower())
        self.obj = self.portal._getOb(self.type_name.lower())

    def beforeTearDown(self):
        super(ArchetypesTestCase.ArcheSiteTestCase, self).beforeTearDown()
        self.infile.close()

    def compare(self, one, two):
        diff = difflib.ndiff(one.splitlines(), two.splitlines())
        diff = '\n'.join(list(diff))
        return diff

    def test_marshall_roundtrip(self):
        marshaller = getComponent(self.prefix)
        content = self.infile.read()
        marshaller.demarshall(self.obj, content)
        ctype, length, got = marshaller.marshall(self.obj, filename=self.input)
        if self.input.endswith('xml'):
            content, got = normalize_xml(content), normalize_xml(got)
        diff = self.compare(content, got)
        self.failUnless(got.splitlines() == content.splitlines(), diff)


class ATXMLReferenceMarshallTest(ArchetypesTestCase.ArcheSiteTestCase):

    def afterSetUp(self):
        super(ArchetypesTestCase.ArcheSiteTestCase, self).afterSetUp()
        self.loginPortalOwner()
        self.qi = self.portal.portal_quickinstaller
        self.qi.installProduct('Marshall')
        self.tool = getToolByName(self.portal, tool_id)
        self.marshaller = getComponent('atxml')

    def createPerson(self, ctx, id, **kw):
        person.addPerson(ctx, id, **kw)
        return ctx._getOb(id)

    def test_uid_references(self):
        paulo = self.createPerson(
            self.portal,
            'paulo',
            title='Paulo da Silva')
        eligia = self.createPerson(
            self.portal,
            'eligia',
            title='Eligia M. da Silva')
        sidnei = self.createPerson(
            self.portal,
            'sidnei',
            title='Sidnei da Silva')

        self.assertEquals(sidnei.getParents(), [])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <uid>
        %(uid)s
        </uid>
        </reference>
        </field>
        </metadata>
        """ % {'uid':paulo.UID()}
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test a simple UID reference
        self.assertEquals(sidnei['parents'], [paulo.UID()])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <uid>
        XXX%(uid)sXXX
        </uid>
        </reference>
        </field>
        </metadata>
        """ % {'uid':paulo.UID()}
        # Test that invalid UID reference raises an exception
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)


        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <uid>
        %(uid1)s
        </uid>
        </reference>
        </field>
        <field id="parents">
        <reference>
        <uid>
        %(uid2)s
        </uid>
        </reference>
        </field>
        </metadata>
        """ % {'uid1':paulo.UID(), 'uid2':eligia.UID()}
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test that multiple UID references work.
        self.assertEquals(sidnei['parents'], [paulo.UID(), eligia.UID()])

        # *WARNING* the tests below are dependent on the one above.
        new_uid = '9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9'
        old_uid = paulo.UID()
        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <uid>
        %(uid)s
        </uid>
        </metadata>
        """ % {'uid':new_uid}
        self.marshaller.demarshall(paulo, ref_xml)
        # Test modifying a uid by marshalling
        self.assertEquals(paulo.UID(), new_uid)
        # Test that the references still apply
        self.assertEquals(sidnei['parents'], [paulo.UID(), eligia.UID()])
        # Test that trying to set a different object to the same UID
        # will raise an exception.
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)

    def test_path_references(self):
        paulo = self.createPerson(
            self.portal,
            'paulo',
            title='Paulo da Silva')
        eligia = self.createPerson(
            self.portal,
            'eligia',
            title='Eligia M. da Silva')
        sidnei = self.createPerson(
            self.portal,
            'sidnei',
            title='Sidnei da Silva')

        self.assertEquals(sidnei.getParents(), [])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <path>
        %(path)s
        </path>
        </reference>
        </field>
        </metadata>
        """ % {'path':'paulo'}
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test a simple path reference
        self.assertEquals(sidnei['parents'], [paulo.UID()])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <path>
        XXX%(path)sXXX
        </path>
        </reference>
        </field>
        </metadata>
        """ % {'path':'paulo'}
        # Test that an invalid path reference raises an exception
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/">
        <field id="parents">
        <reference>
        <path>
        %(path1)s
        </path>
        </reference>
        </field>
        <field id="parents">
        <reference>
        <path>
        %(path2)s
        </path>
        </reference>
        </field>
        </metadata>
        """ % {'path1':'paulo', 'path2':'eligia'}
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test multiple path references
        self.assertEquals(sidnei['parents'], [paulo.UID(), eligia.UID()])


    def test_metadata_references(self):
        paulo = self.createPerson(
            self.portal,
            'paulo',
            title='Paulo da Silva',
            description='Familia Silva')
        paulo_s = self.createPerson(
            self.portal,
            'paulo_s',
            title='Paulo Schuh',
            description='Familia Schuh')
        sidnei = self.createPerson(
            self.portal,
            'sidnei',
            title='Sidnei da Silva',
            description='Familia Silva')

        self.assertEquals(sidnei.getParents(), [])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Paulo Schuh
        </dc:title>
        <dc:description>
        Familia Schuh
        </dc:description>
        </metadata>
        </reference>
        </field>
        </metadata>
        """
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test a simple metadata reference
        self.assertEquals(sidnei['parents'], [paulo_s.UID()])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Silva
        </dc:title>
        </metadata>
        </reference>
        </field>
        </metadata>
        """

        # Test that a metadata reference that doesn't uniquely
        # identifies a target raises an exception
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Souza
        </dc:title>
        </metadata>
        </reference>
        </field>
        </metadata>
        """
        # Test that a metadata reference that doesn't uniquely
        # find at least one object raises an exception
        self.assertRaises(MarshallingException, self.marshaller.demarshall,
                          sidnei, ref_xml)

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Paulo da Silva
        </dc:title>
        <dc:description>
        Familia Silva
        </dc:description>
        </metadata>
        </reference>
        </field>
        </metadata>
        """
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test simple metadata reference
        self.assertEquals(sidnei['parents'], [paulo.UID()])

        ref_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Paulo da Silva
        </dc:title>
        <dc:description>
        Familia Silva
        </dc:description>
        </metadata>
        </reference>
        </field>
        <field id="parents">
        <reference>
        <metadata>
        <dc:title>
        Paulo Schuh
        </dc:title>
        <dc:description>
        Familia Schuh
        </dc:description>
        </metadata>
        </reference>
        </field>
        </metadata>
        """
        self.marshaller.demarshall(sidnei, ref_xml)
        # Test multiple metadata references
        self.assertEquals(sidnei['parents'], [paulo.UID(), paulo_s.UID()])

    def test_linesfield(self):
        sidnei = self.createPerson(
            self.portal,
            'sidnei',
            title='Sidnei da Silva',
            description='Familia Silva',
            food_preference='BBQ\nPizza\nShrimp')

        self.assertEquals(sidnei.getFoodPrefs(),
                          ('BBQ', 'Pizza', 'Shrimp'))

        lines_xml = """<?xml version="1.0" ?>
        <metadata xmlns="http://plone.org/ns/archetypes/"
                  xmlns:dc="http://purl.org/dc/elements/1.1/">
        <field id="food_preference">
        BBQ
        </field>
        <field id="food_preference">
        Camaron Diablo
        </field>
        </metadata>
        """
        self.marshaller.demarshall(sidnei, lines_xml)
        self.assertEquals(sidnei.getFoodPrefs(),
                          ('BBQ', 'Camaron Diablo'))
        ctype, length, got = self.marshaller.marshall(sidnei)
        expected = [s.strip() for s in """\
        <field id="food_preference">
        BBQ
        </field>
        <field id="food_preference">
        Camaron Diablo
        </field>""".splitlines()]
        got = [s.strip() for s in got.splitlines()]
        comp = [s for s in expected if s in got]
        self.assertEquals(comp, expected)

from zExceptions.ExceptionFormatter import format_exception
from ZPublisher.HTTPResponse import HTTPResponse

orig_exception = HTTPResponse.exception
def exception(self, **kw):
    def tag_search(*args):
        return False
    kw['tag_search'] = tag_search
    return orig_exception(self, **kw)

orig_setBody = HTTPResponse.setBody
def setBody(self, *args, **kw):
    kw['is_error'] = 0
    if len(args[0]) == 2:
        title, body = args[0]
        args = (body,) + args[1:]
    return orig_setBody(self, *args, **kw)

def _traceback(self, t, v, tb, as_html=1):
    return ''.join(format_exception(t, v, tb, as_html=as_html))

HTTPResponse._error_format = 'text/plain'
HTTPResponse._traceback = _traceback
HTTPResponse.exception = exception
HTTPResponse.setBody = setBody

class DocumentationTest(ZopeTestCase.Functional,
                        ArchetypesTestCase.ArcheSiteTestCase):

    def afterSetUp(self):
        super(ArchetypesTestCase.ArcheSiteTestCase, self).afterSetUp()
        self.loginPortalOwner()
        self.qi = self.portal.portal_quickinstaller
        self.qi.installProduct('Marshall')
        self.qi.installProduct('ArchExample')

def test_suite():
    import unittest
    from Testing.ZopeTestCase import doctest
    suite = unittest.TestSuite()
    suite.addTest(doctest.FunctionalDocFileSuite('doc/README.txt',
                                                 package='Products.Marshall',
                                                 test_class=DocumentationTest))
    return suite
    suite.addTest(unittest.makeSuite(ATXMLReferenceMarshallTest))
    dirs = glob.glob(os.path.join(PACKAGE_HOME, 'input', '*'))
    comps = [i['name'] for i in getRegisteredComponents()]
    for d in dirs:
        prefix = os.path.basename(d)
        if prefix not in comps:
            continue
        files = glob.glob(os.path.join(d, '*'))
        for f in files:
            if os.path.isdir(f):
                continue
            f_name = os.path.basename(f)
            type_name = os.path.splitext(f_name)[0]
            k_dict = {'prefix':prefix,
                      'type_name':type_name,
                      'input':f}
            klass = type('%s%sTest' % (prefix, type_name),
                         (MarshallerTest,),
                         k_dict)
            suite.addTest(unittest.makeSuite(klass))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=1)
