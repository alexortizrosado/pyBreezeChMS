import unittest
import os
import json
from typing import List
from breeze_chms_api.profile_helper import (join_dicts,
                                            ProfileHelper,
                                            compare_profiles)

TEST_FILES_DIR = os.path.join(os.path.split(__file__)[0], 'test_files')

def make_dict(key_list: List[str], val: str):
    return {k: f'{k}: {val}' for k in key_list}

class HelperTests(unittest.TestCase):
    def _validate_merge(self, right_keys: List[str],
                        left_keys: List[str],
                        expect_order: List[str]
                        ) -> dict:
        right = make_dict(right_keys, 'right')
        left = make_dict(left_keys, 'left')
        result = join_dicts(right, left)
        got_keys = [k for k in result.keys()]
        self.assertEqual(got_keys, expect_order)
        lset = set(left.keys())
        rset = set(right.keys())
        allkeys = lset.union(rset)
        for k in allkeys:
            rv, lv = result.get(k)
            if k in rset:
                self.assertEqual(rv, f'{k}: right')
            else:
                self.assertIsNone(rv, f'Got unexpected right {rv}')
            if k in lset:
                self.assertEqual(lv, f'{k}: left')
            else:
                self.assertIsNone(lv, f'Got unexpected left {lv}')
        return result

    def test_merge(self):
        right_keys = ['a', 'l', 'x', 'c', 'd', 'e', 'b', 'z', 'q']
        left_keys = ['a', 'b', 'c', 'e', 'f', 'x', 'q']
        right = make_dict(right_keys, 'right')
        left = make_dict(left_keys, 'left')
        expect_order = ['a', 'b', 'c', 'e', 'l', 'f', 'x', 'q', 'd', 'z']
        self._validate_merge(right_keys, left_keys, expect_order)
        result = join_dicts(right, left)
        lset = set(left.keys())
        rset = set(right.keys())
        allkeys = lset.union(rset)
        for k in allkeys:
            rv, lv = result.get(k)
            if k in rset:
                self.assertEqual(rv, f'{k}: right')
            else:
                self.assertIsNone(rv, f'Got unexpected right {rv}')
            if k in lset:
                self.assertEqual(lv, f'{k}: left')
            else:
                self.assertIsNone(lv, f'Got unexpected left {lv}')

class DiffTests(unittest.TestCase):
    def test_diff(self):
        with open(os.path.join(TEST_FILES_DIR, 'TestDataRef.json'), 'r') as f:
            alldata = json.load(f)
            ref_field_spec = alldata[0]
            ref_profiles = alldata[1]
            ref_helper = ProfileHelper(ref_field_spec)
        with open(os.path.join(TEST_FILES_DIR, 'TestData.json'), 'r') as f:
            alldata = json.load(f)
            test_field_spec = alldata[0]
            test_profiles = alldata[1]
            test_helper = ProfileHelper(test_field_spec)
        field_names = ref_helper.get_field_id_to_name()
        field_names.update(test_helper.get_field_id_to_name())
        result = compare_profiles(ref_helper, test_helper, ref_profiles, test_profiles)
        self.assertIsNotNone(result)
        self.assertEqual(4, len(result))
        p = result[0]
        self.assertEqual(p[0], 'Alast, Firstname1')
        d = p[1][0]
        self.assertEqual(d[0], 'Spiritual Gifts:Spiritual Gifts')
        self.assertEqual(len(d[1]), 0)
        self.assertEqual(d[2], ['Exhortation'])

        p = result[1]
        self.assertEqual(p[0], 'Blast, Firstname2 Lee')
        d = p[1][0]
        self.assertEqual(d[0], 'Name')
        self.assertEqual(d[1], ['Blast, Firstname2 Lee'])
        self.assertEqual(d[2], ['Blast, Firstname2 (Harry) Lee'])
        d = p[1][1]
        self.assertEqual(d[0], 'Communication:Phone')
        self.assertEqual(d[1], ['mobile:(333) 543-2100(private)(no text)'])
        self.assertEqual(d[2], ['mobile:(333) 543-2100(private)'])
        d = p[1][3]
        self.assertEqual(d[0], 'Spiritual Gifts:Spiritual Gifts')
        self.assertEqual(d[1], ['Flimflammery'])
        self.assertEqual(len(d[2]), 0)

        p = result[2]
        self.assertEqual(p[0], 'Bonzo, NewFirst')
        d = p[1][0]
        d = p[1][1]
        self.assertEqual(d[0], 'Communication:Address')
        self.assertEqual(len(d[1]), 0)
        self.assertEqual(d[2], ['205 S Pleasant St;Los Angeles CA 12456'])


if __name__ == '__main__':
    unittest.main()