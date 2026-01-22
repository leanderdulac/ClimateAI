import sys
from unittest.mock import MagicMock

# Create dummy classes
class Tensor:
    pass

class Module:
    pass

# Setup torch mock
torch_mock = MagicMock()
torch_mock.Tensor = Tensor

# Setup torch.nn mock
nn_mock = MagicMock()
nn_mock.Module = Module
torch_mock.nn = nn_mock

# Setup torch.nn.functional mock
functional_mock = MagicMock()
nn_mock.functional = functional_mock
torch_mock.nn.functional = functional_mock

# Register in sys.modules
sys.modules["torch"] = torch_mock
sys.modules["torch.nn"] = nn_mock
sys.modules["torch.nn.functional"] = functional_mock
sys.modules["tensorflow"] = MagicMock()
sys.modules["pynamicalsys"] = MagicMock()
sys.modules["pycep_correios"] = MagicMock()
