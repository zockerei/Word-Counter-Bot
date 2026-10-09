import unittest

from counting import compile_patterns, count_words, normalize


class TestCounting(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize('  Café ÜBER  '), 'cafe uber')

    def test_counts_whole_words_only(self):
        patterns = compile_patterns(['cat'])
        self.assertEqual(count_words('Cat, cat! concatenate cats', patterns), {'cat': 2})

    def test_phrases_with_spaces(self):
        patterns = compile_patterns(['dead server'])
        self.assertEqual(count_words('DEAD SERVER again, dead server', patterns), {'dead server': 2})

    def test_accents_match(self):
        patterns = compile_patterns(['frauen'])
        self.assertEqual(count_words('Fräuen und frauen', patterns), {'frauen': 2})

    def test_multiple_words_and_misses(self):
        patterns = compile_patterns(['a b', 'c', 'missing'])
        self.assertEqual(count_words('a b c c', patterns), {'a b': 1, 'c': 2})

    def test_regex_characters_are_literal(self):
        patterns = compile_patterns(['c.t'])
        self.assertEqual(count_words('cat c.t', patterns), {'c.t': 1})


if __name__ == '__main__':
    unittest.main()
