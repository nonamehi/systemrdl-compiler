import hashlib
import enum
from .. import rdltypes
from .. import node

def normalize(value, owner_node=None):
    """
    Flatten an RDL value into a unique string that is used for type
    normalization.
    """
    # Determine what type is being flattened
    if type(value) == int:
        return normalize_scalar(value)
    elif type(value) == bool:
        return normalize_boolean(value)
    elif type(value) == str:
        return normalize_string(value)
    elif type(value) == list:
        return normalize_array(value)
    elif isinstance(value, enum.Enum):
        return normalize_enum(value)
    elif isinstance(value, rdltypes.UserStruct):
        return normalize_struct(value)
    elif isinstance(value, node.Node):
        return normalize_component_ref(value, owner_node)
    elif isinstance(value, rdltypes.PropertyReference):
        return normalize_property_ref(value, owner_node)
    elif rdltypes.is_user_enum(value):
        return normalize_user_enum_type(value)
    else:
        # Should never get here
        raise RuntimeError


def normalize_scalar(value):
    """
    5.1.1.4 - c.1:
        Scalar values shall be rendered using their hexadecimal representation.
    """
    return "%x" % value


def normalize_boolean(value):
    """
    5.1.1.4 - c.2:
        Boolean values shall be rendered using either t for true or f for false.
    """
    if value:
        return "t"
    else:
        return "f"


def normalize_string(value):
    """
    5.1.1.4 - c.3:
        String values shall be rendered using the first eight characters of
        their md5 (Message-Digest Algorithm) checksum.
    """
    md5 = hashlib.md5(value.encode('utf-8')).hexdigest()
    return md5[:8]


def normalize_enum(value):
    """
    5.1.1.4 - c.4:
        Enum values shall be rendered using their enumerator literal.
    """
    return value.name


def normalize_array(value):
    """
    5.1.1.4 - c.5:
        Arrays shall be rendered by:
        1. generating the normalized values of its elements,
        2. joining these elements with single underscores (_) into a single
            character sequence, and
        3. using the first eight characters of the md5 checksum of this
            character sequence

        ... which can be semi-formalized as:
            subsequence( md5( join( normalized_values, '_' ), 0, 8 )
    """
    norm_elements = []
    for element in value:
        norm_elements.append(normalize(element))

    norm_str = "_".join(norm_elements)
    md5 = hashlib.md5(norm_str.encode('utf-8')).hexdigest()
    return md5[:8]


def normalize_struct(value):
    """
    5.1.1.4 - c.6:
        Structs shall be rendered by:
        1. generating the normalized value of each member,
        2. joining each member’s name with its normalized value, separated by
            a single underscore (_),
        3. joining the member character sequences with single underscores,
        4. using the first eight characters of the md5 checksum of this
            character sequence

        ... which can be semi-formalized as:
            member_normalization = concat( member_name, '_', normalized_member_value )
            subsequence( md5( join( apply( struct_members, member_normalization ) ), 0, 8)
    """
    norm_elements = []
    for member_name, member_value in value._values.items():
        norm_elements.append("%s_%s" % (member_name, normalize(member_value)))

    norm_str = "_".join(norm_elements)
    md5 = hashlib.md5(norm_str.encode('utf-8')).hexdigest()
    return md5[:8]


def normalize_component_ref(value, owner_node):
    """
    Hash of relative path from owner of the property to the target component
    """
    path = value.get_rel_path(owner_node)
    md5 = hashlib.md5(path.encode('utf-8')).hexdigest()
    return md5[:8]


def normalize_property_ref(value, owner_node):
    """
    Hash of relative path from owner of the property to the target component's
    property
    """
    path = "%s->%s" % (value.node.get_rel_path(owner_node), value.name)
    md5 = hashlib.md5(path.encode('utf-8')).hexdigest()
    return md5[:8]


def normalize_user_enum_type(value):
    """
    Enum type references shall be rendered using their enumeration type name.
    """
    return value.__name__
