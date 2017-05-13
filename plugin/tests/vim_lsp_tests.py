import unittest
import vim_lsp as sut


@unittest.skip("Don't forget to test!")
class VimLspTests(unittest.TestCase):

    def test_example_fail(self):
        result = sut.vim_lsp_example()
        self.assertEqual("Happy Hacking", result)
