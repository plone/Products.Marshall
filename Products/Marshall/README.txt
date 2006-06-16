Marshall: A framework for pluggable marshalling policies
========================================================

Features
--------

- A ControlledMarshaller class that delegates to underlying implementations
- A marshall registry tool where you can configure some predicates for
  choosing marshallers based on several pieces of information available. 

Copyright
---------

- This code is copyrighted by Enfold Systems, LLC.
  You can find more information at http://www.enfoldsystems.com/

License
-------

- GPL, a LICENSE file should have accompanied this module.  If not
  please contact the package maintainer.

Mantainer
---------

Archetypes Release Manager

  - for Archetypes 1.4: Jens Klein

  - for Archetypes 1.5+: Daniel Nouri


Acknowledgements
----------------

- The workers: Sidnei da Silva

  o Sidnei da Silva - Designer, Test Champion and Master of Laziness

  o Alan Runyan - Cheerleading.

  o Zope Europe Association - Sponsoring

- Zope Corporation for providing such a wonderful application server.

- Python Developers for making things so damn easy.

Requirements
------------

- Python 2.3.5 or greater

- Zope 2.7.8 or greater

- Plone 2.1.1 or greater

- Archetypes 1.3.5+ (a bug with BooleanField was fixed right after 1.3.5)

- libxml2 2.6.6+ (previous versions seem to have a bug validating RelaxNG)

- DavPack (optional) to support rename-on-upload
