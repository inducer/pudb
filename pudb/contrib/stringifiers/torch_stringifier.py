from typing import Any

try:
    import torch

    HAVE_TORCH = 1
except:
    HAVE_TORCH = 0

import pudb.var_view as vv


def torch_stringifier_fn(value: Any) -> str:
    if not HAVE_TORCH:
        # Fall back to default stringifier

        return vv.default_stringifier(value)

    if isinstance(value, torch.nn.Module):
        device: str = str(next(value.parameters()).device)
        params: int = sum([p.numel() for p in value.parameters() if p.requires_grad])
        rep: str = value.__repr__() if len(value.__repr__()) < 55 else type(
            value
        ).__name__

        return "{}[{}] Params: {}".format(rep, device, params)
    elif isinstance(value, torch.Tensor):
        return "{}[{}][{}] {}".format(
            type(value).__name__,
            str(value.dtype).replace("torch.", ""),
            str(value.device),
            str(list(value.shape)),
        )
    else:
        # Fall back to default stringifier

        return vv.default_stringifier(value)
