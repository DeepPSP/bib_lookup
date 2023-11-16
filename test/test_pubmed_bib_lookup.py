"""
"""

import bib_lookup

pubmed_examples = {
    "PMID: 35344711": "@article{Li_2022,\n      title = {Broad neutralization of SARS-CoV-2 variants by an inhalable bispecific single-domain antibody},\n     author = {Li, Cheng and Zhan, Wuqiang and Yang, Zhenlin and Tu, Chao and Hu, Gaowei and Zhang, Xiang and Song, Wenping and Du, Shujuan and Zhu, Yuanfei and Huang, Keke and Kong, Yu and Zhang, Meng and Mao, Qiyu and Gu, Xiaodan and Zhang, Yi and Xie, Youhua and Deng, Qiang and Song, Yuanlin and Chen, Zhenguo and Lu, Lu and Jiang, Shibo and Wu, Yanling and Sun, Lei and Ying, Tianlei},\n    journal = {Cell},\n     volume = {185},\n       issn = {0092-8674},\n        doi = {10.1016/j.cell.2022.03.009},\n     number = {8},\n  publisher = {Elsevier BV},\n       year = {2022},\n      month = {4},\n      pages = {1389-1401.e18}\n}",
    "20339075": "@article{Wang_2010,\n      title = {The Wnt/β-Catenin Pathway Is Required for the Development of Leukemia Stem Cells in AML},\n     author = {Wang, Yingzi and Krivtsov, Andrei V. and Sinha, Amit U. and North, Trista E. and Goessling, Wolfram and Feng, Zhaohui and Zon, Leonard I. and Armstrong, Scott A.},\n    journal = {Science},\n     volume = {327},\n       issn = {1095-9203},\n        doi = {10.1126/science.1186624},\n     number = {5973},\n  publisher = {American Association for the Advancement of Science (AAAS)},\n       year = {2010},\n      month = {3},\n      pages = {1650–1653}\n}",
    "PMCID: PMC8956294": "@article{Swets_2022,\n      title = {SARS-CoV-2 co-infection with influenza viruses, respiratory syncytial virus, or adenoviruses},\n     author = {Swets, Maaike C and Russell, Clark D and Harrison, Ewen M and Docherty, Annemarie B and Lone, Nazir and Girvan, Michelle and Hardwick, Hayley E and Visser, Leonardus G and Openshaw, Peter J M and Groeneveld, Geert H and Semple, Malcolm G and Baillie, J Kenneth},\n    journal = {The Lancet},\n     volume = {399},\n       issn = {0140-6736},\n        doi = {10.1016/s0140-6736(22)00383-x},\n     number = {10334},\n  publisher = {Elsevier BV},\n       year = {2022},\n      month = {4},\n      pages = {1463–1464}\n}",
    "https://pubmed.ncbi.nlm.nih.gov/35172054/": "@article{Hammond_2022,\n      title = {Oral Nirmatrelvir for High-Risk, Nonhospitalized Adults with Covid-19},\n     author = {Hammond, Jennifer and Leister-Tebbe, Heidi and Gardner, Annie and Abreu, Paula and Bao, Weihang and Wisemandle, Wayne and Baniecki, MaryLynn and Hendrick, Victoria M. and Damle, Bharat and Simón-Campos, Abraham and Pypstra, Rienk and Rusnak, James M.},\n    journal = {New England Journal of Medicine},\n     volume = {386},\n       issn = {1533-4406},\n        doi = {10.1056/nejmoa2118542},\n     number = {15},\n  publisher = {Massachusetts Medical Society},\n       year = {2022},\n      month = {4},\n      pages = {1397–1408}\n}",
}


bl = bib_lookup.BibLookup(cache_limit=None)


def test_pubmed_bib_lookup():
    for pmid, lookup_result in pubmed_examples.items():
        bib_string = bl(pmid, timeout=1000)
        assert bib_string == lookup_result, f"{pmid} mismatch"
    bib_string = bl(pmid, timeout=1000, verbose=10)
    assert bib_string == lookup_result, f"{pmid} mismatch"
