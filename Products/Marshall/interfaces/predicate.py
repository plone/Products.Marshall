"""
Interfaces for Predicate

$Id: predicate.py,v 1.1 2004/07/23 16:16:29 dreamcatcher Exp $
"""

from Interface import Interface

class IPredicate(Interface):
    """ A Predicate """

    def apply(obj, **kw):
        """Return a sequence of component names
        if the predicate applies.
        """

    def getComponentName():
        """ Return the component name configured for
        this predicate.
        """

    def setComponentName(component_name):
        """ Change the component name """

    def setExpression(expression):
        """ Change the expression condition """

    def expression(context):
        """ Evaluate the expression using context """

    def getExpression():
        """ Get the expression as text """
