"""
$Id: __init__.py,v 1.1 2004/07/23 16:16:26 dreamcatcher Exp $
"""

from _base import Predicate, constructors, manage_addPredicate
add_predicate = manage_addPredicate

# Kick registration of submodules
import _xmlns
