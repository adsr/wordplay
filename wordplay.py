#!/usr/bin/env python
import re
import random
import sys
import argparse

class Wordplay:
    """Algorithmic wordplay"""
    def __init__(self):
        """Make a Wordplay instance."""
        self.word_phoneme_map = {}
        self.phoneme_word_trie = {}
        self.phoneme_type_map = {}
        self.type_phoneme_map = {}
    def load_cmudict(self, cmudict_path, cmudict_phones_path):
        """Load a cmudict from `cmudict_path`.
        May throw an exception if `cmudict_path` is unreadable.
        See <http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict/>."""
        self.build_word_phoneme_map(cmudict_path)
        self.build_phoneme_word_trie(self.word_phoneme_map)
        self.build_phoneme_maps(cmudict_phones_path)
    def get_wordplay(self, line, num_tries = 100):
        """Attempt wordplay on `line`.
        Return None on failure or a string on a success."""
        words = re.split('\s+', line.strip())
        norm_words = self.normalize_words(words)
        num_mutations = max(int(len(norm_words) / 5), 1)
        phonemes = self.get_phonemes(norm_words)
        if not phonemes:
            return None
        new_words = None
        while num_tries > 0:
            mutated_phonemes = self.mutate(phonemes, num_mutations)
            new_words = self.phonemes_to_words(mutated_phonemes, norm_words)
            if new_words and new_words != norm_words:
                break
            num_tries -= 1
        if not new_words:
            return None
        return ' '.join(self.stylize(new_words, words, line))
    def normalize_words(self, words):
        """Return a normalized version of `words`."""
        return [ re.sub("[^A-Za-z_'-]", '', word).upper() for word in words ]
    def get_phonemes(self, words):
        """Return a list of phonemes in `words`.
        Return None on failure."""
        phonemes = []
        for word in words:
            if not word in self.word_phoneme_map:
                return None
            phonemes.extend(random.choice(self.word_phoneme_map[word]))
        return phonemes
    def mutate(self, phonemes, num_mutations):
        """Return a mutated list of `phonemes`."""
        mutated_phonemes = list(phonemes)
        while num_mutations > 0:
            num_phonemes = len(mutated_phonemes)
            idx = random.randint(0, num_phonemes - 1)
            type = self.phoneme_type_map[mutated_phonemes[idx]]
            if len(self.type_phoneme_map[type]) == 1:
                mutated_phonemes.pop(idx)
            else:
                potential_phonemes = list(self.type_phoneme_map[type])
                potential_phonemes.pop(potential_phonemes.index(mutated_phonemes[idx]))
                mutated_phonemes[idx] = random.choice(self.type_phoneme_map[type])
            num_mutations -= 1
        return mutated_phonemes
    def phonemes_to_words(self, phonemes, norm_words):
        """Return a list of words spelled by `phonemes`.
        Return None on failure."""
        words_set = []
        self.phonemes_to_words_recurse(
            self.phoneme_word_trie, list(phonemes), [], norm_words, words_set
        )
        if len(words_set) > 0:
            return self.pick_words(words_set, norm_words)
        return None
    def phonemes_to_words_recurse(self, root, phonemes, words, norm_words, words_set):
        """Return a list of words spelled by `phonemes`.
        Return None on failure."""
        next_phoneme = phonemes.pop(0)
        if not next_phoneme in root:
            return
        new_root = root[next_phoneme]
        next_word = None
        if '*' in new_root:
            next_word = self.pick_word(new_root['*'], norm_words)
        if len(phonemes) == 0:
            if next_word:
                words.append(next_word)
                words_set.append(words)
            return
        if next_word:
            words_copy = list(words)
            words_copy.append(next_word)
            self.phonemes_to_words_recurse(
                self.phoneme_word_trie, list(phonemes), words_copy, norm_words, words_set
            )
        self.phonemes_to_words_recurse(
            new_root, list(phonemes), list(words), norm_words, words_set
        )
    def pick_word(self, potential_words, norm_words):
        """Return a word from `potential_words` favoring words that appear in
        `norm_words`."""
        for word in potential_words:
            if word in norm_words:
                return word
        return random.choice(potential_words)
    def pick_words(self, words_set, norm_words):
        """Return an element from `words_set` favoring elements that have more
        words in `norm_words`."""
        random.shuffle(words_set)
        def pick_words_score(words):
            score = 0
            for word in words:
                if word in norm_words:
                    score += 1
            return score
        words_set.sort(lambda a, b: pick_words_score(b) - pick_words_score(a))
        return words_set[0]
    def stylize(self, words, orig_words, line):
        """Copy capitalization and punctuation from `orig_words` into
        `words`."""
        num_words = len(words)
        num_orig_words = len(orig_words)
        num_min = min(num_words, num_orig_words)
        index_pairs = []
        for i in range(num_words):
            if i == num_words - 1:
                j = num_orig_words - 1
            elif i == 0:
                j = 0
            else:
                j = min(i, num_orig_words - 2)
            index_pairs.append((i, j, ))
        for index_pair in index_pairs:
            word = words[index_pair[0]].lower()
            orig_word = orig_words[index_pair[1]]
            if len(orig_word) > 1 and orig_word == orig_word.upper():
                word = word.upper()
            elif orig_word[0] >= "A" and orig_word[0] <= "Z":
                word = word[0].upper() + word[1:]
            trailing_punctuation = re.search('[^A-Za-z]+$', orig_word)
            if trailing_punctuation:
                word += trailing_punctuation.group(0)
            words[index_pair[0]] = word
        return words
    def build_phoneme_maps(self, cmudict_phones_path):
        """Build a map of phonemes to phoneme types and vice-versa."""
        self.phoneme_type_map = {}
        self.type_phoneme_map = {}
        with open(cmudict_phones_path) as f:
            for line in f:
                terms = re.split('\s+', line.strip(), 2)
                if len(terms) != 2:
                    continue
                self.phoneme_type_map[terms[0]] = terms[1]
                if terms[1] not in self.type_phoneme_map:
                    self.type_phoneme_map[terms[1]] = []
                self.type_phoneme_map[terms[1]].append(terms[0])
    def build_word_phoneme_map(self, cmudict_path):
        """Build a map of words to phonemes from `cmudict_path`.
        Throw exception if `cmudict_path` is unreadable."""
        self.word_phoneme_map = {}
        with open(cmudict_path) as f:
            for line in f:
                first_char = line[0:1]
                if first_char < 'A' or first_char > 'Z':
                    continue
                terms = re.split('\s+', line.strip())
                if len(terms) < 2:
                    continue
                word = terms[0].split('(')[0]
                phonemes = [
                    re.sub("[^A-Za-z]", '', phoneme).upper() for phoneme in terms[1:]
                ]
                if not word in self.word_phoneme_map:
                    self.word_phoneme_map[word] = []
                self.word_phoneme_map[word].append(phonemes)
    def build_phoneme_word_trie(self, word_phoneme_map):
        """Build a trie of phonemes with words as leaf nodes using
        `word_phoneme_map`."""
        self.phoneme_word_trie = {}
        for word in word_phoneme_map:
            phonemes_set = word_phoneme_map[word]
            for phonemes in phonemes_set:
                self.build_phoneme_word_trie_recurse_term(
                    self.phoneme_word_trie, list(phonemes), word
                )
    def build_phoneme_word_trie_recurse_term(self, root, phonemes, word):
        """Ensure the path in `phonemes` exists in `self.phoneme_word_trie`
        and add `word` as a leaf to the end node."""
        next_phoneme = phonemes.pop(0)
        if not next_phoneme in root:
            root[next_phoneme] = {}
        new_root = root[next_phoneme]
        if len(phonemes) > 0:
            self.build_phoneme_word_trie_recurse_term(
                new_root, phonemes, word
            )
        else:
            if not '*' in new_root:
                new_root['*'] = []
            new_root['*'].append(word)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Algorithmic wordplay tool.')
    parser.add_argument('-d', '--dict', required=True, help='cmudict path')
    parser.add_argument('-p', '--phones', required=True, help='cmudict phones path')
    parser.add_argument('-s', '--use_stdin', action='store_true', help='read stdin instead of key input')
    args = vars(parser.parse_args())
    wordplay = Wordplay()
    print >> sys.stderr, args
    print >> sys.stderr, 'Loading cmudict...'
    wordplay.load_cmudict(args['dict'], args['phones'])
    print >> sys.stderr, 'Loaded!'
    while True:
        if args['use_stdin']:
            line = sys.stdin.readline()
        else:
            line = raw_input('> ')
            line = line.strip()
            if len(line) < 1:
                break
        output = wordplay.get_wordplay(line.strip())
        if output:
            print >> sys.stdout, output
            sys.stdout.flush()
