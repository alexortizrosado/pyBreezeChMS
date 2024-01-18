PyBreezeChMS
=================

Python interface to BreezeChMS REST API.

This is an adaption of [PyBreezeChMS](https://github.com/alexortizrosado/pyBreezeChMS),
the "official" Python implementation of the [Breeze API](https://app.breezechms.com/api).
However, the owner of said repository is apparently no longer with Breeze,
and doesn't respond to email or issues in that repository. This is distributed
as a [PyPI package](https://pypi.org/project/breeze-chms-api/).

Since I've wanted several changes and enhancements, I've cloned that original
and extended it. However, what started as a minor cleanup, mostly with
the goal of making it a pip-installable package, it turned into 
quite a project. While vestiges of the original version remain, it's
a pretty major rewrite. Some things that motivated that:
* Upgrade to Python 3.6 or later; earlier versions are no longer supported.
* Using at least a current (maybe not latest) PEP coding standard.
* A number of method parameter names in the Python implementation differ
from the underlying implementation in the REST description. I found
that confusing, so parameter names in this implementation match the
REST description.
* I found a number of bugs in my testing.
* In my many years of coding, my credo has been "anything worth coding"
is worth coding once," so a great many repetitive instances of
similar code have been consolidated.

Consequentially, I'm calling this a new work, inspired by and including
a few internal pieces of the original.

And a note: I found that the original Python implementation doesn't
implement all the REST APIs. Volunteer management, for example, is
missing. I haven't added them. Maybe in a future release.

## Installation

    $ pip install breeze-chms-api

This will automatically install the required packages.

## Getting Started

The preferred method is to set up configuration files 
for [combine_settings](https://pypi.org/project/combine-settings/)
to specify the two parameters need to access the breeze_api:
* `breeze_url`: Your breeze access url.
* `api_key`: Your organization's API key.

Those settings must be in a file named `breeze_maker.yml`.

With those configuration files set up appropriately, you can instantiate
a `BreezeAPI` simply by:

```python
from breeze_chms_api import breeze

breeze_api = breeze.breeze_api()
```

`breeze.breeze_api()` also passes other keyword parameters through to `config_builder`
if needed. You can also override the default configuration file name with
the `config_name` parameter.

If you don't want to use `config_builder` you can pass `breeze_url` and `breeze_api`
directly to `breeze.breeze_api()`.


To get a JSON of all people:

```python
people = breeze_api.list_people()
```

## Other methods

* `get_account_summary`: Retrieve details of your account.
* `list_people`: Get information about people.
* `get_profile_fields`: Your organization's profile fields.
* `get_field_spec_by_id`: Get profile field specification by id
* `get_field_spec_by_name:` Get profile field specification for named field
* `get_person_details`: Details about a specific person from id.
* `add_person`: Add a person.
* `update_person`: Update a person's information.
* `list_calendars`: Get a list of calendars.
* `list_events`: Get a list of selected events.
* `list_event`: Get information about a specific event.
* `add_event`: Add an event
* `event_check_in`: Check someone in to an event.
* `event_check_out`: Remove someone from an event.
* `delete_attendance`: Delete attendance records for a person from an event.
* `list_eligible_people`: List people eligible for an event.
* `list_attendance`: List attendance for an event.
* `add_contribution`: Add a contribution.
* `edit_contribution`: Edit an existing contribution.
* `delete_contribution`: Delete a contribution.
* `list_form_entries`: Get submitted forms.
* `remove_form_entry`: Remove specified form entry.
* `list_form_fields`: List the fields in a given form.
* `list_contributions`: List selected contributions.
* `list_funds`: List your contribution funds.
* `list_campaigns`: List pledge campaigns.
* `list_pledges`: List pledges in a campaign.
* `get_tags`: Get information about your tags.
* `get_tag_folders`: And your tag folders.
* `assign_tag`: Assign a person to a tag.
* `unassign_tag` and unassign them.

The parameters and returns of all of the above are described in the 
[Breeze API Reference Guide](https://app.breezechms.com/api). Look there,
or the source of this package as necessary.

For deails of this Python implementation see 
[this documentation](https://github.com/dawillcox/pyBreezeChMS/blob/master/DOCUMENTATION.md).

## Test
    pip install coverage combine-settings
    coverage run -m unittest
    coverage report -m

## How do I make a contribution?
Never made an open source contribution before? Wondering how contributions work in the in our project? Here's a quick rundown!

1. Find an issue that you are interested in addressing or a feature that you would like to add.
2. Fork the repository associated with the issue to your local GitHub organization. This means that you will have a copy of the repository under `your-GitHub-username/pyBreezeChMS`.
3. Clone the repository to your local machine using git clone https://github.com/github-username/pyBreezeChMS.git.
4. Create a new branch for your fix using `git checkout -b branch-name-here`.
5. Make the appropriate changes for the issue you are trying to address or the feature that you want to add.
6. Use `git add insert-paths-of-changed-files-here` to add the file contents of the changed files to the "snapshot" git uses to manage the state of the project, also known as the index.
7. Use `git commit -m "Insert a short message of the changes made here"` to store the contents of the index with a descriptive message.
8. Push the changes to the remote repository using `git push origin branch-name-here`.
9. Submit a pull request to the upstream repository.
10. Title the pull request with a short description of the changes made and the issue or bug number associated with your change. For example, you can title an issue like so "Added more log outputting to resolve #4352".
11. In the description of the pull request, explain the changes that you made, any issues you think exist with the pull request you made, and any questions you have for the maintainer. It's OK if your pull request is not perfect (no pull request is), the reviewer will be able to help you fix any problems and improve it!
12. Wait for the pull request to be reviewed by a maintainer.
13. Make changes to the pull request if the reviewing maintainer recommends them.
14. Celebrate your success after your pull request is merged!

## License

Code released under the [Apache 2.0](https://github.com/aortiz32/pyBreezeChMS/blob/master/LICENSE) license.
