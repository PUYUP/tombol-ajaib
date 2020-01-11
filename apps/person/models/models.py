from .models_abstract import *
from .models_attribute import *
from .models_validation import *

# PROJECT UTILS
from utils.generals import is_model_registered

__all__ = list()

# 0
if not is_model_registered('person', 'Role'):
    class Role(AbstractRole):
        class Meta(AbstractRole.Meta):
            db_table = 'person_role'

    __all__.append('Role')


# 1
if not is_model_registered('person', 'Person'):
    class Person(AbstractPerson):
        class Meta(AbstractPerson.Meta):
            db_table = 'person'

    __all__.append('Person')


# Attribute
# 2
if not is_model_registered('person', 'Attribute'):
    class Attribute(AbstractAttribute):
        class Meta(AbstractAttribute.Meta):
            db_table = 'person_attribute'

    __all__.append('Attribute')


# 3
if not is_model_registered('person', 'AttributeValue'):
    class AttributeValue(AbstractAttributeValue):
        class Meta(AbstractAttributeValue.Meta):
            db_table = 'person_attribute_value'

    __all__.append('AttributeValue')


# 4
if not is_model_registered('person', 'AttributeOption'):
    class AttributeOption(AbstractAttributeOption):
        class Meta(AbstractAttributeOption.Meta):
            db_table = 'person_attribute_option'

    __all__.append('AttributeOption')


# 5
if not is_model_registered('person', 'AttributeOptionGroup'):
    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        class Meta(AbstractAttributeOptionGroup.Meta):
            db_table = 'person_attribute_option_group'

    __all__.append('AttributeOptionGroup')


# 6
if not is_model_registered('person', 'Option'):
    class Option(AbstractOption):
        class Meta(AbstractOption.Meta):
            db_table = 'person_option'

    __all__.append('Option')


# Validation
# 7
if not is_model_registered('person', 'Validation'):
    class Validation(AbstractValidation):
        class Meta(AbstractValidation.Meta):
            db_table = 'person_validation'

    __all__.append('Validation')


# 8
if not is_model_registered('person', 'ValidationValue'):
    class ValidationValue(AbstractValidationValue):
        class Meta(AbstractValidationValue.Meta):
            db_table = 'person_validation_value'

    __all__.append('ValidationValue')


# 9
if not is_model_registered('person', 'SecureCode'):
    class SecureCode(AbstractSecureCode):
        class Meta(AbstractSecureCode.Meta):
            db_table = 'person_secure_code'

    __all__.append('SecureCode')
