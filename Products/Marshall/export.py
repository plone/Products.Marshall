"""
$Id: export.py,v 1.1 2004/07/23 16:16:26 dreamcatcher Exp $
"""

import os
import tempfile
import zipfile
import shutil
from cStringIO import StringIO
from ExtensionClass import Base
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName

class Export(Base):

    def marshall_data(self, obj):
        from Products.Marshall.registry import getComponent
        marshaller = getComponent('primary_field')
        return self.marshall(obj, marshaller)

    def marshall_metadata(self, obj):
        from Products.Marshall.registry import getComponent
        marshaller = getComponent('atxml')
        return self.marshall(obj, marshaller)

    def marshall(self, obj, marshaller):
        REQUEST = obj.REQUEST
        RESPONSE = REQUEST.RESPONSE
        ddata = marshaller.marshall(obj, REQUEST=REQUEST,
                                    RESPONSE=RESPONSE)
        if hasattr(aq_base(obj), 'marshall_hook') \
           and obj.marshall_hook:
            ddata = obj.marshall_hook(ddata)

        content_type, length, data = ddata

        if type(data) is type(''): return StringIO(data)

        s = StringIO()
        while data is not None:
            s.write(data.data)
            data=data.next
        s.seek(0)
        return s

    def export(self, context, paths):
        data = StringIO()
        out = zipfile.ZipFile(data, 'w')

        for path in paths:
            filename = os.path.basename(path)
            dir_path = os.path.dirname(path)
            obj = context.restrictedTraverse(path)

            # Write data
            fpath = os.path.join(dir_path, filename)
            stream = self.marshall_data(obj)
            out.writestr(fpath, stream.read())

            # Write metadata
            metadata_path = os.path.join(dir_path, '.metadata')
            fpath = os.path.join(metadata_path, filename)
            stream = self.marshall_metadata(obj)
            out.writestr(fpath, stream.read())
        out.close()
        data.seek(0)
        return data
