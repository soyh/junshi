import unittest
from registration import validate

class RegistrationTests(unittest.TestCase):
    def test_boundaries(self):
        for name, password in [('A._','a'*12),('a'*64,'密'*256),('user-01','😀'*12)]:
            validate(name, password)
    def test_invalid_inputs(self):
        for name,password in [('ab','a'*12),('a'*65,'a'*12),('用户名','a'*12),('abc def','a'*12),('abc','😀'*6),('abc','a'*257)]:
            with self.assertRaises(ValueError): validate(name,password)

if __name__ == '__main__': unittest.main()
