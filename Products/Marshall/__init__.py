"""
$Id: __init__.py,v 1.1 2004/07/23 16:16:25 dreamcatcher Exp $
"""

# Kick off Extensions.Install import
import Products.Marshall.Extensions.Install

# Kick off handler registration
from Products.Marshall import handlers
from Products.Marshall import marshaller

def initialize(context):
    from Products.Marshall import registry
    from Products.Marshall import predicates

    context.registerClass(
        registry.Registry,
        permission='Add Marshaller Registry',
        constructors=(registry.manage_addRegistry,),
        icon='www/registry.png',
        )

    context.registerClass(
        instance_class=predicates.Predicate,
        permission='Add Marshaller Predicate',
        constructors=predicates.constructors,
        icon='www/registry.png')

    context.registerHelpTitle('Marshall Help')
    context.registerHelp(directory='interfaces')
