from Products.Archetypes.public import *

class Person(BaseContent):

    schema = BaseSchema + Schema((
        ReferenceField('parents',
                       multiValued=True),
        ReferenceField('children',
                       multiValued=True),
        ReferenceField('father',
                       multiValued=False,
                       required=False),
        ReferenceField('mother',
                       multiValued=False,
                       required=False)
        ))

registerType(Person, 'tests.Marshall')
