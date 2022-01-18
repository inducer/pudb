# Community contributed extensions for pudb

Here the community can extend pudb with custom stringifiers, themes and shells.


## How to contribute your stringifiers

Simply add a new python module inside `contrib/stringifiers` that contains your custom stringifier.

Then add your stringifier to the `CONTRIB_STRINGIFIERS` dict inside
`contrib/stringifiers/__init__.py`.

The new options should appear in the pudb settings pane after setting the `Enable community contributed content` option.
