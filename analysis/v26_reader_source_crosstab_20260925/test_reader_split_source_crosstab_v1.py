"""Strict synthetic/adversarial unit tests; they grant NO frozen-byte authority."""
from __future__ import annotations
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).parent))
import verify_reader_split_source_crosstab_v1 as m


def fixture():
    registry = []
    reader = []
    for d, source, part in [('d1', 'HVS', 'reader_fit'),
                            ('d2', 'NPH52', 'reader_fit'),
                            ('d3', 'SEA_AD', 'reader_validation')]:
        reader.append({'donor_id': d, 'reader_partition': part})
        registry.append({'split_domain': 'foundation', 'study_id': source,
                         'canonical_person_id': source + '::' + d,
                         'split_group_id': source + '::' + d,
                         'split': 'train',
                         'pathology_used_for_foundation_split': 'False'})
    return reader, registry


class SourceCensusAdversaries(unittest.TestCase):
    def test_01_positive_all_sources_and_partitions(self):
        reader, registry = fixture()
        cross, mapping = m.derive_reader_sources(reader, registry)
        self.assertEqual(cross['reader_fit']['HVS'], 1)
        self.assertEqual(cross['reader_fit']['NPH52'], 1)
        self.assertEqual(cross['reader_fit']['SEA_AD'], 0)
        self.assertEqual(cross['reader_validation']['SEA_AD'], 1)
        self.assertEqual(cross['reader_oracle']['NPH52'], 0)
        self.assertEqual(set(mapping), {'d1', 'd2', 'd3'})

    def test_02_reader_duplicate_identity_fails(self):
        rd, reg = fixture()
        with self.assertRaisesRegex(ValueError, 'duplicate reader'):
            m.derive_reader_sources(rd + [rd[0].copy()], reg)

    def test_03_continuation_or_missing_donor_fails(self):
        rd, reg = fixture()
        rd[0]['donor_id'] = 'continuation_donor'
        with self.assertRaisesRegex(ValueError, 'outside exact foundation'):
            m.derive_reader_sources(rd, reg)

    def test_04_development_is_not_reader_fit_fails(self):
        rd, reg = fixture()
        reg[0]['split'] = 'development'
        with self.assertRaisesRegex(ValueError, 'outside exact foundation'):
            m.derive_reader_sources(rd, reg)

    def test_05_duplicate_foundation_row_fails(self):
        rd, reg = fixture()
        with self.assertRaisesRegex(ValueError, 'duplicate or group mismatch'):
            m.derive_reader_sources(rd, reg + [reg[0].copy()])

    def test_06_cross_source_prefix_collision_fails(self):
        rd, reg = fixture()
        reg[0]['canonical_person_id'] = 'SEA_AD::d1'
        with self.assertRaisesRegex(ValueError, 'study/person identity'):
            m.derive_reader_sources(rd, reg)

    def test_07_wrong_group_identity_fails(self):
        rd, reg = fixture()
        reg[0]['split_group_id'] = 'HVS::d2'
        with self.assertRaisesRegex(ValueError, 'group mismatch'):
            m.derive_reader_sources(rd, reg)

    def test_08_pathology_flag_in_frozen_split_fails(self):
        rd, reg = fixture()
        reg[0]['pathology_used_for_foundation_split'] = 'True'
        with self.assertRaisesRegex(ValueError, 'pathology-dependent'):
            m.derive_reader_sources(rd, reg)

    def test_09_orphan_extra_foundation_train_fails(self):
        rd, reg = fixture()
        r = reg[0].copy()
        r['canonical_person_id'] = r['split_group_id'] = 'HVS::orphan'
        with self.assertRaisesRegex(ValueError, 'not exactly identical'):
            m.derive_reader_sources(rd, reg + [r])

    def test_10_context_positive_separate_fit_cell_mass(self):
        rd, reg = fixture()
        cross, _ = m.derive_reader_sources(rd, reg)
        ctx = [{'partition':'reader_fit','source':'HVS','cell_count':'5','donor_count':'1'},
               {'partition':'reader_fit','source':'NPH52','cell_count':'7','donor_count':'1'},
               {'partition':'reader_validation','source':'SEA_AD','cell_count':'11','donor_count':'1'}]
        result = m.check_context(ctx, cross, fit_cell_counts={'HVS':5,'NPH52':7,'SEA_AD':0})
        self.assertEqual(result['reader_validation']['SEA_AD'],11)

    def test_11_context_val_donor_mismatch_fails(self):
        rd, reg = fixture(); cross, _ = m.derive_reader_sources(rd, reg)
        ctx = [{'partition':'reader_fit','source':'HVS','cell_count':'5','donor_count':'1'},
               {'partition':'reader_fit','source':'NPH52','cell_count':'7','donor_count':'1'},
               {'partition':'reader_validation','source':'SEA_AD','cell_count':'11','donor_count':'2'}]
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            m.check_context(ctx, cross, fit_cell_counts={'HVS':5,'NPH52':7,'SEA_AD':0})

    def test_12_context_fit_cell_mismatch_fails(self):
        rd, reg = fixture(); cross, _ = m.derive_reader_sources(rd, reg)
        ctx = [{'partition':'reader_fit','source':'HVS','cell_count':'4','donor_count':'1'},
               {'partition':'reader_fit','source':'NPH52','cell_count':'7','donor_count':'1'},
               {'partition':'reader_validation','source':'SEA_AD','cell_count':'11','donor_count':'1'}]
        with self.assertRaisesRegex(ValueError, 'fit cell counts'):
            m.check_context(ctx, cross, fit_cell_counts={'HVS':5,'NPH52':7,'SEA_AD':0})

    def test_13_duplicate_context_row_fails(self):
        rd, reg = fixture(); cross, _ = m.derive_reader_sources(rd, reg)
        ctx = [{'partition':'reader_fit','source':'HVS','cell_count':'5','donor_count':'1'}]*3
        with self.assertRaisesRegex(ValueError, 'unexpected/duplicate'):
            m.check_context(ctx, cross, fit_cell_counts={'HVS':5,'NPH52':7,'SEA_AD':0})

    def test_14_exact_header_no_silent_column_substitution(self):
        with self.assertRaisesRegex(ValueError, 'header mismatch'):
            m._csv(b'person,reader_partition\nd1,reader_fit\n',
                   ('donor_id','reader_partition'), 'reader')

    def test_15_numeric_decimal_or_scientific_not_accepted(self):
        for s in ('1.0','1e3','-1','','NaN'):
            with self.subTest(s=s), self.assertRaises(ValueError):
                m._natural(s,'count')

    def test_17_protected_split_flag_outside_fit_is_not_silently_ignored(self):
        rd, reg = fixture()
        addition = reg[0].copy()
        addition.update(split_domain='continuation', canonical_person_id='HVS::extra',
                        split_group_id='HVS::extra', pathology_used_for_foundation_split='True')
        with self.assertRaisesRegex(ValueError, 'pathology-dependent'):
            m.derive_reader_sources(rd, reg + [addition])

    def test_18_reader_and_continuation_domain_overlap_fails(self):
        rd, reg = fixture()
        addition = reg[0].copy()
        addition.update(split_domain='continuation')
        with self.assertRaisesRegex(ValueError, 'spills into continuation'):
            m.derive_reader_sources(rd, reg + [addition])

    def test_16_bad_archive_sha_fails_before_member_reads(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'fake.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('fake',b'irrelevant')
            with self.assertRaisesRegex(ValueError, 'whole-file SHA-256 mismatch'):
                m.verify_archive(p)


if __name__ == '__main__': unittest.main()
