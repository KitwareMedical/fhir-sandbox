# Creating a Custom Data Source

This tutorial will run through the process of creating a custom data source.
The complete example is in this directory, and it can be run by
```sh
python populate_fhir_server.py --json_file example/example_data_source.json --fhir_server "http://localhost:3000/hapi-fhir-jpaserver/fhir"
```
assuming that the [initial setup](../README.md#initial-setup) is complete.

## Importing Data into Python

Suppose we have some [data](example.csv) that we wish to load into a FHIR server:

| patient_id | patient_name | date | body_weight_kg |
|---|---|---|---|
| 123 | June Davis | 2022-10-30 | 80.4 |
| 123 | June Davis | 2022-12-31 | 82 |
| 123 | June Davis | 2023-05-01 | 81 |
| 456 | Lawrence Simons | 2022-11-02 | 68 |
| 456 | Lawrence Simons | 2023-01-15 | 66 |
| 789 | Steve Ireland | 2021-02-04 | 77.4 |
| 789 | Steve Ireland | 2021-04-05 | 78.6 |
| 789 | Steve Ireland | 2021-04-12 | 78.8 |
| 789 | Steve Ireland | 2021-09-07 | 79 |

There are three patients here, and there's only one type of observation: body weight.

The first step is to create a new python file in which we will define subclasses of the `PatientDataSource`, `Patient`, and `Observation` classes.
We initialized `example_data_source.py` as follows:

```python
from .patient_data_source import PatientDataSource, Patient, Observation

class ExamplePatient(Patient):
    pass

class ExampleObservation(Observation):
    pass

class ExampleDataSource(PatientDataSource):
    pass
```

The first method we will implement is the `__init__` method for `ExampleDataSource`. This
is where we will handle loading the table [example.csv](example.csv). We choose to use pandas.

```python
class ExampleDataSource(PatientDataSource):
    def __init__(self, csv_file):
        self.data = pd.read_csv(csv_file)
```

## Implementing `get_all_patients`

For a minimal implementation of a custom data source, `get_all_patients` is a simple method. The code
below shows how to create an Iterable of `ExamplePatient`.

```python
class ExampleDataSource(PatientDataSource):

    ...
    def get_all_patients(self):
        unique_patients = self.data.drop_duplicates('patient_id')
        return (ExamplePatient(row) for _, row in unique_patients.iterrows())
``` 

By writing `ExamplePatient(row)`, we have decided that a patient should be defined one of its rows from the table,
so we should now implement `ExamplePatient.__init__`.

## Implementing `ExamplePatient`

The only two methods we need to implement for `ExamplePatient` are `__init__` and `get_identifier_value`.

For `__init__`, we just need to store the patient information,
which we've chosen to represent as a row from the table (a pandas series):

```python
class ExamplePatient(Patient):
    def __init__(self, patient_info):
        self.patient_info = patient_info
```

For `get_identifier_value`, we need to return a string to identify the patient for `get_patient_observations`.
We will use the `patient_id` row since the values are unique.

```python
    def get_identifier_value(self) -> str:
        return str(self.patient_info['patient_id'])
```

This ID will get stored in the FHIR server database, but it is separate from the IDs used within the FHIR server itself.
This ID serves to link objects in the FHIR server to their origins in the data table.

For a minimal implementation of `ExamplePatient`, we will not need to implement any other methods. We will discuss
other methods we can implement later.

## Implementing `get_patient_observations`

The `get_patient_observations` method should get each observation for a given
patient. Using the `get_identifier_value` method we implemented above, the code below shows how to create
an Iterable of `ExampleObservation`

```python
class ExampleDataSource(PatientDataSource):

    ...
    def get_patient_observations(self, patient):
        patient_id = int(patient.get_identifier_value())
        observations_for_patient = self.data[self.data['patient_id']==patient_id]
        return (ExampleObservation(row) for _, row in observations_for_patient.iterrows())
```

Once again, we will need to implement the `__init__` method for `ExampleObservation`.

## Implementing `ExampleObservation`

To implement `__init__`, all we need to do is store the `row` variable passed from `get_patient_observations`:

```python
class ExampleObservation(Observation):

    ...

    def __init__(self, observation_info):
        self.observation_info = observation_info
```

The next two methods we need to implement are `get_observation_type` and `get_value`.

`get_observation_type` returns one of the supported [observation_types.json](../observation_types.json).
For this small example, we only have `bodyweight`.

```python
    def get_observation_type(self):
        return 'bodyweight'
```

`get_value` returns the actual observed value, in this case the patient weights. The code below is how
`ExampleObservation` implements `get_value`.

```python
    def get_value(self):
        return self.observation_info['body_weight_kg']
```

Note that the "bodyweight" observation type in [observation_types.json](../observation_types.json) was configured to report the units as "kg".
Since the body weights in our table are already in kg, we are good. If the weights in our table were in, say, lbs, then we would have to do one of the following:
- Convert from lbs to kg in our `ExampleObservation.get_value` so that we provide values that match the unit label, or
- Reimplement `Observation.get_unit_code` with our own `ExampleObservation.get_unit_code` that returns the unit code '[lb_av]' from the [UCUM system](https://ucum.org/). This unit code sometimes looks odd, but we can always implement `ExampleObservation.get_unit_string` to return something human readable like 'lbs'.

These are the last methods we are required to implement; however, there is one last file
we will need to create.

## Creating JSON config file

In order for `populate_fhir_server.py` to recognize `ExampleDataSource`, we need to create
a new JSON config file that contains the appropriate paths and arguments:

```json
    {
        "args":
        {
            "csv_file": "./example/example.csv"
        },
        "class_name": "ExampleDataSource",
        "module_path": "./example_data_source.py"
    }

```

- `args` are the arguements passed into the `PatientDataSource.__init__` implementation. In this example the arguments happen to be filesystem paths, and they are given relative to the expected working directory when the `populate_fhir_server_script` is executed, just because of the way `ExampleDataSource.__init__` happens to be written.
- `class_name` is the name of the `PatientDataSource` subclass.
- `module_path` is the path to the `PatientDataSource` implementation. The path here should always be _relative to the directory containing the json file_.

After following these steps, we should be able to run `populate_fhir_server.py` with the JSON config file as an argument.

## Including more data

While the previous steps created a minimal implementation, it is possible to implement more methods
to store more information on the FHIR server. Two pieces of
information stored in `example.csv` that we did not use are `patient_name` and `date`.

For `patient_name`, we can implement `get_name` in `ExamplePatient`. The code below shows a 
possible implementation.

```python
class ExamplePatient(Patient):

    ...
    
    def get_name(self) -> tuple[str, str]:
        split_name = self.patient_info['patient_name'].split(' ')
        return split_name[1], split_name[0]
```

Note that the returned tuple is in the order `last_name, first_name`,
as indicated in the `PatientDataSource.get_name` docstring.
Details like this can be checked by looking at the docstrings.

For `date`, we can implement `get_time` in `ExampleObservation`. The code below shows a
possible implementation.

```python
class ExampleObservation(Observation):

    ...
    
    def get_time(self) -> str:
        return self.observation_info['date']
```

The docstrings in [patient_data_source.py](../data_sources/patient_data_source.py) should help guide your implementation of the subclasses. If more information is needed on the precise meanings of things, check the FHIR [documentation](https://www.hl7.org/fhir/observation.html).
