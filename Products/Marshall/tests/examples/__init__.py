# import this
from Products.Archetypes.public import listTypes, process_types

import person
process_types(listTypes('tests.Marshall'), 'tests.Marshall')
