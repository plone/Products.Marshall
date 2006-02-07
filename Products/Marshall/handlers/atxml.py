##################################################################
# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004 ObjectRealms, LLC
# Copyright @ 2004 Enfold Systems, LLC
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
##################################################################

"""
generic xml marshaller

 based on registering namespaces with the marshaller,
 the marshaller tries to delegate as much as possible
 to the namespaces, the default implementation of which
 delegates as much as possible to schema attributes
 within that namespace.

 see the Marshall.namespaces package for some sample and
 default namespaces.
 
caveats

 - if you want to use multiple namespaces on the same
   xml node, then this isn't the parser for you. you
   can do some basic hacks around it w/ ParseContext
   namespace delegation.

Authors: kapil thangavelu <k_vertigo@objectrealms.net> (current impl)
         sidnei de silva <sidnei@awkly.org>
         
"""

#################################
import thread
from cStringIO import StringIO
from xml.dom import minidom
import libxml2

from Products.Archetypes.Marshall import Marshaller
from Products.Archetypes.debug import log
from Products.Marshall import config
from Products.Marshall.exceptions import MarshallingException

#################################

_marker = object()

XMLNS_NS = 'http://www.w3.org/2000/xmlns/'
XMLREADER_START_ELEMENT_NODE_TYPE = 1
XMLREADER_END_ELEMENT_NODE_TYPE = 15
XMLREADER_TEXT_ELEMENT_NODE_TYPE = 3

class ErrorCallback:

    def __init__(self):
        self.msgs = {}

    def __call__(self, ctx, msg):
        self.append(msg)

    def append(self, msg):
        tid = thread.get_ident()
        msgs = self.msgs.setdefault(tid, [])
        msgs.append(msg)

    def get(self, clear=False):
        tid = thread.get_ident()
        msgs = self.msgs.setdefault(tid, [])
        if clear: self.clear()
        return ''.join(msgs)

    def clear(self):
        tid = thread.get_ident()
        msgs = self.msgs[tid] = []

# libxml2 initialization. Register a per-thread global error callback.
libxml2.initParser()
error_callback = ErrorCallback()
libxml2.registerErrorHandler(error_callback, "")


class XmlNamespace(object):


    #################################
    # the framework does a bit of introspection on
    # namespaces for some attributes, defined below

    # whether or not this namespace uses fields from an
    # object's at schema. if true then this namespace
    # should also define the get getATFields below
    uses_at_fields = False

    # the xml namespace uri
    xmlns = "http://example.com"

    # the xml namespace prefix
    prefix = "xxx"
    #################################

    def __init__(self):
        for attribute in self.attributes:
            attribute.setNamespace( self )

    def getAttributeByName(self, name):
        """ given an xml name return the schema attribute
        """
        for attribute in self.attributes:
            if attribute.name == name:
                return attribute
        return None

    def getRelaxNG(self):
        """ get the relaxng fragment that defines
        whats in the namespace
        """
        raise NotImplemented("Subclass Responsiblity")

    def getATFields(self):
        """ return the at schema field names which are
        handled by this namespace, this is utilized by
        the AT namespace so it doesn't also handle these
        fields. """
        raise NotImplemented("Subclass Responsiblity")

    def serialize(self, dom_node, parent_node, instance, options):
        """ serialize the instance values to xml
        based on attributes in this namespace
        """
        for attribute in self.attributes:
            attribute.serialize( dom_node, parent_node, instance)

    def deserialize(self, instance, ns_data, options):
        """ given the instance and the namespace data for
        instance, reconstitute this namespace's attributes
        on the instance.
        """
        if not ns_data:
            return 
        for attribute in self.attributes:
            attribute.deserialize( instance, ns_data )

    def processXml(self, context, node):
        """ handle the start of a xml tag with this namespace
        the namespace and the name of the tag are bound to node.

        if this method return false then the node is assumed to
        be junk and it is discarded.
        """ 
        attribute = self.getAttributeByName( node.name )
        if attribute is None:
            return False
        node.attribute = attribute
        return attribute.processXml( context, node)

    def processXmlEnd(self, name, context):
        """ callback invoked when the parser reaches the
        end of an xml node in this namespace.
        """

    def getSchemaInfo( self ):
        """ return information on this namespace's rng schema

        should be an iterable of sets of ( 'defined_name', 'occurence', 'schema')
        where defined name is the name of any top level defined entities in
        the schema, occurence defines the rng occurence value for that entity
        in the object's xml representation, and schema is the rng schema
        definition for the defined entities
        """
        return ()

class SchemaAttribute(object):

    def __init__(self, name, field_name=None):
        self.name, self.field_id = name, field_name or name
        self.namespace = None
        
    def set(self, instance, data):
        """ set the attribute's value on the instance
        """
        raise NotImplemented

    def get(self, instance):
        """ retrieve the schema attribute's value from the instance
        """
        raise NotImplemented

    def serialize(self, dom, instance):
        """ serialize the attribute's instance value into the dom
        """
        raise NotImplemented

    def deserialize(self, instance, ns_data):
        """ give the instance and the namespace data for
        instance, reconstitute this attribute on the instance
        """ 
        self.set( instance, ns_data )

    def processXml(self, context, ctx_node):
        """ callback invoked with a node from the xml stream
        if false is returned the current node is assumed to be
        not interesting and is ignored.
        """
        return True

    def processXmlValue(self, context, value):
        """ callback to process text nodes
        """
        value = value.strip()
        if not value:
            return
        data = context.getDataFor( self.namespace.xmlns )
        data[self.name] = value

    def setNamespace(self, namespace):
        """ sets which namespace the attribute belongs to
        """
        self.namespace = namespace

class DataNode(object):
    """ a data bag holding a namespace uri and a node name
    """
    __slots__ = (
        'ns',
        'name',
        'attribute',
        )

    def __init__(self, ns, name):
        self.ns = ns
        self.name = name
        self.attribute = None

class ParseContext(object):
    """ a bag for holding data values from and for parsing
    """
    def __init__(self, instance, reader, ns_map):
        self.instance = instance
        self.reader = reader # xml reader
        self.ns_map = ns_map # ns_uri -> namepace
        self.data = {} # ns_uri -> ns_data
        self.node = None # current node if any
        self.ns_delegate = None
        
    def getDataFor(self, ns_uri):
        return self.data.setdefault(ns_uri, {})

    def getNamespaceFor(self, ns_uri):
        if self.ns_delegate is not None:
            return self.ns_delegate
        return self.ns_map.get( ns_uri )

    def setNamespaceDelegate( self, namespace):
        self.ns_delegate = namespace

class XmlParser(object):
    """ an abstraction for setting up the xml parser
    """

    def __init__(self, instance, data, use_validation=False, debug_memory=False):
        error_callback.clear()

        if debug_memory:
            libxml2.debugMemory(1)
        libxml2.lineNumbersDefault(1)
        self.input = StringIO(data)
        self.input_source = libxml2.inputBuffer(self.input)
        self.reader = self.input_source.newTextReader("urn:%s" % instance.absolute_url())

        # Initialize RNG schema validation.
        if use_validation:
            self.rngp = libxml2.relaxNGNewMemParserCtxt(ATXML_RNG, len(ATXML_RNG))
            self.rngs = self.rngp.relaxNGParse()
            self.reader.RelaxNGSetSchema(self.rngs)

        self.debug_memory = debug_memory

    def getReader(self):
        return self.reader
    
    def clear(self):
        debug_memory = self.debug_memory
        self.__dict__.clear()

        # XXX are these affecting some global state ?
        libxml2.relaxNGCleanupTypes()
        # Memory debug specific
        libxml2.cleanupParser()

        if debug_memory:
            # Useful for debugging memory errors
            if libxml2.debugMemory(1) == 0:
                print "OK"
            else:
                print "Memory leak %d bytes" % (libxml2.debugMemory(1))
            libxml2.dumpMemory()
        

class ATXMLMarshaller(Marshaller):

    # Just a plain list of ns objects.
    namespaces = []

    # options for a subclass
    use_validation = False

    def getFieldNamespace(self, field):
        namespaces = self.getNamespaceURIMap()
        # Flatten ns into (ns, attr) tuples
        flat_ns = []
        [flat_ns.extend(zip((n,)*len(n.attrs), n.attrs)) for n in namespaces]        
        # Dict mapping an AT fieldname to a (prefix, element name) tuple
        field_map = dict([(a.field, (n.prefix, a.name)) for n, a in flat_ns])
        return field_map
    
    def getNamespaceURIMap(self):
        """ Mapping of xmlns URI to ns object
        """
        ns_map = dict([(ns.xmlns, ns) for ns in self.namespaces])
        return ns_map

    def getNamespacePrefixMap(self):
        """ Mapping of prefix -> xmlns URI
        """
        prefix_map = dict([(ns.prefix, ns.xmlns) for ns in namespaces])

    def getNamespaces(self, namespaces=None):
        if namespaces is None:
            for ns in getRegisteredNamespaces():
                yield ns
            raise StopIteration

        ns = getRegisteredNamespaces()
        for n in ns:
            if n.prefix in namespaces or \
               n.xmlns in namespaces:
                yield n

    def demarshall(self, instance, data, **kwargs):
        context = self.parseContext( instance, data)
        self.processContext( instance, context, kwargs )

    def marshall(self, instance, use_namespaces=None, **kwargs):
        response = minidom.Document()
        node = response.createElementNS( config.AT_NS, 'metadata')
        response.appendChild( node )

        # setup default namespace
        attr = response.createAttribute('xmlns')
        attr.value = config.AT_NS
        node.setAttributeNode(attr)

        for ns in self.getNamespaces( use_namespaces ):
            ns.serialize( response, node, instance, kwargs )
            if not ns.prefix:
                continue
            attrname = 'xmlns:%s' % ns.prefix
            attr = response.createAttribute(attrname)
            attr.value = ns.xmlns
            node.setAttributeNode(attr)                

        content_type = 'text/xml'
        data = response.toprettyxml()#.encode('utf-8')
        length = len(data)
        return (content_type, length, data)

    def parseContext(self, instance, data):        
        parser = XmlParser( instance, data, use_validation=self.use_validation)
        ns_map = self.getNamespaceURIMap()
        reader = parser.getReader()
        context = ParseContext(instance, reader, ns_map)

        self.parseXml( reader, context )

        # libxml2 cleanups. Don't keep references for any longer then nesc.
        del reader, context.reader
        parser.clear()

        if self.use_validation: # and not reader.IsValid():
            errors = error_callback.get(clear=True)
            log(errors)
            raise MarshallingException, ("Input failed to validate against "
                                         "the ATXML RelaxNG schema.\n"
                                         "%s" % errors)
        error_callback.clear()

        return context


    def parseXml(self, reader, context):
        """
        input read and dispatch loop
        """
        read_result = 1
        
        while read_result == 1:
            read_result = reader.Read()

            if reader.NodeType() == XMLREADER_END_ELEMENT_NODE_TYPE:
                namespace_uri  = reader.NamespaceUri()
                namespace = context.getNamespaceFor(namespace_uri)
                if namespace is not None:
                    namespace.processXmlEnd( reader.LocalName(), context )
                context.node = None
            
            elif reader.NodeType() == XMLREADER_START_ELEMENT_NODE_TYPE:
                namespace_uri  = reader.NamespaceUri()
                namespace = context.getNamespaceFor(namespace_uri)
                if namespace is None:
                    continue

                name = reader.LocalName()
                node = DataNode(namespace, name)
                if namespace.processXml( context, node ):
                    context.node = node
                
            elif reader.NodeType() == XMLREADER_TEXT_ELEMENT_NODE_TYPE:
                # The value to be set on the field should always be
                # in a #text element inside the field element.
                if context.node is None:
                    continue
                context.node.attribute.processXmlValue( context,
                                                        reader.Value() )
                
        return read_result

    def processContext(self, instance, context, options):
        """ instantiate instance with data from context
        """
        for ns in getRegisteredNamespaces():
            ns_data = context.getDataFor( ns.xmlns )
            ns.deserialize( instance, ns_data, options )


class _NamespaceCatalog( object ):

    def __init__( self ):
        self._namespaces = {}
        self._order = []

    def registerNamespace( self, namespace, override=False, position=-1):
        if namespace.xmlns in self._namespaces and not override:
            raise RuntimeError("Duplicate Namespace Registration %s"%namespace.xmlns )
        self._namespaces[ namespace.xmlns ] = namespace
        if position == -1:
            position = len( self._order )
        self._order.append( position, namespace.xmlns )

    def getRegisteredNamespaces( self ):
        return [ self._namespaces[ xmlns ] for xmlns in self._order ]


NamespaceCatalog = _NamespaceCatalog()

registerNamespace = NamespaceCatalog.registerNamespace
getRegisteredNamespaces = NamespaceCatalog.getRegisteredNamespaces

def registerNamespace( namespace ):
    if not isinstance( namespace, XmlNamespace):
        namespace = namespace()
    ATXMLMarshaller.namespaces.append( namespace )

def getRegisteredNamespaces():
    return tuple( ATXMLMarshaller.namespaces )


