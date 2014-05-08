# Taken from https://raw.githubusercontent.com/ozgur/python-linkedin/master/linkedin/utils.py

def make_enum(enum_type='enum', base_classes=None, methods=None, **attrs):
  """
  Generates a enumeration with the given attributes.
  """
  # Enumerations can not be initalized as a new instance
  def __init__(instance, *args, **kwargs):
    raise RuntimeError('%s types can not be initialized.' % enum_type)

  if base_classes is None:
    base_classes = ()

  if methods is None:
    methods = {}

  base_classes = base_classes + (object,)
  for k, v in methods.iteritems():
    methods[k] = classmethod(v)

  attrs['enums'] = attrs.copy()
  methods.update(attrs)
  methods['__init__'] = __init__
  return type(enum_type, base_classes, methods)
