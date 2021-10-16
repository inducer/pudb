from pudb.contrib.stringifiers.torch_stringifier import torch_stringifier_fn

CONTRIB_STRINGIFIERS = {
    # User contributed stringifiers
    # Use the contrib prefix for all keys to avoid clashes with the core stringifiers
    # and make known to the user that this is community contributed code
    "contrib.pytorch": torch_stringifier_fn,
}
