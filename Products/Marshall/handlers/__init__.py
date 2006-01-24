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
$Id$
"""
from Products.Marshall.registry import registerComponent

# Register default Archetypes marshallers
from Products.Archetypes.Marshall import PrimaryFieldMarshaller
from Products.Archetypes.Marshall import RFC822Marshaller

registerComponent('primary_field', 'Primary Field Marshaller',
                  PrimaryFieldMarshaller)
registerComponent('rfc822', 'RFC822 Marshaller',
                  RFC822Marshaller)

# Now register our own marshallers
try:
    import libxml2
except ImportError:
    # XXX can't import libxml2
    import warnings
    warnings.warn('libxml2 not available. Unable to register libxml2 based ' \
                  'marshallers')
else:
    from Products.Marshall.handlers._xml import SimpleXMLMarshaller
    from Products.Marshall.handlers._xml import ATXMLMarshaller

    registerComponent('simple_xml', 'Simple XML Marshaller',
                      SimpleXMLMarshaller)
    registerComponent('atxml', 'ATXML Marshaller',
                      ATXMLMarshaller)
