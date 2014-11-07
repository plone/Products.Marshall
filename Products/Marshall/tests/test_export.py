import glob
import os
import re
import zipfile

# Load fixture
from Testing import ZopeTestCase
from Products.Marshall.tests.base import BaseTest

# Install our product
ZopeTestCase.installProduct('Marshall')
ZopeTestCase.installProduct('Archetypes')
ZopeTestCase.installProduct('ATContentTypes')

from Products.CMFCore.utils import getToolByName
from Products.Marshall import registry
from Products.Marshall.registry import Registry, getRegisteredComponents
from Products.Marshall.registry import getComponent
from Products.Marshall.tests import PACKAGE_HOME
tool_id = Registry.id

def normalize_xml(s):
    s = re.sub(r"[ \t]+", " ", s)
    return s


def import_file(relparts, fname, target, handler):
    marshaller = getComponent(handler)
    f = open(fname, 'rb+')
    content = f.read()
    f.close()
    curr = parent = target
    for p in relparts[:-1]:
        curr = parent.restrictedTraverse(p, None)
        if curr is None:
            parent.invokeFactory('Folder', p)
            curr = parent.restrictedTraverse(p)
        parent = curr
    obj_id = relparts[-1]
    obj = parent.restrictedTraverse(obj_id, None)
    if obj is None:
        parent.invokeFactory('Document', obj_id)
        obj = parent.restrictedTraverse(obj_id)
    marshaller.demarshall(obj, content)
    return

IGNORE_NAMES = ('CVS', '.svn')
def fromFS(base, target, metadata='atxml', data='primary_field'):
    paths = []
    ignore = lambda x: filter(None, [x.endswith(n) for n in IGNORE_NAMES])
    def import_metadata(relparts, fname, target, handler=metadata):
        return import_file(relparts, fname, target, handler)
    def import_data(relparts, fname, target, handler=data):
        return import_file(relparts, fname, target, handler)
    def import_func(arg, dirname, names):
        # Remove ignored filenames
        [names.remove(n) for n in names if ignore(n)]
        names = map(os.path.normcase, names)
        for name in names:
            fullname = os.path.join(dirname, name)
            if not os.path.isfile(fullname):
                continue
            fparts = fullname.split(os.sep)
            bparts = base.split(os.sep)
            relparts = fparts[len(bparts):]
            relpath = '/'.join(relparts)
            arg.append(relpath)
            if '.metadata' in dirname:
                relparts.remove('.metadata')
                import_metadata(relparts, fullname, target)
            else:
                import_data(relparts, fullname, target)
    os.path.walk(base, import_func, paths)
    return paths

class ExportTest(BaseTest):

    def afterSetUp(self):
        super(ExportTest, self).afterSetUp()
        self.loginPortalOwner()
        registry.manage_addRegistry(self.portal)
        self.tool = getToolByName(self.portal, tool_id)

    def test_export(self):
        self.portal.invokeFactory('Folder', 'test_data')
        self.folder = self.portal.test_data
        paths = fromFS(self.base, self.folder)
        paths.sort()
        obj_paths = filter(lambda x: '.metadata' not in x, paths)
        data = self.tool.export(self.folder, obj_paths)
        zipf = zipfile.ZipFile(data)
        self.assertEquals(zipf.testzip(), None)
        zipl = zipf.namelist()
        zipl.sort()
        self.assertEquals(zipl, paths)

def test_suite():
    import unittest
    suite = unittest.TestSuite()
    dirs = glob.glob(os.path.join(PACKAGE_HOME, 'export', '*'))
    comps = [i['name'] for i in getRegisteredComponents()]
    for d in dirs:
        prefix = os.path.basename(d)
        if prefix not in comps:
            continue
        k_dict = {'base':d,
                  'prefix':prefix}
        klass = type('%sExportTest' % prefix,
                     (ExportTest,),
                     k_dict)
        suite.addTest(unittest.makeSuite(klass))
    return suite
