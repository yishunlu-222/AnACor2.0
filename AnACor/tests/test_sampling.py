
import pytest

class TestBasic:
    @classmethod
    def setup_class(cls):
        """Set up any state specific to the execution of the given class."""
        pass  # If any setup is needed before running tests

    def test_import(cls):
        import AnACor
        from AnACor.utils.utils_mp import worker_function
        from AnACor.utils.utils_rt import generate_sampling
    # def test_sampling(cls):
        assert AnACor is not None
        assert worker_function is not None
        assert generate_sampling is not None