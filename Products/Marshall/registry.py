"""
$Id: registry.py,v 1.1 2004/07/23 16:16:25 dreamcatcher Exp $
"""

from OFS.OrderedFolder import OrderedFolder
from Globals import PersistentMapping, InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view, manage_properties
from Products.Marshall.interfaces import IPredicate
from Products.Marshall.config import TOOL_ID
from Products.Marshall.export import Export

class RegistryItem:

    def __init__(self, name, title, factory):
        self.name = name
        if not title:
            title = name
        self.title = title
        self.factory = factory

    def info(self):
        return {'name':self.name,
                'title':self.title}

    def create(self, id, title, expression, component_name):
        return self.factory(id, title or self.title, expression, component_name)

comp_registry = {}
def registerComponent(name, title, component):
    comp_registry[name] = RegistryItem(name, title, component)

def getRegisteredComponents():
    return [item.info() for item in comp_registry.values()]

def getComponent(name):
    return comp_registry[name].factory()

registry = {}
def registerPredicate(name, title, component):
    component.predicate_type = title
    registry[name] = RegistryItem(name, title, component)

def getRegisteredPredicates():
    return [item.info() for item in registry.values()]

def createPredicate(name, id, title, expression, component_name):
    return registry[name].create(id, title, expression, component_name)

class Registry(OrderedFolder, Export):
    """ A registry that holds predicates and applies them to
    objects in the hope of selecting the right one that matches
    a given set of constraints.
    """

    meta_type = 'Marshaller Registry'
    id = TOOL_ID
    security = ClassSecurityInfo()

    def __init__(self, id='', title=''):
        OrderedFolder.__init__(self, self.id)
        self.title = title or self.meta_type

    def all_meta_types(self):
        return OrderedFolder.all_meta_types(self, interfaces=(IPredicate,))

    security.declareProtected(view, 'getMarshallerFor')
    def getMarshallersFor(self, obj, **kw):
        set = []
        for predicate in self.objectValues():
            # An OrderedSet, in the lack of a real one.
            # The order in which predicates are evaluated
            # is managed by the underlying OrderedFolder impl.
            [set.append(s) for s in predicate.apply(obj, **kw)
             if s not in set]
        return tuple(set)

InitializeClass(Registry)

def manage_addRegistry(self, REQUEST=None, **ignored):
    """ Factory method that creates a Registry"""
    obj = Registry()
    self._setObject(obj.id, obj)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')
    else:
        return self._getOb(obj.id)
