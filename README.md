# DDIT
The Data-Driven Information Theory (DDIT, pronounced "did-it") framework is a set of useful tools for applying information theory to your data.

## Requirements
Right now, the only version of DDIT is a python class. This makes for both ease of use and ease of developement. DDIT is developed with python 3.7.3 64-bit and numpy v1.17.2 .

## Usage
The following sections describe how to use DDIT.

### Initializing DDIT
To begin, simply import DDIT.py into your python script. Once imported, create a DDIT object:
```python
# import DDIT class
from DDIT import DDIT

# create an instance of the class
ddit = DDIT()
```
### Loading Data
DDIT assumes you can provide your data in a CSV format. If you can, use the DDIT load_csv() function to load it.
```python
# load data that has no column headers
ddit.load_csv("data.csv")
```
By default, DDIT assumes there are no column headers and will load the first row as data. If your data has column headers instead use:
```python
# load data that has column headers
ddit.load_csv("data.csv", header=True)
```
Data that has been loaded is stored in DDIT.raw_data as a list of lists (RC addressable). If the header flag was set, the column titles are stored in DDIT.labels as a list of strings.
DDIT.raw_data is used as a staging ground for you to construct your random variables (hereafter also known as "columns").

### Registering Columns (Random Variables)
There are two main ways to regester random variables. The first way is to manually register them, and the second is to automatically regester them.
To manually regester a column, you can either call DDIT.register_column(),
```python
# register column 0 of raw_data as "Input_1"
ddit.register_column("Input_1", 0)
```
 or DDIT.register_column_list().
 ```python
# register column 1 of raw_data as "Input_2" via custom column construction
custom_column = [row[1] for row in ddit.raw_data]
ddit.register_column_list("Input_2", custom_column)
```
The first allows you to specify a column index of raw_data to load while the second offers you the ability to filter, concatinate, or otherwise manipulate one or several columns before regestering the final result.

If your CSV file is organized in such a way that each column *is* a random variable *and* column headers are provided, you can automatically regester each column of raw_data as a random variable. The name given to each variable is the corresponding column header.
 ```python
# load data and regester each column automatically 
ddit.load_csv("data.csv", header=True, auto_register=True)
```

### Calculating Entropies, Information, and Joint Variables
To calculate the entropy of any regestered variable:
 ```python
# Calculate the entropy of "Input_1"
e1 = ddit.H("Input_1")
```
To calculate the shared entropy (Information) between two columns:
 ```python
# Calculate The information between "Input_1" and "Input_2"
i12 = ddit.I("Input_1", "Input_2")
```
To register a joint variable:
 ```python
# register the joint variable "Input_1&Input_2"
ddit.AND("Input_1", "Input_2")
```

### Complex Entropy Formulas
Sometimes the labor required to manually regester joint variables and calculate shared entropy etc. can be too much. In this case, a function exists to calculate any arbetrary entropy formula that you can give. The acceptable input format is any formula in "standard form" which is here defined as a formula which is in the form "X:Y|Z". There are several mathematical notes to make here:
First, "X:Y|Z", "X:Y", "Y|Z", and "Z" are each examples of formulas in standard form. So is "A:B:C:D|EFGH". In general, standard form is when you express your entropy as a shared entropy (of arbetraly many variables >= 0) conditional on a joint entropy (of arbetraly many variables >= 0) and no variable appears more than once.
The formula "" or "|" is undefined (though in a data driven system would always evaluate to 0 anyway if it was).
To get DDIT to evaluate your entropy formula simply call:
 ```python
# calculate an entropy given by a formula in standard form
ddit.recursively_solve_formula("X:Y|Z")
```
To access the resulting entropy value simply:
 ```python
# the result is automatically stored in DDIT.entropies
ent = ddit.entropies["X:Y|Z"]
```

### Generating a system's Venn diagram
To generate the venn diagram of all regestered columns:
 ```python
# get the venn diagram of the entire system (all regestered columns)
ddit.solve_venn_diagram()
```
To generate the venn diagram for a specific subset of regestered columns:
 ```python
# get the venn diagram of X, Y and Z only
ddit.solve_venn_diagram(column_keys=["X","Y","Z"])
```

### Verbose mode
You can set DDIT to verbose mode when you create the object instance or at any time after to get aditional printout from many of the DDIT functions. It also enables timestamped messages. This is primarily a debugging tool for developers and end users and does not affect data processing in any way.
Usage:
 ```python
# Verbose mode on object creation
ddit = DDIT(verbose=True)
```
or
 ```python
# Verbose mode after object creation
ddit = DDIT()
ddit.verbose = True
```

### Save Memory mode
Several functions like DDIT.recursively_solve_formula() and DDIT.solve_venn_diagram() have a parameter called "save_memory" which is set to False by default. DDIT caches intermediate forms of your data to speed up computation, but this is only practical for small problem sizes. To disable this caching (reducing performance, but also reducing memory usage significantly) simply call these functions and pass the save_memory paramater as True instead.

### Alternate Entropy measures
By default DDIT calculates all entropies using the maximum-likelihood method, whereby all events' probabilities are estimated by their frequency relative to the total number of observed events. DDIT partially supports the james-stein entropy estimator. It is currently not compatable with DDIT.recursively_solve_formula() and, by extension, also not compatible with DDIT.solve_venn_diagram(). This will be fixed one day.
