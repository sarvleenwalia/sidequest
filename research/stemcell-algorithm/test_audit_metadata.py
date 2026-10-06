import unittest
import pandas as pd
from audit_metadata import audit


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.frame=pd.DataFrame({'cell_id':[f'c{i}' for i in range(8)],
                                 'donor_id':[f'd{i}' for i in range(8)],
                                 'batch_id':['b1','b2']*4,'status':['PD']*4+['control']*4})

    def test_eligible_metadata(self):
        self.assertTrue(audit(self.frame)['eligible_for_declared_cv'])

    def test_samples_are_not_new_donors(self):
        self.frame['donor_id']=['pd_donor']*4+['control_donor']*4
        report=audit(self.frame)
        self.assertFalse(report['eligible_for_declared_cv'])
        self.assertEqual(report['donors_per_class'],{'PD':1,'control':1})

    def test_batch_confounding_rejected(self):
        self.frame['batch_id']=['b1']*4+['b2']*4
        self.assertTrue(any('confounding' in x for x in audit(self.frame)['reasons']))


if __name__=='__main__':
    unittest.main()
