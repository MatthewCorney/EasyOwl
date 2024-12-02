# Introduction
Simple and quick way to parse and understand XML based ontology formats, created due to problems
that more comprehensive packages have in converting some owl and obo files into python objects due to 
problems inherent to the file format and the lack of consistency.


# Dependencies
- requests
- lxml
- sklearn
- scipy
- numpy

# Usage

# Example
```
pip install git+https://github.com/MatthewCorney/EasyOwl.git
```
#### Downloading
```
from easyowl.dowload import download_ontology
from easyowl.reader import OntologyParser
from pprint import pprint

download_ontology(url="https://github.com/EBISPOT/efo/releases/download/current/efo.owl", destination_dir="data")
```
#### Parse to Dictionary
```
parser = OntologyParser(f"data/efo.owl")
```
#### Example Format
```
res=parser.entities['http://www.ebi.ac.uk/efo/EFO_0005634']
pprint(res)
```
```
{'disjoints': [],
 'matches': {'broadMatch': [],
             'closeMatch': [],
             'exactMatch': [],
             'narrowMatch': []},
 'properties': {'IAO_0000115': 'The Anatomical Therapeutic Chemical (ATC) '
                               'Classification System is used for the '
                               'classification of active ingredients of drugs '
                               'according to the organ or system on which they '
                               'act and their therapeutic, pharmacological and '
                               'chemical properties. It is controlled by the '
                               'World Health Organization Collaborating Centre '
                               'for Drug Statistics Methodology (WHOCC), and '
                               'was first published in 1976.',
                'IAO_0000117': 'Sirarat Sarntivijai',
                'comment': 'In the Anatomical Therapeutic Chemical (ATC) '
                           'classification system, the active substances are '
                           'divided into different groups according to the '
                           'organ or system on which they act and their '
                           'therapeutic, pharmacological and chemical '
                           'properties. Drugs are classified in groups at five '
                           'different levels.  The drugs are divided into '
                           'fourteen main groups (1st level), with '
                           'pharmacological/therapeutic subgroups (2nd '
                           'level).  The 3rd and 4th levels are '
                           'chemical/pharmacological/therapeutic subgroups and '
                           'the 5th level is the chemical substance.  The 2nd, '
                           '3rd and 4th levels are often used to identify '
                           'pharmacological subgroups when that is considered '
                           'more appropriate than therapeutic or chemical '
                           'subgroups.',
                'hasExactSynonym': 'Anatomical Therapeutic Chemical '
                                   'Classification System',
                'label': 'ATC Classification System',
                'subClassOf': 'http://purl.obolibrary.org/obo/IAO_0000030'},
 'subclasses': ['http://purl.obolibrary.org/obo/IAO_0000030'],
 'synonyms': {'hasBroadSynonym': [],
              'hasExactSynonym': ['Anatomical Therapeutic Chemical '
                                  'Classification System'],
              'hasNarrowSynonym': []}}
```
#### Get Parent Terms
```
parents = parser.get_parents('http://www.ebi.ac.uk/efo/EFO_0005634', max_depth=-1)
pprint(parents)
```

```
['http://www.ebi.ac.uk/efo/EFO_0005634',
 'http://purl.obolibrary.org/obo/IAO_0000030',
 'http://www.ebi.ac.uk/efo/EFO_0000001']
```
#### Get Child Terms


```
children = parser.get_children('http://www.ebi.ac.uk/efo/EFO_0005634', max_depth=-1)
pprint(children)
```
```
['http://www.ebi.ac.uk/efo/EFO_0005635',
 'http://www.ebi.ac.uk/efo/EFO_0005640',
 'http://www.ebi.ac.uk/efo/EFO_0005637',
 'http://www.ebi.ac.uk/efo/EFO_0005643',
 'http://www.ebi.ac.uk/efo/EFO_0005645',
 'http://www.ebi.ac.uk/efo/EFO_0005644',
 'http://www.ebi.ac.uk/efo/EFO_0005633',
 'http://www.ebi.ac.uk/efo/EFO_0005642',
 'http://www.ebi.ac.uk/efo/EFO_0005639',
 'http://www.ebi.ac.uk/efo/EFO_0005647',
 'http://www.ebi.ac.uk/efo/EFO_0005636',
 'http://www.ebi.ac.uk/efo/EFO_0005646',
 'http://www.ebi.ac.uk/efo/EFO_0005638',
 'http://www.ebi.ac.uk/efo/EFO_0005641']
```