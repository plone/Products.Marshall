========
Marshall
========

A framework for pluggable marshalling policies
==============================================

:Author: Sidnei da Silva
:Contact: sidnei@awkly.org
:Date: $Date$
:Version: $Revision: 1.1 $

People coming to Plone from other CMS or from no CMS at all often want
to be able to bulk import existing content. There are also cases of
sites which produce a high volume of content that needs to be
published constantly.

The easiest way to achieve the goal of allowing import/export of
structured content currently is through introspectable
schemas. Archetypes provides this right now. However, Archetypes
expects a schema to have only one marshaller component, and the
default ones are not able to marshall all the facets of a complex
piece of content by themselves.

The Marshall product provides the missing pieces of this complicated
puzzle by giving you:

- A ``ControlledMarshaller`` implementation, which resorts on a tool
  to decide which marshaller implementation should be used for
  marshalling a given piece of content or demarshalling an uploaded
  file.

- A ``marshaller_tool`` which sits on the root of your CMF/Plone site
  and that allows you to do fine grained control of marshallers.

- Simple export functionality to dump the Archetypes-based objects of
  your CMF/Plone site as a hierarchy of files in .zip format.

Installation
------------

Installing is as simple as clicking a button, thanks to
QuickInstaller. However, by default only the ``marshaller_tool`` is
installed. After that, you need to add some ``marshaller predicates``
by yourself. You can do that through the ZMI. The interface should be
verbose enough to tell you all that you need to know to be able to
make a simple setup.

Let's go through a step-by-step example on how to setup the ``Marshaller
Registry`` programatically.

If you follow the steps listed here, you will have a working setup
that can handle uploading either a ``ATXML`` file, or some other file
containing whatever you like.

Assuming you already installed the ``Marshall`` and the
``ArchExample`` products using the quick-installer tool, the next step
is to add a couple marshaller predicates.

Our setup will consist of two predicates: one for handling ``ATXML``
files, and another dummy predicate to be used as a ``fallback``, ie:
if it's not ATXML, use the dummy predicate.

Add a predicate of the ``xmlns_attr`` kind. This kind of predicate is
used to check for the existence of a certain attribute or element in a
XML file. If the predicate matches, we will map it to the ``atxml``
marshaller (component_name).

    >>> from Products.Marshall.predicates import add_predicate
    >>> from Products.Marshall.config import TOOL_ID as marshall_tool_id
    >>> from Products.Marshall.config import AT_NS, CMF_NS
    >>> from Products.CMFCore.utils import getToolByName

    >>> tool = getToolByName(self.portal, marshall_tool_id)
    >>> p = add_predicate(tool, id='atxml',
    ...                   title='ATXML Predicate',
    ...                   predicate='xmlns_attr',
    ...                   expression='',
    ...                   component_name='atxml')

Then edit the predicate so that it matches on the existence of a
element named ``metadata`` using the ``AT_NS`` namespace.

    >>> p.edit(element_ns=AT_NS, element_name='metadata', value=None)

Add a default predicate, that just maps to the ``primary_field``
marshaller (which just stuffs the content of the uploaded file into
the object's primary field).

    >>> p = add_predicate(tool, id='default',
    ...                   title='Default Marshaller',
    ...                   predicate='default',
    ...                   expression='',
    ...                   component_name='primary_field')

The next step is making your Archetypes-based schema aware of the
Marshaller Registry, by making it use the ``ControlledMarshaller``
implementation.

For our example, we will use the ``Article`` class from the
``ArchExample`` product.

    >>> from Products.ArchExample.Article import Article
    >>> from Products.Marshall import ControlledMarshaller

Save current marshaller implementation, and register
``ControlledMarshaller`` on it's place.

    >>> old_marshall = Article.schema.getLayerImpl('marshall')
    >>> Article.schema.registerLayer('marshall',
    ...                              ControlledMarshaller())

At this point, our Article should be able to use the Marshaller
Registry to decide what Marshaller to use at runtime.

    >>> from Products.Archetypes.tests.utils import makeContent
    >>> article = makeContent(self.portal, 'Article', 'article')
    >>> article.getId()
    'article'

    >>> article.Title()
    ''

    >>> article.setTitle('Example Article')
    >>> article.Title()
    'Example Article'

    >>> article.getPortalTypeName()
    'Article'

    >>> article.getBody()
    ''

