# bib_lookup
A useful tool for looking up Bib entries using DOI, or pubmed ID (or URL), or arXiv ID (or URL).

It is an updated version of
https://github.com/wenh06/utils/blob/master/utils_universal/utils_bib.py

**NOTE** that you should have internet connection to use `bib_lookup`.

## Installation
Run
```bash
python -m pip install bib-lookup
```
or install the latest version in [GitHub](https://github.com/DeepPSP/bib_lookup/) using
```bash
python -m pip install git+https://github.com/DeepPSP/bib_lookup.git
```
or git clone this repository and install locally via
```bash
cd bib_lookup
python -m pip install .
```

## Requirements
- requests
- feedparser


## Usage Examples
```python
>>> bl = BibLookup(align="middle")
>>> res = bl("1707.07183")
@article{wen2017_1707.07183v2,
   author = {Hao Wen and Chunhui Liu},
    title = {Counting Multiplicities in a Hypersurface over a Number Field},
  journal = {arXiv preprint arXiv:1707.07183v2}
     year = {2017},
    month = {7},
}
>>> bl("10.1109/CVPR.2016.90")
@inproceedings{He_2016,
     author = {Kaiming He and Xiangyu Zhang and Shaoqing Ren and Jian Sun},
      title = {Deep Residual Learning for Image Recognition},
  booktitle = {2016 {IEEE} Conference on Computer Vision and Pattern Recognition ({CVPR})}
        doi = {10.1109/cvpr.2016.90},
       year = {2016},
      month = {6},
  publisher = {{IEEE}},
}
>>> bl("10.23919/cinc53138.2021.9662801", align="left-middle")
@inproceedings{Wen_2021,
  author    = {Hao Wen and Jingsu Kang},
  title     = {Hybrid Arrhythmia Detection on Varying-Dimensional Electrocardiography: Combining Deep Neural Networks and Clinical Rules},
  booktitle = {2021 Computing in Cardiology ({CinC})}
  doi       = {10.23919/cinc53138.2021.9662801},
  year      = {2021},
  month     = {9},
  publisher = {{IEEE}},
}
```

## TODO
1. add CLI support;
2. use eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi for PubMed, as in \[[3](#ref3)\];
3. try using google scholar api described in \[[4](#ref4)\] (unfortunately \[[4](#ref4)\] is charged);
4. use `Flask` to write a simple browser-based UI;

## WARNING
Many journals have specific requirements for the Bib entries,
for example, the title and/or journal (and/or booktitle), etc. should be **capitalized**,
which could not be done automatically since
- some abbreviations in title should have characters all in the upper case, for example
> ALBERT: A Lite BERT for Self-supervised Learning of Language Representations

- some should have characters all in in the lower case,
> mixup: Beyond Empirical Risk Minimization

- and some others should have mixed cases,
> KeMRE: Knowledge-enhanced Medical Relation Extraction for Chinese Medicine Instructions

This should be corrected by the user himself **if necessary** (which although is rare),
and remember to enclose such fields with **double curly braces**.

## References
1. <a name="ref1"></a> https://github.com/davidagraf/doi2bib2
2. <a name="ref2"></a> https://arxiv.org/help/api
3. <a name="ref3"></a> https://github.com/mfcovington/pubmed-lookup/
4. <a name="ref4"></a> https://serpapi.com/google-scholar-cite-api
5. <a name="ref5"></a> https://www.bibtex.com/
