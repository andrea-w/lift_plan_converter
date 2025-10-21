# lift_plan_converter
A python project that converts treadling sequences and tie-ups for floor looms to lift plans for table looms.

# Input CSV files
All of the following CSV files are required as inputs:
- Sections
- Treadling
- Tieup

Refer to the sample_inputs directory for an example of the expected format of the input files.

Note that for the treadling CSV file, sections can be repeated by using:
```
pick,section_name
1,hem x4
```

or they can be reversed by using:
```
pick,section_name
4,block reverse
```

I've included a screenshot called `original_treadling.png` in the sample_inputs folder that shows the original treadling draft I referred to when creating my sample input CSV files. 

# Project Setup

First ensure you have python and poetry installed.
At the root level of the directory, run `poetry install`. This will install all the necessary packages.

# Running the Script

Command needed to run script:

```
python weaving_liftplan.py ./sample_inputs/towel_8_sections.csv ./sample_inputs/towel_8_treadling.csv ./sample_inputs/sample_tieup.csv --shafts 8 --output annotated_plan.pdf
```

Refer to included file `annotated_plan.pdf` for the output created by the sample inputs provided.
