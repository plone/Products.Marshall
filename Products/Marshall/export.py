# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004-2006 Enfold Systems, LLC
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
"""

from App.class_init import InitializeClass
from ExtensionClass import Base
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Products.CMFCore.permissions import ManagePortal
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from six.moves import cStringIO as StringIO

import os
import six
import zipfile


class Export(Base):

    security = ClassSecurityInfo()

    security.declareProtected(ManagePortal, 'atxml_template')
    atxml_template = PageTemplateFile('www/atxml', globals(),
                                      __name__='atxml_template')

    @security.protected(ManagePortal)
    def marshall_data(self, obj):
        from Products.Marshall.registry import getComponent
        marshaller = getComponent('primary_field')
        return self.marshall(obj, marshaller)

    @security.protected(ManagePortal)
    def marshall_metadata(self, obj):
        from Products.Marshall.registry import getComponent
        marshaller = getComponent('atxml')
        return self.marshall(obj, marshaller)

    @security.protected(ManagePortal)
    def marshall(self, obj, marshaller):
        REQUEST = obj.REQUEST
        RESPONSE = REQUEST.RESPONSE
        ddata = marshaller.marshall(obj, REQUEST=REQUEST,
                                    RESPONSE=RESPONSE)
        if hasattr(aq_base(obj), 'marshall_hook') \
           and obj.marshall_hook:
            ddata = obj.marshall_hook(ddata)

        content_type, length, data = ddata

        if isinstance(data, six.string_types):
            return StringIO(data)

        s = StringIO()
        while data is not None:
            s.write(data.data)
            data = data.next
        s.seek(0)
        return s

    @security.protected(ManagePortal)
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

    @security.protected(ManagePortal)
    def export_info(self, context, info):
        data = StringIO()
        out = zipfile.ZipFile(data, 'w')

        for d in info:
            path = d.get('path', d.get('id'))
            filename = os.path.basename(path)
            dir_path = os.path.dirname(path)

            # Write data
            _d = d.get('data', '')
            fpath = os.path.join(dir_path, filename)
            out.writestr(fpath, _d)

            metadata = d.copy()
            for name in ('data', 'path'):
                if name in metadata:
                    del metadata[name]
            # Write metadata
            metadata_path = os.path.join(dir_path, '.metadata')
            fpath = os.path.join(metadata_path, filename)
            _d = str(self.atxml_template(info=metadata))
            out.writestr(fpath, _d)

        out.close()
        data.seek(0)
        return data


InitializeClass(Export)
