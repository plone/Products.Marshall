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


