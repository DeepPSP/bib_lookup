try:
    import bib_lookup
except ModuleNotFoundError:
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
    import bib_lookup


pubmed_examples = {
    "PMID: 35344711": "@article{Li_2022,\n      title = {Broad neutralization of {SARS}-{CoV}-2 variants by an inhalable bispecific single-domain antibody},\n     author = {Cheng Li and Wuqiang Zhan and Zhenlin Yang and Chao Tu and Gaowei Hu and Xiang Zhang and Wenping Song and Shujuan Du and Yuanfei Zhu and Keke Huang and Yu Kong and Meng Zhang and Qiyu Mao and Xiaodan Gu and Yi Zhang and Youhua Xie and Qiang Deng and Yuanlin Song and Zhenguo Chen and Lu Lu and Shibo Jiang and Yanling Wu and Lei Sun and Tianlei Ying},\n    journal = {Cell},\n        doi = {10.1016/j.cell.2022.03.009},\n       year = {2022},\n      month = {4},\n  publisher = {Elsevier {BV}},\n     volume = {185},\n     number = {8},\n      pages = {1389--1401.e18}\n}",
    "20339075": "@article{Wang_2010,\n      title = {The Wnt/$\\upbeta$-Catenin Pathway Is Required for the Development of Leukemia Stem Cells in {AML}},\n     author = {Yingzi Wang and Andrei V. Krivtsov and Amit U. Sinha and Trista E. North and Wolfram Goessling and Zhaohui Feng and Leonard I. Zon and Scott A. Armstrong},\n    journal = {Science},\n        doi = {10.1126/science.1186624},\n       year = {2010},\n      month = {3},\n  publisher = {American Association for the Advancement of Science ({AAAS})},\n     volume = {327},\n     number = {5973},\n      pages = {1650--1653}\n}",
    "PMCID: PMC8956294": "@article{Swets_2022,\n      title = {{SARS}-{CoV}-2 co-infection with influenza viruses, respiratory syncytial virus, or adenoviruses},\n     author = {Maaike C Swets and Clark D Russell and Ewen M Harrison and Annemarie B Docherty and Nazir Lone and Michelle Girvan and Hayley E Hardwick and Leonardus G Visser and Peter J M Openshaw and Geert H Groeneveld and Malcolm G Semple and J Kenneth Baillie},\n    journal = {The Lancet},\n        doi = {10.1016/s0140-6736(22)00383-x},\n       year = {2022},\n      month = {4},\n  publisher = {Elsevier {BV}},\n     volume = {399},\n     number = {10334},\n      pages = {1463--1464}\n}",
    "https://pubmed.ncbi.nlm.nih.gov/35172054/": "@article{Hammond_2022,\n      title = {Oral Nirmatrelvir for High-Risk, Nonhospitalized Adults with Covid-19},\n     author = {Jennifer Hammond and Heidi Leister-Tebbe and Annie Gardner and Paula Abreu and Weihang Bao and Wayne Wisemandle and MaryLynn Baniecki and Victoria M. Hendrick and Bharat Damle and Abraham Sim{\\'{o}}n-Campos and Rienk Pypstra and James M. Rusnak},\n    journal = {New England Journal of Medicine},\n        doi = {10.1056/nejmoa2118542},\n       year = {2022},\n      month = {4},\n  publisher = {Massachusetts Medical Society},\n     volume = {386},\n     number = {15},\n      pages = {1397--1408}\n}",
}


bl = bib_lookup.BibLookup()


def test_pubmed_bib_lookup():
    for pmid, lookup_result in pubmed_examples.items():
        bib_string = bl(pmid, timeout=1000)
        assert bib_string == lookup_result, f"{pmid} mismatch"


if __name__ == "__main__":
    test_pubmed_bib_lookup()
