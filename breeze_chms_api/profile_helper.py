from abc import abstractmethod
from typing import Union, List, Type, Mapping, Dict, Tuple
from collections import OrderedDict


def _extract_name(profile: dict) -> str:
    """
    Get a name from a profile.
    :param profile: Dict with name info. Note, this can be either the
                    main section of a profile, or the "details" part of
                    a "family" entry
    :return: String with name in an established form.
    """
    full_name = profile.get('last_name', '')
    first = profile.get('first_name', '')
    middle = profile.get('middle_name', '')
    nick = profile.get('nick_name', '')
    if nick and nick != first:
        first += f' ({nick})'
    if middle:
        first += f' {middle}'
    if first:
        full_name += f', {first}'
    return full_name


def _delist(val: Union[List[str], None]) -> Union[List[str], str, None]:
    """
    Turn a list of only one element into just that element
    :param val: List of strings
    :return: None if empty string, single entry if only one, else List
    """
    if not val:
        return None
    else:
        return val[0] if len(val) == 1 else val


class _BaseExtractor:
    def __init__(self, name: str, field_id: str):
        """
        Construct extractor
        :param name: Name of profile field
        :param field_id:  id (for extracting from a profile)
        """
        self.field_id = field_id
        self.field_name = name

    @property
    def name(self):
        return self.field_name

    @abstractmethod
    def get_value(self, profile: dict) -> Union[List[str], str, None]:
        pass

class _Extractor(_BaseExtractor):
    """Simple case, value extractor"""
    def __init__(self, name: str, field_id: str):
        _BaseExtractor.__init__(self, name, field_id)

    def get_value(self, profile: dict) -> Union[List[str], None]:
        """
        Return value for single value profile fields.
        :param profile: A user's profile
        :return: A single value list with the value, or None if no value
        """
        details = profile.get('details')
        return _delist(self._value_from_details(details))
        # return self._value_from_details(details) if details else None

    def _value_from_details(self, details: dict) -> Union[List[str], None]:
        value = details.get(self.field_id)
        return self._process_field_value(value) if value else None

    @abstractmethod
    def _process_field_value(self, value: Union[dict, List, str]) -> \
            Union[List[str], None]:
        pass

class _NameExtractor(_BaseExtractor):
    def __init__(self):
        _BaseExtractor.__init__(self, 'Name', 'name')

    def get_value(self, profile: dict) -> Union[List[str], str, None]:
        # return [_extract_name(profile)]
        return _extract_name(profile)

class _SimpleExtractor(_Extractor):
    """
    The profile is just a single value, eg:
            "2114298802": "Wilder",
    """

    def _process_field_value(self, value: Union[dict, List, str]) -> \
            Union[List[str], None]:
        return [value]

class _SingleValueExtractor(_Extractor):
    """
    The field can have exactly one value from a selection of possibilities, e.g.:
        "2114298948": {
          "value": "211",
          "name": "Include (Default for adults)"
        }
        "value" is an internal key for which value out of the universe of
        possibilities. "name" is the human-visible version.
    """

    def _process_field_value(self, values: Union[dict, List, str]) ->\
            Union[List[str], None]:
        value = values.get('name')
        return [value] if value else None

class _MultiValueExtractor(_Extractor):
    """
    The field can have many values selected from a set. e.g.:
        "2114298810": [
          {
            "name": null,
            "value": "null"
          },
          {
            "name": "Coffee Host",
            "value": "78"
          },
          {
            "name": "Worship",
            "value": "145"
          }
        ]
        Note that there always seems to be one empty entry.
    """

    def _process_field_value(self, values: List[dict]) -> Union[List[str], None]:
        """
        Profile value is a list of entries, each with "name" as interesting key.
        :param values:
        :return:
        """
        return_list = []
        for entry in values:
            return_list += self._extract_entry(entry)

        # if not return_list:
        #     return None
        # return return_list if len(return_list) > 1 else return_list[0]
        return return_list if return_list else None

    def _extract_entry(self, entry: dict) -> List[str]:
        value = entry.get('name')
        return [value] if value else []

class _EmailExtractor(_MultiValueExtractor):
    def _extract_entry(self, entry: dict) -> List[str]:
        email = entry.get('address')
        if not email:
            return []

        if entry.get('is_private', '') == '1':
            email += '(private)'
        fname = entry.get('field_type')[6:] # Strip off 'email_'
        if fname != 'primary':
            # Note, while the data structure allows for field_type values of other
            # than email_primary, there's currently no way t set that in Breeze
            # like there is for phone numbes.:q!
            email = f'{fname}:{email}'
        return [email]

class _PhoneExtractor(_MultiValueExtractor):
    """
    Handle a phone field (can have multiple values)
    """
    def _extract_entry(self, entry: dict) -> List[str]:
        phone = entry.get('phone_number')
        pt = entry.get('phone_type')
        if pt and phone:
            if entry.get('is_private', '') == '1':
                phone += '(private)'
            if entry.get('do_not_text', '') == '1':
                phone += '(no text)'
            if pt != 'primary':
                phone = f'{pt}:{phone}'
            return [phone]
        else:
            return []

class _FamilyExtractor(_MultiValueExtractor):
    def __init__(self):
        _MultiValueExtractor.__init__(self, "family", "family")

    def get_value(self, profile: dict) -> Union[List[str], None]:
        """
        Return value for single value profile fields. (Override because
        family isn't in 'details'
        :param profile: A user's profile
        :return: A single value list with the value, or None if no value
        """
        return _delist(self._value_from_details(profile))
        # return self._value_from_details(profile)

    def _extract_entry(self, entry: dict) -> List[str]:
        name = _extract_name(entry.get('details'))
        role = entry.get('role_name')
        if role:
            name += f' ({role})'
        return [name]


class _AddressExtractor(_MultiValueExtractor):
    """
    Handle an address entry. Note: The data model allows multiple addresses,
    but Breeze currently only supports one. This should still work if they
    start supporting extra addresses.
    """
    def _extract_entry(self, entry: dict) -> List[str]:
        if not entry:
            return []
        csz = [entry.get('city'), entry.get('state'), entry.get('zip')]
        csz = ' '.join([f for f in csz if f])
        fields = []
        # Note: It isn't clear that there's ever a _2.
        for part in [entry.get('street_address'), entry.get('street_address_2')]:
            if part:
                fields += part.split('<br />')
        fields += [csz]
        return [';'.join(v for v in fields if v)]


_extractors: Mapping[str, Type[_BaseExtractor]] = {
    'grade': _SimpleExtractor,
    'single_line': _SimpleExtractor,
    'multiple_choice': _SingleValueExtractor,
    'birthdate': _SimpleExtractor,
    'date': _SimpleExtractor,
    'notes': _SimpleExtractor,
    'dropdown': _SingleValueExtractor,
    'checkbox': _MultiValueExtractor,
    'email': _EmailExtractor,
    'phone': _PhoneExtractor,
    'address': _AddressExtractor,
}

class ProfileHelper:
    def __init__(self, profile_fields):
        """
        Create a ProfileHelper.
        :param profile_fields: Profile fields as returned by
                               BreezeAPI.get_profile_fields()
        """
        self.id_to_field = {
            'name': _NameExtractor(),
        }

        for section in profile_fields:
            section_name = section.get('name')
            for field_def in section.get('fields'):
                field_type = field_def.get('field_type')
                extractor = _extractors.get(field_type)
                if extractor:

                    field_id = field_def.get('field_id')
                    field_name = f"{section_name}:{field_def.get('name')}"
                    self.id_to_field[field_id] = extractor(field_name, field_id)
        self.id_to_field['family'] = _FamilyExtractor()
        self.id_to_name = {field_id: e.name for field_id, e in self.id_to_field.items()}

    def process_member_profile(self, profile: dict) -> \
            Dict[str, Union[str, List[str]]]:
        """
        Extract values from a member's profile, return map from field id field value.
        Only include fields that actually have a value. Each field value can be
        a simple string or a list of strings.
        :param profile: A profile
        :return: map from field id to single field value or list of values
        Notes: The name of the field can be determined by the field_to_name map.
               The person's name is in the 'name' element in the returned dict.
        """
        result = {'name': _extract_name(profile)}
        for field_id, extractor in self.id_to_field.items():
            value = extractor.get_value(profile)
            if value:
                result[field_id] = value
        return result

    def process_profiles(self, profile_list: List[dict]) -> \
            Dict[str, Dict[str, Union[str, List[str]]]]:
        """
        Return all nonempty values from a list of profiles
        :param profile_list: The profiles from a
                         BreezeAPI.get_people(details=True) call
        :return: dict from unique member id to the value returned by
                 self.process_member_profile() for each profile.
        """
        return {profile.get('id'): self.process_member_profile(profile)
                for profile in profile_list}

    def get_field_id_to_name(self) -> Dict[str, str]:
        """
        Return map from field id to qualified field name, which includes
        the section name and field name.
        """
        return self.id_to_name.copy()

def _pop_next(dct: OrderedDict) -> Tuple[object, object]:
    """
    Do a popitem(last=False) on an OrderedDict, but catch
    IndexError and return None, None instead
    :param dct: OrderedDict
    :return: Key and value from first item in the OrderedDict, or None, None if empty
    """
    try:
        return dct.popitem(last=False)
    except KeyError:
        return None, None

def join_dicts(values_right: Dict[str, Union[str, List[str], dict]],
               values_left: Dict[str, Union[str, List[str], dict]]) ->  \
        Dict[str, Tuple[Union[str, List[str], dict, None],
                        Union[str, List[str], dict, None]]]:
    """
    Join two dicts.
    :param values_right: First dict
    :param values_left: Second dict
    :return: A dict of tuples. Each key is from either of the two inputs, preferably
             in the order of values_left. Each value is a tuple with the values from
             values_right and values_left for the given key. Only keys that had
             a non-None value in at least one of the two inputs are in the output.
    """

    dat_left = OrderedDict(values_left if values_left else {})
    dat_right = OrderedDict(values_right if values_right else {})
    key_left, val_left = _pop_next(dat_left)
    key_right, val_right = _pop_next(dat_right)
    result = {}

    while key_left or key_right:
        if key_left == key_right:
            # key exists in both, in order
            result[key_right] = (val_right, val_left)
            key_left, val_left = _pop_next(dat_left)
            key_right, val_right = _pop_next(dat_right)
        elif key_left in dat_right:
            # Current value is later in reference in so pull it out and emit the pair
            result[key_left] = (dat_right.pop(key_left), val_left)
            key_left, val_left = _pop_next(dat_left)
        elif key_right in dat_left:
            # Reference value appears later in current, so move it to the end
            # catch it later
            dat_right[key_right] = val_right
            key_right, val_right = _pop_next(dat_right)
            # But since we know current isn't in reference, also emit it
            result[key_left] = (None, val_left)
            key_left, val_left = _pop_next(dat_left)
        else:
            # At this point, we know neither value is in the other, so
            # just emit them both.
            if key_right:
                result[key_right] = (val_right, None)
                key_right, val_right = _pop_next(dat_right)
            if key_left:
                result[key_left] = (None, val_left)
                key_left, val_left = _pop_next(dat_left)

    return result

def profile_compare(diffs: Dict[str, Dict[str, Dict[str, Tuple[List, List]]]],
                    field_map: Dict[str, str] = None) \
        -> List[Tuple[str, List[Tuple[str, List[str], List[str]]]]]:
    """
    Generate a report of changed field values between two versions of profiles.
    :param diffs: The result of running join_dicts() on the output of
                  ProfileHelper.process_profiles() on two different versions of a site's
                  profile database. The key in diffs is the person's unique ID.
                  Each value is two dicts, each a map from field ID to the reference
                  and current values for that field.
    :param field_map: A map from field_id to field name. (If missing, just field
                      ids will be returned.)
    :return: List of tuples, where items are the profile name and a list of field diffs
             Each element in the list of diffs is a tuple with field name, values
             in the reference not in current, and values in current not in reference.
             All values are strings.
             Only fields and profiles with differences are in the output.
    """
    field_map = field_map if field_map else {}
    result = []
    for person_id, fields in diffs.items():
        fields_r, fields_c = fields
        merged = join_dicts(fields_r, fields_c)
        person_result = []
        for field_id, vals in merged.items():
            val_r, val_c = vals
            # print(f'{field_id} {val_r} {val_c}')
            if val_r != val_c:
                set_r = set(val_r if isinstance(val_r, list) else [val_r]) \
                    if val_r else set()
                set_c = set(val_c if isinstance(val_c, list) else [val_c]) \
                    if val_c else set()
                if set_r != set_c:
                    field_name = field_map.get(field_id, field_id)
                    person_result.append((field_name,
                                          list(set_r - set_c),
                                          list(set_c - set_r)))
        if person_result:
            person_name = (fields_r if fields_r else fields_c).get('name')
            result.append((person_name, person_result))
    return result


def compare_profiles(prev_helper: ProfileHelper,
                     cur_helper: ProfileHelper,
                     prev_people: List[dict],
                     cur_people: List[dict]) -> \
        List[Tuple[str, List[Tuple[str, str, str]]]]:
    """
    Create a report of differences between two instances of a Breeze account.
    (Typically one saved at an earlier date, one current.)
    :param prev_helper: A ProfileHelper instance for the reference profiles
    :param cur_helper: A ProfileHelper instance for the current profiles
    :param prev_people: Profile entries for the reference version
    as returned by BreezeAPI.list_people()
    :param cur_people: A list of profile entries for the current version, same format.
    :return: A list of profiles that had changed values. Each element is a tuple
    with the profile name and a list of changed fields. Each entry in the
    fields list has the field name, a list of values from the previous
    people but not current, and a list of values in the current people but
    not previous.
    """
    field_names = prev_helper.get_field_id_to_name()
    field_names.update(cur_helper.get_field_id_to_name())
    cur_values = cur_helper.process_profiles(cur_people)
    ref_values = prev_helper.process_profiles(prev_people)
    merged_values = join_dicts(ref_values, cur_values)

    return profile_compare(merged_values, field_names)

if __name__ == '__main__':
    pass