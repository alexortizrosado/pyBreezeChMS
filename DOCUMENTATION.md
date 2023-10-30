# BREEZE_CHMS_API INTERFACE DETAILS
The module [README](./README.md) has a high-level description of the
`breeze_chms_api` module. Details of the various calls are found here.

## Instantiation
While one _could_ instantiate the `BreezeAPI` class directly, the
preferred mechanism is to use the `breeze_api()` call. 

```python
def breeze_api(breeze_url: str = None,
               api_key: str = None,
               dry_run: bool = False,
               connection: requests.Session = requests.Session(),
               config_name: str = 'breeze_maker.yml',
               **kwargs,
               ) -> BreezeApi:
    """
    Create an instance of a Breeze api object. Parameters needed to configure the api
    can be passed explicitly or loaded from a file using load_config().
    :param breeze_url: Explicitly given url for the Breeze API. (load_config() key 'breeze_url')
    :param api_key: Explicitly given API key for the Breeze API. (load_config() key 'api_key')
    :param dry_run: Just for testing, causes breeze_api to skip all net interactions.
    :param connection: Session if other than default (mostly for testing)
    :param config_name: Alternate load_config() file name.
    :param kwargs: Other parameters used by load_config()
    :return: A BreezeAPI instance
    """
```
Two things are required by `breeze_api()`: The url to connect to your Breeze
instance, and the API key that verifies to Breeze that you are authorized
to connect. While you _can_ pass those explicitly to `breeze_api()`, that
means every application you might use needs to have those values, and
you need to do that in a way that doesn't expose them to potential bad
actors.

The preferred method is to let `breeze_api()` use `load_config()` from the 
[combine_settings](https://pypi.org/project/combine-settings/) module to
load those values from a `breeze_maker.yml` configuration file. (You can
override that file name with the `config_name` parameter.) See the
`combine_settings` module description for where the file should be
placed, but you want it in a place and with permissions so that only
those authorized to use the Breeze API can read it.

## API Calls
`BreezeAPI` is a Python wrapper for the [Breeze API](https://app.breezechms.com/api)
https API. Details of the calls are given there; no attempt is given
here to describe the meaning of the API parameters or the values
returned by each call. Refer to the `Beeze API` description for that.
The following detail the Python interfaces to make those calls.

#### Account Information
```Python
def get_account_summary(self) -> dict:
    """Retrieve the details for a specific account using the API key 
      and URL. It can also work to see if the key and URL are valid.
     :return: JSON object
    """
```
#### People
##### Get Profile Fields
```Python
def get_profile_fields(self) -> List[dict]:
    """List profile fields from your database.
    To be clear, this is a list of profile sections, each section
    having a list of field specifications in that section.
    Each field specification has a new 'section_spec' item
    that refers back to the containing section, which
    can give the setion name among other things
    :return: List of descriptors of profile fields
    """
```
##### Get Profile Field Specification by ID
```Python
def get_field_spec_by_id(self, field_id: str) -> dict:
    """
    Return profile spec for given field id
    :param field_id: Field id
    :return: Field specification
    """
```
##### List People
```Python
def list_people(self, **kwargs) -> List[dict]:
    """
    List people from your database
    :param kwargs: Keyed parameters, all optional:
        limit: If set, number of people to return, If none, will return all people
        offset: Number of people to skip before beginning to return results.
        details: Boolean, if True, return all information, Otherwise just names.
        filter_json: Filter results based on criteria (tags, status, etc.)
                Refer to the list_profile_field response to show values you're
                searching for. Or see the API document for a slightly better
                explanation.
    :return: List of dicts for profiles.
    """
```
This returns all (or a selected subset) of people in your database, with
basic or extended details for each.
##### Get details about a person
```Python
def get_person_details(self, person_id: Union[str, int]) -> dict:
    """
    Retrieve the details for a specific person by their ID.
    :param person_id: Unique id for a person in Breeze database.
    :return: JSON response.
    """
```
##### Add a person
```Python
def add_person(self, **kwargs) -> str:
    """
    Add a new person to the database
    :param kwargs: Keyed parameters:
        first: The first name of the person.
        last: The last name of the person.
        fields_json: JSON string representing an array of fields to update.
                   Each array element must contain field id, field type, response,
                   and in some cases, more information.
                   Obtain such field information from get_profile_fields() or
                   use get_person_details() to see fields that already exist for a specific person.
    :return: JSON response equivalent to get_person_details(). Includes
             the ID of the added person.
    """
```
Note that here, and everywhere following where a parameter
ending in `_json` appears,
the parameter can be a JSON-encoded string, a single Python `dict`, or
a list of `dicts`. The latter two will be automatically converted
for transmission.
##### Update person
```Python
def update_person(self, **kwargs) -> dict:
    """
    Updates the details for a specific person in the database.
    :param kwargs:
      person_id: Unique id for a person in Breeze database.
      fields_json: JSON list of fields to update, similar to add_person().
    :returns: JSON response equivalent to get_person_details(person_id).
    """
```
#### Calendars and Events
##### List calenders
```Python
def list_calendars(self) -> List[dict]:
    """
    Return a list of calendars
    :return: List of descriptions of available calenders
        """
```
##### List Events
```Python
def list_events(self, **kwargs) -> List[dict]:
    """
    Retrieve all events for a given date range.

    :param kwargs: Keyed parameters
      start: Start date; defaults to first day of the current month.
      end: End date; defaults to last day of the current month
    :return: JSON response
"""
```
Dates are in the form YYYY-MM-DD, all numeric.
##### List Event
```Python
def list_event(self, instance_id: Union[str, int]) -> dict:
    """
    Return information about a specific event
    :param instance_id: ID of the event
    :return: json object with event data
    """
```
##### Add Event
```Python
def add_event(self, **kwargs) -> str:
    """
    Add event for given date rage

    :param kwargs: Keyed parameters
      name: Name of event
      starts_on: Start datetimestamp (epoch time)
      ends_on: End datetimestamp (epoch time)
      all_day: boolean
      description: description of event (default none)
      category id: which calendar your event is on (defaults to primary)
      event id: series id
    :return: JSON response
    """
```
##### Check a person in to an event
```Python
def event_check_in(self, person_id, instance_id):
    """
    Checks a person in to an event.
    :param person_id: ID for person in Breeze database
    :param instance_id: ID for event to check in to
    :return: Request response
    """
```
##### Check a person out from an event
```Python
def event_check_out(self, person_id, instance_id):
    """
    Remove the attendance for a person checked into an event.
    :param person_id: Breeze ID for a person in Breeze database.
    :param instance_id: Breeze ID for a person in Breeze database.
    :return: True if check-out succeeds; False if check-out fails.
    """
```
Note: `event_check_out()` differs from `delete_attendance()` in that
it adds a check-out record. (It also adds a check-in if the person
isn't already checked in.) `delete_attendance()` removes all attendance
records for the person.
##### Delete Attendance
```Python
def delete_attendance(self, person_id, instance_id):
    """
    Delete all attendance records for a person from an event
    :param person_id: Id of person to remove
    :param instance_id: Event instance ID
    :return: True if delete succeeds
    """
```
##### List Attendance
```Python
def list_attendance(self, instance_id: Union[str, int], details: bool = False):
    """
    List attendance for an event
    :param instance_id: ID of the event
    :param details: If true, give details
    :return: List of people who attended this event
    """
```
##### List Eligible People
```Python
def list_eligible_people(self, instance_id: Union[int, str]):
    """
    List people eligible for an event
    :param instance_id: ID of the event
    :return: List of eligible people
    """
```
#### Contributions
None of the contributions apis are documented in the generic Breeze API
document, but they're implemented in the original Python implementation.
This implementation was derived from the original Python version, but
documentation is sparse.
##### Add a contribution
```Python
def add_contribution(self, **kwargs) -> str:
    """
    Add a contribution to Breeze.
    :param kwargs: Keyed arguments as follows:
      date: Date of transaction in DD-MM-YYYY format (ie. 24-5-2015)
                 Note: This format is backwards from how Breeze generally does dates.
      name: Name of the person that made the transaction. Used to help match up
            contribution to correct profile within Breeze.
      person_id: The Breeze ID of the donor. If unknown, use UID instead of
                 person id  (ie. 1234567)
      uid: The unique id of the person sent from the giving platform. This
           should be used when the Breeze ID is unknown. Within Breeze a
           user will be able to associate this ID with a given Breeze ID.
           (ie. 9876543)
      email: Email address of the donor. If no person_id is provided, used
             to help automatically match the person to the correct profile.
      street_address: Donor's street address. If person_id is not provided,
                      street_address will be used to help automatically
                      match the person to the correct profile.
      processor: The name of the processor used to send the payment. Used
                 in conjunction with uid. Not needed if using Breeze ID.
                 (ie. SimpleGive, BluePay, Stripe)
      method: The payment method. (ie. Check, Cash, Credit/Debit Online,
              Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
              Direct Deposit)
      funds_json: JSON object containing fund names and amounts. This
                  allows splitting fund giving. The ID is optional. If
                  present, it must match an existing fund ID and it will
                  override the fund name. In other words,
                  eg.. [ {
                          'id':'12345',
                          'name':'General Fund',
                          'amount':'100.00'
                        },
                        {
                          'name':'Missions Fund',
                          'amount':'150.00'
                        }
                      ]
      amount: Total amount given. Must match sum of amount in funds_json.
      group: This will create a new batch and enter all contributions with
             the same group into the new batch. Previous groups will be
             remembered and so they should be unique for every new batch.
             Use this if wanting to import into the next batch number in a
             series.
      batch_number: The batch number to import contributions into. Use
                    group instead if you want to import into the next batch
                    number.
      batch_name: The name of the batch. Can be used with batch number or
                  group.
      note: An optional note for the transaction
    :return: Payment id
    :raises: BreezeError on failure to add contribution
    """
```
##### Edit a contribution
```Python
def edit_contribution(self, **kwargs) -> str:
    """
    Edit an existing contribution
    :param kwargs: Keyed parameters
      payment_id: The ID of the payment that should be modified.
      date: Date of transaction in DD-MM-YYYY format (ie. 24-5-2015)
      name: Name of person that made the transaction. Used to help match up
            contribution to correct profile within Breeze.  (ie. John Doe)
      person_id: The Breeze ID of the donor. If unknown, use UID instead of
                 person id  (ie. 1234567)
      uid: The unique id of the person sent from the giving platform. This
           should be used when the Breeze ID is unknown. Within Breeze a
           user will be able to associate this ID with a given Breeze ID.
           (ie. 9876543)
      email: Email address of donor. If no person_id is provided, used to
             help automatically match the person to the correct profile.
             (ie. sample@breezechms.com)
      street_address: Donor's street address. If person_id is not provided,
                      street_address will be used to help automatically
                      match the person to the correct profile.
                      (ie. 123 Sample St)
      processor: The name of the processor used to send the payment. Used
                 in conjunction with uid. Not needed if using Breeze ID.
                 (ie. SimpleGive, BluePay, Stripe)
      method: The payment method. (ie. Check, Cash, Credit/Debit Online,
              Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
              Direct Deposit)
      funds_json: JSON string containing fund names and amounts. This
                  allows splitting fund giving. The ID is optional. If
                  present, it must match an existing fund ID and it will
                  override the fund name.
                  ie. [ {
                          'id':'12345',
                          'name':'General Fund',
                          'amount':'100.00'
                        },
                        {
                          'name':'Missions Fund',
                          'amount':'150.00'
                        }
                      ]
      amount: Total amount given. Must match sum of amount in funds_json.
      group: This will create a new batch and enter all contributions with
             the same group into the new batch. Previous groups will be
             remembered and so they should be unique for every new batch.
             Use this if wanting to import into the next batch number in a
             series.
      batch_number: The batch number to import contributions into. Use
                    group instead if you want to import into the next batch
                    number.
      batch_name: The name of the batch. Can be used with batch number or
                  group.
    :returns: Payment iD
    :raises: BreezeError on failure to edit contribution.
    """
```
Note: Since the behavior of this isn't explicitly documented, the author
can only guarantee that the parameters listed here are delivered to Breeze.
There are no guarantees how Breeze handles various cases.
##### Delete Contribution
```Python
def delete_contribution(self, payment_id):
    """
    Delete an existing contribution.
    :param payment_id: The ID of the payment to be deleted
    :return: Payment id
    :raises: BreezeError on failure to delete a contribution.
    """
```
##### List Contributions
```Python
 def list_contributions(self, **kwargs) -> List[Mapping]:
    """
    Retrieve a list of contributions.
    :param kwargs: Set of keyed arguments
      start: Find contributions given on or after a specific date
                  (ie. 2015-1-1); required.
      end: Find contributions given on or before a specific date
                (ie. 2018-1-31); required.
      person_id: ID of person's contributions to fetch. (ie. 9023482)
      include_family: Include family members of person_id (must provide
                      person_id); default: False.
      amount_min: Contribution amounts equal or greater than.
      amount_max: Contribution amounts equal or less than.
      method_ids: List of method IDs.
      fund_ids: List of fund IDs.
      envelope_number: Envelope number.
      batches: List of Batch numbers.
      forms: List of form IDs.
    :return: List of matching contributions as dicts
    :raises: BreezeError on malformed request
    :raises: BreezeBadParameter on missing start or end
    """
```
##### List Funds
```Python
def list_funds(self, include_totals: bool = False) -> List[dict]:
    """
    List all funds
    :param include_totals: If True include total given for each fund
    :return: List of fund descriptions
    """
```
##### List Campaigns
```Python
def list_campaigns(self) -> List[dict]:
    """
    List pledge campaigns
    :return:  List of campaigns
    """
```
##### List Pledges
```Python
def list_pledges(self, campaign_id) -> List[dict]:
    """
    List of pledges within a campaign
    :param campaign_id: ID number of a campaign
    :return: List of pledges
    """
```
#### Forms
##### List Form Entries
```Python
def list_form_entries(self, form_id, details=False):
    """
    Return entries for a given form
    :param form_id: The ID of the form
    :param details: If True, return all information (slower) else just names
    :return: List of form entries, for example:
      [
       {
        "id":"11",
        "form_id":"15326",
        "created_on":"2021-03-09 13:04:02",
        "person_id":null,
        "response":{
            "45":{
            "id":"13",
            "oid":"1512",
            "first_name":"Zoe",
            "last_name":"Washburne",
            "created_on":"2021-03-09 13:04:03"
            },
            "46":"zwashburne@test.com",
            "47":"Red"
        }
       },
      ]
      """
```
#### Tags
#### Get Tags
```Python
def get_tags(self, folder_id=None):
    """
    Get list of tags
    :param folder_id: If set, only include tags in this folder id
    :return: List of tags, for example:
        [
          {
            "id":"523928",
            "name":"4th & 5th",
            "created_on":"2018-09-10 09:19:40",
            "folder_id":"1539"
          },
          {
            "id":"51994",
            "name":"6th Grade",
            "created_on":"2018-02-06 06:40:40",
            "folder_id":"1539"
          },
        ]
    """
```
##### Get Tag Folders
```Python
def get_tag_folders(self) -> List[dict]:
    """
    Get list of tag folders
    :return: List of tag folders, for example:
       [
         {
             "id":"1234567",
             "parent_id":"0",
             "name":"All Tags",
             "created_on":"2018-06-05 18:12:34"
         },
         {
             "id":"8234253",
             "parent_id":"120425",
             "name":"Kids",
             "created_on":"2018-06-05 18:12:10"
         },
         {
             "id":"1537253",
             "parent_id":"5923042",
             "name":"Small Groups",
             "created_on":"2018-09-10 09:19:40"
         },
         {
             "id":"20033",
             "parent_id":"20031",
             "name":"Student Ministries",
             "created_on":"2018-12-15 18:11:31"
         }
      ]
    """
```
##### Assign Tag To a Person
```Python
def assign_tag(self,
               person_id: str,
               tag_id: str) -> bool:
    """
    Assign a tag to a person
    :param person_id: The person to get the tag
    :param tag_id: ID of tag to assign
    :return: True if success
    """
```
##### Unassign Tag From a Person
```Python
def unassign_tag(self, person_id: str,
                 tag_id: str) -> bool:
    """
    Unassign a tag from a person
    :param person_id: Person to lose the tag
    :param tag_id: ID of tag to lose
    :return: True if success
    """
```

## Profile Helper
Version 1.2.0 adds `profile_helper` which makes it easier
to deal with member profiles from Breeze. `profile_helper` defines
the `ProfileHelper` class that can convert raw profiles
from Breeze into maps of profile field values.
## `ProfileHelper`
`ProfileHelper` is a class that makes it easy to extract fields from
members' profiles.
```Python
class ProfileHelper:
    def __init__(self, profile_fields):
        """
        Create a ProfileHelper.
        :param profile_fields: Profile fields as returned by
                               BreezeAPI.get_profile_fields()
        """
```
You can create a `ProfileHelper` roughly like this:
```Python
# Instantiate a breeze API
api = breeze.breeze_api()
# Get profile fields
profile_fields = api.get_profile_fields()
# Create a ProfileHelper
helper = profile_helper.ProfileHelper(profile_fields)
```
The returned helper knows how to extract the various forms
of profile field from profiles from your Breeze instance.

`ProfileHelper` has several useful methods.
### `Field ID to Field Name Map`
```Python
    def get_field_id_to_name(self) -> Dict[str, str]:
        """
        Return map from field id to qualified field name, which includes
        the section name and field name.
        """
```
This returns a map from your site's unique field ids to the fields'
names. These are "fully qualified" names including section (aka "paragraph")
name, so field "Address" in section "Communication" would have
name "Communication:Address".
### `Process Member Profile`
```Python
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
```
This returns a report of field values
from a single Breeze member's profile. An illustrative but not necessarily
useful example is:
```Python
person = api.list_people(details=True, limit=1, offset=x)
# Note that list_people always returns a list,
# even if only getting one profile
fields = helper.process_member_profile(person[0])
```
This call returns a map from unique field id to the value
in the field. Only fields with values are included. The value
of the field is a string if that's appropriate. If there are multiple
values (for example a checkbox field with multiple boxes
checked)
or multiple phone numbers, the value is a list of values.

As a special case, 'name' is the key for the member's name.

Some field strings are constructed from multiple bits of information
in the profile itself. For example:
* a phone number might be returned as '800-555-1212(private)(no_text)'
* 'name' is constructed from first, middle, nick, and last names
* the multiple 'family' values are constructed from the name and role of each family member.
### `Process Profiles`
```Python
    def process_profiles(self, profile_list: List[dict]) -> \
            Dict[str, Dict[str, Union[str, List[str]]]]:
        """
        Return all nonempty values from a list of profiles
        :param profile_list: The profiles from a
                         BreezeAPI.get_people(details=True) call
        :return: dict from unique member id to the value returned by
                 self.process_member_profile() for each profile.
        """
```
As a convenience you can use `process_profiles()` to process
people data from Breeze. It returns a map from unique member id
to the value returned by `process_single_profile()` for
that member.

So you might do something like this:
```Python
people = api.list_people(details=True)
profiles = helper.process_profiles(people)
for pid, person in profiles.items():
    handle_this_person(pid, person)
```

## Profile Helper Utility Methods
`profile_helper` has a couple of utility functions that may
not seem useful to you, but will be used in a future suite of
 report generators.
### Join Two Dictionaries
```Python
    """
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
```
This joins two different dicts.
It returns a dict with all of the keys that had a non-None
value in either dict. The value for each key is a tuple with
the values from the two input dicts. Here's an example:
```Python
    r = {'a': 'ra', 'b': 'rb'}
    l = {'b': 'lb', 'c': 'lc'}
    rl = profile_helper.join_dicts(r, l)
    # Results in
    # {'a': ('ra', None), 'b': ('rb, 'lb'), 'c': (None, 'lc)}
```
The preferred order of keys (should you care) will be as much
as possible as in the second dict.

### Compare Profile Versions
```Python
def profile_compare(diffs: Dict[str, Dict[str, Dict[str, Tuple[List, List]]]],
                    field_map: Dict[str, str] = None) \
        -> List[Tuple[str, List[Tuple[str, str, str]]]]:
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
```
This compares two versions
of your member database and tells you what changed between them.
This presumes that you have a mechanism to save the profile information
from one run to use in a compare at a later date.
Here's the basic idea:
```Python
    # Get field map and values saved during previous run
    # whoever you implement this.
    prev_field_map, prev_profiles = load_from_previous()
    
    # Get field map and values from now
    cur_helper = profile_helper.ProfileHelper(api.get_profile_fields())
    cur_profiles = cur_helper.process_profile(api.get_people())
    
    # Get a map of all field ids to name for ids in
    # either previous or current system
    cur_field_map = cur_helper.field_id_to_name()
    field_id_to_name = prev_field_map.copy()
    field_id_to_name.update(cur_field_map)
    
    # Join the two sets of profiles together based on member id.
    joined_values = profile_helper.join_dicts(prev_profiles, cur_profiles)
    
    # Now, do the compare
    updates = profile_helper.profile_compare(joined_values, field_id_to_name)

    # Finally, save current values for later, however you do it.
    save_for_future_use(cur_field_map, cur_profiles)
    
```
The `updates` result is a list of tuples, one for each person that
had at least one change in their profile. The first value in each
tuple is the member's name. The second is another list of tuples.
Each entry in that list has three values:
* The name of the field with a changed value.
* A list of values that were in the previous profile but not the new.
* A list of values in the new profile but not the previous.

### Compare Profile Versions (Alternate Method)
If you're willing to save the entire field definition and
profile data between sessions instead of the much reduced
information used by `profile_compare()`, there's
a slightly simpler alternative.
```Python
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
    :return: See profile_compare()
    """
```
The result is the same as `profile_compare()`, but its 
use would be something like this:
```Python
# Get previous saved data
prev_field_def, prev_profiles = load_previous_data()

# Get current data
current_field_def = api.api.get_profile_fields()
current_profiles = api.get_people()

prev_helper = profile_helper.ProfileHelper(prev_field_def)
cur_helper = profile_helper.ProfileHelper(current_field_def)

# get differences
updates = profile_helper.profile_compare(
                profile_helper.ProfileHelper(prev_field_def),
                profile_helper.ProfileHelper(current_field_def),
                prev_profiles,
                current_profiles)

# Save for next run
save_current_data(current_field_def, current_profiles)
)
```
