from .agr_256 import palette_dict as agr256
from .classic import palette_dict as classic
from .dark_vim import palette_dict as darkvim
from .gray_light_256 import palette_dict as graylight256
from .midnight import palette_dict as midnight
from .mono import palette_dict as mono
from .monokai import palette_dict as monokai
from .monokai_256 import palette_dict as monokai256
from .nord_dark_256 import palette_dict as norddark256
from .solarized import palette_dict as solarized
from .vim import palette_dict as vim


THEMES = {
    "classic": classic,
    "vim": vim,
    "dark vim": darkvim,
    "midnight": midnight,
    "monokai": monokai,
    "solarized": solarized,
    "mono": mono,
    "agr-256": agr256,
    "gray-light-256": graylight256,
    "monokai-256": monokai256,
    "nord-dark-256": norddark256,
}
