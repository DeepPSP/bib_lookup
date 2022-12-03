"""
"""

import bib_lookup


arXiv_examples = {
    "arXiv:1707.07183v2": "@article{wen2017_1707.07183v2,\n    title = {Counting Multiplicities in a Hypersurface over a Number Field},\n   author = {Hao Wen and Chunhui Liu},\n  journal = {arXiv preprint arXiv:1707.07183v2},\n     year = {2017},\n    month = {7}\n}",
    "1804.02767": "@article{redmon2018_1804.02767v1,\n    title = {YOLOv3: An Incremental Improvement},\n   author = {Joseph Redmon and Ali Farhadi},\n  journal = {arXiv preprint arXiv:1804.02767v1},\n     year = {2018},\n    month = {4}\n}",
    "arxiv.org/abs/1908.08681": "@article{misra2019_1908.08681v3,\n    title = {Mish: A Self Regularized Non-Monotonic Activation Function},\n   author = {Diganta Misra},\n  journal = {arXiv preprint arXiv:1908.08681v3},\n     year = {2019},\n    month = {8}\n}",
    "https://arxiv.org/abs/1909.11942": "@article{lan2019_1909.11942v6,\n    title = {ALBERT: A Lite BERT for Self-supervised Learning of Language Representations},\n   author = {Zhenzhong Lan and Mingda Chen and Sebastian Goodman and Kevin Gimpel and Piyush Sharma and Radu Soricut},\n  journal = {arXiv preprint arXiv:1909.11942v6},\n     year = {2019},\n    month = {9}\n}",
}


bl = bib_lookup.BibLookup()


def test_arxiv_bib_lookup():
    for arXiv_id, lookup_result in arXiv_examples.items():
        bib_string = bl(arXiv_id, arxiv2doi=False, timeout=1000)
        assert bib_string == lookup_result, f"{arXiv_id} mismatch"
    bib_string = bl(arXiv_id, arxiv2doi=True, timeout=1000, verbose=10)
