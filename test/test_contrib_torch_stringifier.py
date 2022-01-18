try:
    import torch
    HAVE_TORCH = True
except ImportError:
    HAVE_TORCH = False

from pudb.var_view import default_stringifier
from pudb.contrib.stringifiers.torch_stringifier import torch_stringifier_fn

def test_tensor():
    if HAVE_TORCH:
        x = torch.randn(10, 5, 4)
        assert torch_stringifier_fn(x) == "Tensor[float32][cpu] [10, 5, 4]"


def test_conv_module():
    if HAVE_TORCH:
        x = torch.nn.Conv2d(20, 10, 3)
        assert torch_stringifier_fn(x) == "Conv2d(20, 10, kernel_size=(3, 3), stride=(1, 1))[cpu] Params: 1810"


def test_linear_module():
    if HAVE_TORCH:
        x = torch.nn.Linear(5, 2, bias=False)
        assert torch_stringifier_fn(x) == "Linear(in_features=5, out_features=2, bias=False)[cpu] Params: 10"


def test_long_module_repr_should_revert_to_type():
    if HAVE_TORCH:
        x = torch.nn.Transformer()
        assert torch_stringifier_fn(x) == "Transformer[cpu] Params: 44140544"


def test_reverts_to_default_for_str():
    x = "Everyone has his day, and some days last longer than others."
    assert torch_stringifier_fn(x) == default_stringifier(x)


def test_reverts_to_default_for_dict():
    x = {"a": 1, "b": 2, "c": 3}
    assert torch_stringifier_fn(x) == default_stringifier(x)


def test_reverts_to_default_for_list():
    x = list(range(1000))
    assert torch_stringifier_fn(x) == default_stringifier(x)
