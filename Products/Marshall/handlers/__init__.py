"""
$Id: __init__.py,v 1.1 2004/07/23 16:16:26 dreamcatcher Exp $
"""
from Products.Marshall.registry import registerComponent
from Products.Marshall.handlers._xml import SimpleXMLMarshaller
from Products.Marshall.handlers._xml import ATXMLMarshaller
from Products.Archetypes.Marshall import PrimaryFieldMarshaller
from Products.Archetypes.Marshall import RFC822Marshaller


# Register default Archetypes marshallers
registerComponent('primary_field', 'Primary Field Marshaller',
                  PrimaryFieldMarshaller)
registerComponent('rfc822', 'RFC822 Marshaller',
                  RFC822Marshaller)

# Now register our own marshallers
registerComponent('simple_xml', 'Simple XML Marshaller',
                  SimpleXMLMarshaller)
registerComponent('atxml', 'ATXML Marshaller',
                  ATXMLMarshaller)
