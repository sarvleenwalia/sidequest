import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.io import mmwrite
import stemcell as s


class PipelineTests(unittest.TestCase):
    def test_single_label_donor_folds_keep_every_class(self):
        # Minimum eligible cohort, ordered by class, with two profiles/donor.
        units = pd.DataFrame({'donor_id':[f'd{i//2}' for i in range(16)],
                              'label':['a']*8+['b']*8})
        X = np.random.default_rng(1).normal(size=(16,8))
        for seed in [0, 4, 42]:
            report, _, _ = s.model_evaluation(X, units, 4, 4, seed, with_interval=False)
            labels = dict(zip(units.donor_id, units.label))
            for fold in report['folds']:
                self.assertEqual({labels[d] for d in fold['test_donors']}, {'a','b'})
                self.assertFalse(set(fold['train_donors']) & set(fold['test_donors']))

    def test_donor_bootstrap_perfect_predictions(self):
        result = s.donor_bootstrap(['a','a','b','b'],['a','a','b','b'],['d1','d2','d3','d4'],iterations=100)
        self.assertEqual(result['interval_95_percent'],[1.,1.])
        self.assertEqual(result['resampling_unit'],'donor')

    def test_qc_removes_high_mitochondrial_and_empty_cells(self):
        X = sparse.csr_matrix([[90,10,0],[1,20,30],[0,0,0]])
        keep, _ = s.qc(X, ['MT-ND1','TH','DDC'], min_genes=2, max_mt=20)
        self.assertEqual(keep.tolist(), [False,True,False])

    def test_normalization_matches_expected_values(self):
        X = sparse.csr_matrix([[1,3],[0,2]])
        np.testing.assert_allclose(s.normalize(X).toarray(), np.log1p([[2500,7500],[0,10000]]))

    def test_pseudobulk_sums_counts_not_logs(self):
        X = sparse.csr_matrix([[1,2],[3,4],[7,8]])
        meta = pd.DataFrame({'donor_id':['a','a','b'], 'status':['PD','PD','control'], 'batch_id':['x']*3}, index=['c1','c2','c3'])
        bulk, units = s.pseudobulk(X,meta,'status',min_cells=1)
        np.testing.assert_array_equal(bulk.toarray(), [[4,6],[7,8]])
        self.assertEqual(units.n_cells.tolist(),[2,1])

    def test_variable_gene_selection_uses_training_only(self):
        selector = s.VariableGenes(1).fit(np.array([[0,100],[2,100],[4,100]]))
        np.testing.assert_array_equal(selector.indices_,[0])
        np.testing.assert_array_equal(selector.transform(np.array([[1,999999]])),[[1]])

    def test_bh_known_example(self):
        np.testing.assert_allclose(s.bh(np.array([.01,.04,.03,.9])),[.04,.0533333333,.0533333333,.9])

    def test_rejects_log_normalized_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            pd.DataFrame([[.5,1]],index=['a'],columns=['g1','g2']).to_csv(p/'counts.csv')
            pd.DataFrame({'cell_id':['a'],'donor_id':['d'],'status':['PD']}).to_csv(p/'meta.csv',index=False)
            with self.assertRaisesRegex(ValueError,'integer counts'):
                s.read_data(p/'counts.csv',p/'meta.csv')

    def test_donor_folds_have_no_overlap(self):
        R = np.random.default_rng(4)
        units = pd.DataFrame({'donor_id':[f'd{i//2}' for i in range(32)],'label':['a','b']*16})
        X = R.normal(size=(32,20)); X[1::2,:5] += 4
        report, prediction, importance = s.model_evaluation(X, units, 4, 10, 42)
        for fold in report['folds']:
            self.assertFalse(set(fold['train_donors']) & set(fold['test_donors']))
        self.assertEqual(len(prediction),32)
        self.assertEqual(len(importance),20)
        self.assertGreater(report['balanced_accuracy'],.8)

    def test_insufficient_donors_rejected(self):
        units = pd.DataFrame({'donor_id':['a','b','c','d'],'label':['a','a','b','b']})
        with self.assertRaisesRegex(ValueError,'at least 4 donors'):
            s.model_evaluation(np.ones((4,10)),units,4,5,42)

    def test_mtx_raw_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            mmwrite(p/'counts.mtx', sparse.csr_matrix([[1,2,3],[4,5,6]]))
            pd.DataFrame({'cell_id':['a','b'],'donor_id':['d1','d2']}).to_csv(p/'meta.csv',index=False)
            (p/'genes.csv').write_text('TH\nDDC\nMT-ND1\n')
            X, meta, genes = s.read_data(p/'counts.mtx',p/'meta.csv',p/'genes.csv')
            self.assertEqual(X.shape,(2,3))
            self.assertEqual(genes.tolist(),['TH','DDC','MT-ND1'])

    def test_h5ad_uses_counts_layer(self):
        import anndata
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'counts.h5ad'
            adata = anndata.AnnData(X=np.array([[.2,.3],[.4,.5]]),
                                   obs=pd.DataFrame({'donor_id':['a','b']},index=['c1','c2']),
                                   var=pd.DataFrame(index=['TH','DDC']))
            adata.layers['counts'] = sparse.csr_matrix([[1,2],[3,4]])
            adata.write_h5ad(p)
            X, _, _ = s.read_data(p)
            np.testing.assert_array_equal(X.toarray(),[[1,2],[3,4]])


if __name__ == '__main__':
    unittest.main()
