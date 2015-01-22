import os
import doctest

# Load fixture
from Products.Marshall.tests.base import BaseTest

from Products.CMFCore.utils import getToolByName
from Products.Marshall import registry
from Products.Marshall.registry import Registry
from Products.Marshall.registry import getComponent
from Products.Marshall.exceptions import MarshallingException
from Products.Marshall.tests import PACKAGE_HOME
from Products.Marshall.tests.examples import person
from Products.Marshall.tests.examples import blob
tool_id = Registry.id


def get_data(fname):
    return open(os.path.join(PACKAGE_HOME, 'data', fname), 'rb').read()


class BlobMarshallTest(BaseTest):

    def afterSetUp(self):
        super(BlobMarshallTest, self).afterSetUp()
        self.loginAsPortalOwner()
        registry.manage_addRegistry(self.portal)
        self.tool = getToolByName(self.portal, tool_id)
        self.marshaller = getComponent('atxml')

    def createBlob(self, ctx, id, **kw):
        blob.addBlob(ctx, id, **kw)
        ob = ctx._getOb(id)
        ob.indexObject()
        return ob

    def _test_blob_roundtrip(self, fname, data, mimetype, filename):
        blob = self.createBlob(self.portal, 'blob')

        field = blob.Schema()[fname]
        field.set(blob, data, mimetype=mimetype, filename=filename)

        # Marshall to XML
        ctype, length, got = self.marshaller.marshall(blob)

        # Populate from XML
        self.marshaller.demarshall(blob, got)

        # Marshall from XML again and compare to see if it's
        # unchanged.
        ctype, length, got2 = self.marshaller.marshall(blob)
        self.assertEqualsDiff(got, got2)

    def x_test_blob_image(self):
        # fails with IOError: cannot identify image file <cStringIO.StringI object at 0x7f07776de2d8>
        data = get_data('image.gif')
        self._test_blob_roundtrip('aimage', data, 'image/gif', 'image.gif')

    def test_blob_file_text(self):
        data = get_data('file.txt')
        self._test_blob_roundtrip('afile', data, 'text/plain', 'file.txt')

    def test_blob_file_binary(self):
        data = get_data('file.pdf')
        self._test_blob_roundtrip('afile', data, 'application/pdf', 'file.pdf')

    def test_blob_file_html(self):
        data = get_data('file.html')
        self._test_blob_roundtrip('afile', data, 'text/html', 'file.html')

    def test_blob_text_text(self):
        data = get_data('file.txt')
        self._test_blob_roundtrip('atext', data, 'text/plain', 'file.txt')

    def test_blob_text_binary(self):
        data = get_data('file.pdf')
        self._test_blob_roundtrip('atext', data, 'application/pdf', 'file.pdf')

    def test_blob_text_html(self):
        data = get_data('file.html')
        self._test_blob_roundtrip('atext', data, 'text/html', 'file.html')


OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_ONLY_FIRST_FAILURE)


def test_suite():
    import unittest
    from doctest import DocFileSuite
    from plone.app.testing.bbb import PTC_FUNCTIONAL_TESTING
    from plone.testing import layered
    suite = unittest.TestSuite()

    suite.addTest(layered(doctest.DocFileSuite(
        'doc/README.txt',
        package='Products.Marshall',
        optionflags=OPTIONFLAGS),
        layer=PTC_FUNCTIONAL_TESTING))
    suite.addTest(unittest.makeSuite(BlobMarshallTest))
    return suite
