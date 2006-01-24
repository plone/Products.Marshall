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

import os
import thread
import base64
from types import ListType, TupleType
from xml.dom import minidom
from cStringIO import StringIO
from DateTime import DateTime
from OFS.Image import File
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.BaseObject import BaseObject
from Products.Archetypes.Marshall import Marshaller
from Products.Archetypes.Field import ReferenceField
from Products.Archetypes.config import REFERENCE_CATALOG, UUID_ATTR
from Products.Archetypes.utils import shasattr
from Products.Archetypes.debug import log
from Products.Marshall.config import AT_NS, CMF_NS, ATXML_SCHEMA
from Products.Marshall.exceptions import MarshallingException

def stringify(value):
    if isinstance(value, File):
        value = getattr(value, 'data', value)
    return str(value)

class SimpleXMLMarshaller(Marshaller):

    def demarshall(self, instance, data, **kwargs):
        doc = libxml2.parseDoc(data)
        p = instance.getPrimaryField()
        pname = p and p.getName() or None
        try:
            fields = [f for f in instance.Schema().fields()
                      if f.getName() != pname]
            for f in fields:
                items = doc.xpathEval('/*/%s' % f.getName())
                if not len(items): continue
                # Note that we ignore all but the first element if
                # we get more than one
                value = items[0].children
                if not value:
                    continue
                mutator = f.getMutator(instance)
                if mutator is not None:
                    mutator(value.content.strip())
        finally:
            doc.freeDoc()

    def marshall(self, instance, **kwargs):
        response = minidom.Document()
        doc = response.createElement(instance.portal_type.lower())
        response.appendChild(doc)

        p = instance.getPrimaryField()
        pname = p and p.getName() or None
        fields = [f for f in instance.Schema().fields()
                  if f.getName() != pname]

        for f in fields:
            value = instance[f.getName()]
            values = [value]
            if type(value) in [ListType, TupleType]:
                values = [str(v) for v in value]
            elm = response.createElement(f.getName())
            for value in values:
                value = response.createTextNode(stringify(value))
                elm.appendChild(value)
            doc.appendChild(elm)

        content_type = 'text/xml'
        data = response.toprettyxml().encode('utf-8')
        length = len(data)

        return (content_type, length, data)

class ns:

    def __init__(self, xmlns, prefix, *attrs):
        self.xmlns, self.prefix, self.attrs = xmlns, prefix, attrs
        self._byfield = dict([(a.field, a) for a in attrs])
        self._byname = dict([(a.name, a.field) for a in attrs])

    def getField(self, name, default=None):
        return self._byname.get(name, default)

    def getAttr(self, field, default=None):
        return self._byfield.get(field, default)

class attr:

    def __init__(self, name, field=None, many=False, process=()):
        if field is None:
            field = name
        self.name, self.field, self.many = name, field, many
        self.process = process

class reference(dict):

    index_map = dict([('title', 'Title'),
                      ('description', 'Description'),
                      ('creation_date', 'created'),
                      ('modification_data', 'modified'),
                      ('creators', 'Creator'),
                      ('subject', 'Subject'),
                      ('effectiveDate', 'effective'),
                      ('expirationDate', 'expires'),
                      ])

    def resolve(self, context):
        uid = self.get('uid')
        rt = getToolByName(context, REFERENCE_CATALOG)
        if uid is not None:
            return rt.lookupObject(uid)
        path = self.get('path')
        if path is not None:
            return context.restrictedTraverse(path, None)
        ct = getToolByName(context, 'portal_catalog')
        params = [(k, v) for k, v in self.items()
                  if k not in ('uid', 'path')]
        kw = [(self.index_map.get(k), v) for k, v in params]
        kw = dict(filter(lambda x: x[0] is not None and x, kw))
        res = ct(**kw)
        if not res:
            return None

        # First step: Try to filter by brain metadata
        # *Usually* a metadata item will exist with the same name
        # as the index.
        verify = lambda obj: filter(None, [obj[k] == v for k, v in kw.items()])
        for r in res:
            # Shortest path: If a match is found, return immediately
            # instead of checking all of the results.
            if verify(r):
                return r.getObject()

        # Second step: Try to get the real objects and look
        # into them. Should be *very* slow, so use with care.
        # We use __getitem__ to access the field raw data.
        verify = lambda obj: filter(None, [obj[k] == v for k, v in params])
        valid = filter(verify, [r.getObject() for r in res])
        if not valid:
            return None
        if len(valid) > 1:
            raise MarshallingException, ('Metadata reference does not '
                                         'uniquely identifies the reference.')
        return valid[0]

class ctx: pass

class normalizer:

    def space(cls, text):
        return '\n'.join([s.strip() for s in text.splitlines()])
    space = classmethod(space)

    def newline(cls, text):
        return ' '.join([s.strip() for s in text.splitlines()])
    newline = classmethod(newline)

# Some constants for use below
_marker = []
XMLNS_NS = 'http://www.w3.org/2000/xmlns/'
XMLREADER_START_ELEMENT_NODE_TYPE = 1
XMLREADER_END_ELEMENT_NODE_TYPE = 15
XMLREADER_TEXT_ELEMENT_NODE_TYPE = 3
XMLREADER_CDATA_NODE_TYPE = 4

# Initialize ATXML RNG Schema
ATXML_RNG = open(os.path.join(ATXML_SCHEMA, 'atxml.rng'), 'rb+').read()

# libxml2 initialization. Register a per-thread global error callback.
import libxml2
libxml2.initParser()

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

error_callback = ErrorCallback()
libxml2.registerErrorHandler(error_callback, "")

class ATXMLMarshaller(Marshaller):

    # Just a plain list of ns objects.
    namespaces = [ns('adobe:ns:meta', 'xmp',
                     attr('CreateDate', 'creation_date'),
                     attr('ModifyDate', 'modification_date')),
                  ns('http://purl.org/dc/elements/1.1/', 'dc',
                     attr('title', process=(normalizer.space,
                                            normalizer.newline)),
                     attr('description', process=(normalizer.space,)),
                     attr('subject', many=True),
                     attr('contributor', 'contributors', many=True),
                     attr('creator', 'creators', many=True),
                     attr('rights'),
                     attr('language')),
                  ns(CMF_NS, 'cmf',
                     attr('type'))
                  ]
    # Mapping of xmlns URI to ns object
    ns_map = dict([(ns.xmlns, ns) for ns in namespaces])
    # Mapping of prefix -> xmlns URI
    prefix_map = dict([(ns.prefix, ns.xmlns) for ns in namespaces])
    # Flatten ns into (ns, attr) tuples
    flat_ns = []
    [flat_ns.extend(zip((n,)*len(n.attrs), n.attrs)) for n in namespaces]
    # Dict mapping an AT fieldname to a (prefix, element name) tuple
    field_map = dict([(a.field, (n.prefix, a.name)) for n, a in flat_ns])

    def demarshall(self, instance, data, **kwargs):
        error_callback.clear()
        # libxml2.debugMemory(1)
        libxml2.lineNumbersDefault(1)
        input = kwargs.get('file')
        if not input:
            input = StringIO(data)
        input_source = libxml2.inputBuffer(input)
        reader = input_source.newTextReader("urn:%s" % instance.absolute_url())

        # Initialize RNG schema validation.
        rngp = libxml2.relaxNGNewMemParserCtxt(ATXML_RNG, len(ATXML_RNG))
        rngs = rngp.relaxNGParse()
        reader.RelaxNGSetSchema(rngs)

        # Some elements may occur more than once, so we defer
        # calling the mutator until we collected all the values.
        deferred = {}
        field_values = {}
        field_extras = {}
        refs = {}
        stack = []

        schema_fields = instance.Schema().fields()
        fields = [(f.getName(), (f.getMutator(instance), f))
                  for f in schema_fields]
        # Collect LinesFields which may not present on our namespace definition
        defer_fields = dict([(f.getName(), True)
                             for f in schema_fields
                             if getattr(f, 'type', None) == 'lines'])
        # Filter out non-existing mutators (probably meaning read-only fields)
        mutators = dict(filter(lambda x: x[1][0] is not None, fields))
        c = ctx()
        c.is_at = c.is_ref = c.ns = c.name = c.fname = None
        c.value = _marker
        at_uid = _marker
        stack.append(c)
        ret = reader.Read()
        is_ref = False
        read = False
        while ret == 1:
            if read:
                ret = reader.Read()
            read = True
            if reader.NodeType() == XMLREADER_END_ELEMENT_NODE_TYPE:
                c = stack.pop()
                if c.is_at and reader.LocalName() == 'reference':
                    is_ref = False
            if reader.NodeType() == XMLREADER_START_ELEMENT_NODE_TYPE:
                c = ctx()
                c.is_at = c.attr = c.ns = c.name = c.defer = c.fname = None
                c.value = _marker
                stack.append(c)
                # By default, anything that isn't an AT field should
                # be registered with an namespace. If it isn't, then
                # we plain ignore it.
                c.is_at = reader.NamespaceUri() == AT_NS
                if not c.is_at:
                    c.ns = self.ns_map.get(reader.NamespaceUri())
                    if c.ns is None:
                        # Unknown namespace
                        continue
                    c.name = reader.LocalName()
                    c.fname = c.ns.getField(c.name)
                    if c.fname is None:
                        # Unknown field
                        continue
                    c.attr = c.ns.getAttr(c.fname)
                    if c.attr.many:
                        c.defer = True
                # If it's in the AT_NS namespace, then it should
                # map to a field. The field name is then given by the
                # 'id' attribute of the element.
                if c.is_at:
                    if reader.LocalName() == 'metadata':
                        # It's the outermost element
                        continue
                    if reader.LocalName() == 'reference':
                        # It's a reference
                        is_ref = True
                        fname = stack[-2].fname
                        _refs = refs.setdefault(fname, [])
                        ref = reference()
                        _refs.append(ref)
                        continue
                    if reader.LocalName() in ('uid', 'path',):
                        # If uid and not is_ref, it's the object UID
                        # If path and not is_ref, then it's an error. RelaxNG
                        # validation should catch that though.
                        # If uid or path and is_ref, then its a reference.
                        c.name = c.fname = reader.LocalName()
                    else:
                        # Look for field name on at:id attribute
                        while reader.MoveToNextAttribute():
                            # Should be on AT_NS namespace
                            if reader.LocalName() in ('id',):
                                # Note that if there shouldn't exist
                                # a field named 'uid' as that's a reserved
                                # word for us.
                                c.name = c.fname = reader.Value()
                                # Currently, only LinesFields will
                                # fall into this category
                                if defer_fields.get(c.fname):
                                    c.defer = True
                            if reader.LocalName() in (
                                'content_type', 'filename'):
                                attr = reader.LocalName()
                                setattr(c, attr, reader.Value())
            elif reader.NodeType() in (
                XMLREADER_TEXT_ELEMENT_NODE_TYPE,
                XMLREADER_CDATA_NODE_TYPE):
                # The value to be set on the field should always be in
                # a #text element inside the field element or in a
                # CDATA section.
                c.value = reader.Value()
                if c.value is not None:
                    if reader.NodeType() in (
                        XMLREADER_TEXT_ELEMENT_NODE_TYPE,):
                        # Strip whitespace and newlines only for text
                        # elements.
                        c.value = c.value.strip()
                    # Some values may require some extra processing.
                    if c.attr is not None:
                        for proc in c.attr.process:
                            c.value = proc(c.value)
            if c.fname is None:
                # Couldn't find a field name.
                continue
            if not is_ref:
                if c.fname in ('uid',):
                    # It's the UID!
                    at_uid = c.value
                    continue
                mutator, field = mutators.get(c.fname, (None, None))
                if mutator is None:
                    # Found a field name, but doesn't match any
                    # schema field or the field didn't had a mutator.
                    continue
            if c.value is _marker:
                # Didn't get to the value yet. Most likely on the
                # next iteration. Notice that value is given by the
                # #text node inside the element in which we found
                # the field name.
                continue
            # If an element can have multiple values, we defer
            # changing it until we collected all the values.
            if c.defer is True:
                if is_ref:
                    vdefer = ref.setdefault(c.fname, [])
                else:
                    vdefer = deferred.setdefault(c.fname, [])
                if c.value not in vdefer:
                    vdefer.append(c.value)
                continue
            if is_ref:
                ref[c.fname] = c.value
            else:
                ct = getattr(c, 'content_type', None)
                fn = getattr(c, 'filename', None)
                value = c.value
                if fn is not None:
                    # It's some file-ish thing.
                    if ct is not None and not ct.startswith('text'):
                        # It's a blob-ish thing, we expect it to be
                        # base64 encoded.
                        value = value.decode('base64')
                    field_extras[c.fname] = {'mimetype': ct,
                                             'filename': fn}
                field_values[c.fname] = value

        is_input_valid = reader.IsValid()
        # libxml2 cleanups. Don't keep references around
        # for longer than we need.
        del rngp
        del rngs
        del reader
        del input_source
        del input
        libxml2.relaxNGCleanupTypes()
        # Memory debug specific
        libxml2.cleanupParser()
        # Useful for debugging memory errors
        # if libxml2.debugMemory(1) == 0:
        #    print "OK"
        # else:
        #    print "Memory leak %d bytes" % (libxml2.debugMemory(1))
        # libxml2.dumpMemory()

        __traceback_info__ = (data, stack, c.__dict__.items())

        if ret != 0:
            errors = error_callback.get(clear=True)
            log(errors)
            raise MarshallingException, ("There was an error parsing the "
                                         "input. Please make sure that it "
                                         "is well formed and try again.\n"
                                         "%s" % errors)
        if is_input_valid != 1:
            errors = error_callback.get(clear=True)
            log(errors)
            raise MarshallingException, ("Input failed to validate against "
                                         "the ATXML RelaxNG schema.\n"
                                         "%s" % errors)
        error_callback.clear()

        # First thing to do: Try to set the UID if there's one.
        if at_uid is not _marker:
            existing = getattr(instance, UUID_ATTR, _marker)
            if existing is _marker or existing != at_uid:
                ref = reference(uid=at_uid)
                target = ref.resolve(instance)
                if target is not None:
                    raise MarshallingException, (
                        "Trying to set uid of "
                        "%s to an already existing uid "
                        "clashed with %s" % (
                        instance.absolute_url(), target.absolute_url()))
                instance._setUID(at_uid)

        for fname, value in field_values.items():
            # Mutator should be guaranteed to exist, given that
            # field_values is set *after* checking for an existing
            # mutator above.
            mutator, field = mutators.get(fname, (None, None))
            kw = field_extras.get(fname, {})
            mutator(value, **kw)

        # Now that we are done with normal fields, handle
        # deferred fields.
        for fname, value in deferred.items():
            # Mutator should be guaranteed to exist, given that
            # deferred is set *after* checking for an existing
            # mutator above.
            mutator, field = mutators.get(fname, (None, None))
            # Let's assume that if a field was deferred for having
            # multiple values that it is an LinesField and thus can
            # handle input joined with '\n'. This should be the case in
            # 90% of the cases anyway.
            value = '\n'.join(value)
            mutator(value)

        # And then, handle references
        for fname, _refs in refs.items():
            # Mutator is not guaranteed to exist in this case
            mutator, field = mutators.get(fname, (None, None))
            if mutator is None:
                continue
            values = []
            for ref in _refs:
                value = ref.resolve(instance)
                if value is None:
                    raise MarshallingException, ('Could not resolve '
                                                 'reference %r' % ref)
                values.append(value)
            if values:
                mutator(values)

    def marshall(self, instance, **kwargs):
        ns = []
        add_ns = lambda n: n != AT_NS and n not in ns and ns.append(n)
        response = minidom.Document()

        # The outermost element is AT_NS:metadata
        doc = response.createElementNS(AT_NS, 'metadata')
        response.appendChild(doc)

        # Set the default xmlns attribute
        attr = response.createAttribute('xmlns')
        attr.value = AT_NS
        doc.setAttributeNode(attr)

        # Then, the next thing should be the cmf:type element
        # containing the portal_type of the item
        elm = response.createElementNS(CMF_NS, 'cmf:type')
        value = response.createTextNode(str(instance.portal_type))
        elm.appendChild(value)
        doc.appendChild(elm)
        add_ns(CMF_NS)

        # And then, the object uid.
        elm = response.createElementNS(AT_NS, 'uid')
        # The UUID_ATTR should *always* exist.
        value = response.createTextNode(getattr(instance, UUID_ATTR))
        elm.appendChild(value)
        doc.appendChild(elm)

        for f in instance.Schema().fields():
            fname = f.getName()

	    # We need to handle references in different ways.
            is_ref = isinstance(f, ReferenceField)
            __traceback_info__ = (instance, fname)
            # Use __getitem__ directly, which deals properly with edit
            # accessors and normal accessors.
            value = instance[fname]
            if isinstance(value, DateTime):
                value = value.HTML4()
            values = [value]
            if type(value) in [ListType, TupleType]:
                values = value
            non_empty = lambda x: str(x) not in ('',)
            # Don't export empty values.
            values = filter(non_empty, values)
            if not values:
                continue
            if is_ref and values in ([None],):
                # Don't export null refs
                continue
            elns = AT_NS
            elname = 'field'
            elinfo = self.field_map.get(fname)
            if elinfo is not None:
                elname = '%s:%s' % elinfo
                elns = self.prefix_map[elinfo[0]]
            add_ns(elns)
            for value in values:
                # In the case of multiple values, we create one element for
                # each value.
                elm = response.createElementNS(elns, elname)
                # AT_NS elements have an 'id' attribute with the field name.
                if elns == AT_NS:
                    attr = response.createAttributeNS(AT_NS, 'id')
                    attr.value = fname
                    elm.setAttributeNode(attr)
                if is_ref:
                    # References have a <uid> element
                    r = response.createElementNS(AT_NS, 'reference')
                    u = response.createElementNS(AT_NS, 'uid')
                    value = response.createTextNode(str(value))
                    u.appendChild(value)
                    r.appendChild(u)
                    value = r
                else:
                    # Store content_type and filename as
                    # attributes on the enclosing element.
                    ct = fn = None
                    if shasattr(f, 'getFilename'):
                        fn = f.getFilename(instance)
                        attr = response.createAttributeNS(
                            AT_NS, 'filename')
                        attr.value = fn
                        elm.setAttributeNode(attr)
                    if fn is not None and shasattr(f, 'getContentType'):
                        ct = f.getContentType(instance)
                        attr = response.createAttributeNS(
                            AT_NS, 'content_type')
                        attr.value = ct
                        elm.setAttributeNode(attr)
                    # Make sure it's a string
                    # XXX Beware of memory consumption.
                    value = stringify(value)
                    if fn is not None:
                        # If it has a filename, it's probably a
                        # blob-ish field.
                        if ct is not None and not ct.startswith('text'):
                            # If it's non-text-ish then store it
                            # base64 encoded.
                            value = value.encode('base64')
                    if ct is not None and fn is not None:
                        # File-ish, make a CDATA section.
                        value = response.createCDATASection(value)
                    else:
                        # Otherwise, just store it as a text node.
                        value = response.createTextNode(value)
                elm.appendChild(value)
                elm.normalize()
                doc.appendChild(elm)

        # Last thing: declare all namespaces.
        for n in ns:
            prefix = self.ns_map[n].prefix
            attrname = 'xmlns:%s' % prefix
            attr = response.createAttribute(attrname)
            attr.value = n
            doc.setAttributeNode(attr)

        content_type = 'text/xml'
        data = response.toprettyxml().encode('utf-8')
        length = len(data)

        return (content_type, length, data)
