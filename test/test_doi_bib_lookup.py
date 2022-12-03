"""
"""

import bib_lookup


doi_examples = {
    "DOI: 10.1142/S1005386718000305": "@article{Wen_2018,\n      title = {Counting Multiplicities in a Hypersurface over Number Fields},\n     author = {Hao Wen and Chunhui Liu},\n    journal = {Algebra Colloquium},\n        doi = {10.1142/s1005386718000305},\n       year = {2018},\n      month = {8},\n  publisher = {World Scientific Pub Co Pte Lt},\n     volume = {25},\n     number = {03},\n      pages = {437--458}\n}",
    "10.1109/ICCVW.2019.00246": "@inproceedings{Cao_2019,\n      title = {{GCNet}: Non-Local Networks Meet Squeeze-Excitation Networks and Beyond},\n     author = {Yue Cao and Jiarui Xu and Stephen Lin and Fangyun Wei and Han Hu},\n  booktitle = {2019 {IEEE}/{CVF} International Conference on Computer Vision Workshop ({ICCVW})},\n        doi = {10.1109/iccvw.2019.00246},\n       year = {2019},\n      month = {10},\n  publisher = {{IEEE}}\n}",
    "10.1109/tpami.2019.2913372": "@article{Hu_2020,\n      title = {Squeeze-and-Excitation Networks},\n     author = {Jie Hu and Li Shen and Samuel Albanie and Gang Sun and Enhua Wu},\n    journal = {{IEEE} Transactions on Pattern Analysis and Machine Intelligence},\n        doi = {10.1109/tpami.2019.2913372},\n       year = {2020},\n      month = {8},\n  publisher = {Institute of Electrical and Electronics Engineers ({IEEE})},\n     volume = {42},\n     number = {8},\n      pages = {2011--2023}\n}",
    "doi.org/10.1007/s11263-019-01198-w": "@article{Wu_2019,\n      title = {Group Normalization},\n     author = {Yuxin Wu and Kaiming He},\n    journal = {International Journal of Computer Vision},\n        doi = {10.1007/s11263-019-01198-w},\n       year = {2019},\n      month = {7},\n  publisher = {Springer Science and Business Media {LLC}},\n     volume = {128},\n     number = {3},\n      pages = {742--755}\n}",
    "https://doi.org/10.23919/cinc53138.2021.9662801": "@inproceedings{Wen_2021,\n      title = {Hybrid Arrhythmia Detection on Varying-Dimensional Electrocardiography: Combining Deep Neural Networks and Clinical Rules},\n     author = {Hao Wen and Jingsu Kang},\n  booktitle = {2021 Computing in Cardiology ({CinC})},\n        doi = {10.23919/cinc53138.2021.9662801},\n       year = {2021},\n      month = {9},\n  publisher = {{IEEE}}\n}",
}


bl = bib_lookup.BibLookup()
bl.debug()


def test_doi_bib_lookup():
    for doi, lookup_result in doi_examples.items():
        bib_string = bl(doi, timeout=1000, verbose=3)
        assert bib_string == lookup_result, f"{doi} mismatch"

        assert bib_lookup.bib_lookuper(doi, timeout=1000, ignore_fields="doi") is None

    assert bl(list(doi_examples), timeout=1000, print_result=True, verbose=10) is None
