# fhir-sandbox

This repository contains tools for building a prepopulated [FHIR](https://www.hl7.org/fhir/overview.html) R4 server,
intended for the construction of sandbox environments for Electronic Health
Records (EHR). `fhir-sandbox` creates a [FHIR](https://www.hl7.org/fhir/overview.html) server inside a
docker container. The FHIR server contains Patients
and Observations from a user defined data source. Currently,
a handful of observation types are supported such as heart rate and some mechanical ventilation parameters.
The full list of supported observation types can be found in [observation_types.json](observation_types.json).

## Initial Setup

1. Ensure that [Docker](https://docs.docker.com/get-docker/) and [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) are installed.
2. Clone this project.
    ```sh
    git clone git@github.com:KitwareMedical/fhir-sandbox.git
    ```
3. Install the required pacakages (python verion >= 3.9 required):
    ```sh
    pip install -r requirements.txt
    ```
4. Download the empty [hapi r4 container](https://hub.docker.com/layers/hapi-5/smartonfhir/hapi-5/r4-empty/images/sha256-42d138f85967cbcde9ed4f74d8cd57adf9f0b057e9c45ba6a8e1713d3f9e1cea?context=explore) by the SMART on FHIR team.
    ```sh
    docker pull smartonfhir/hapi-5:r4-empty
    ```
5. Run the docker container.
    ```sh
    docker run -dp 3000:8080 smartonfhir/hapi-5:r4-empty
    ```
    The port "3000" may be replaced by your choice of port; just replace appearances of "3000" by your choice in the rest of the instructions.
6. Verify that the server is working by visiting http://localhost:3000/hapi-fhir-jpaserver/fhir/Patient. This should display some json.


## Using fhir-sandbox

With the initial setup finished, there are two ways to use
`fhir-sandbox`:
1. Use one of the existing data sources, such as the random data generator used for testing, or the data source that takes NICU data from a downloaded MIMIC-III dataset.
2. Create your own `PatientDataSource` to populate custom patient and observation data into a FHIR server.

### Random data

This approach can be used to test basic functionality by populating a FHIR server with random data:

```sh
python populate_fhir_server.py --json_file ./data_sources/random.json
    --fhir_server http://localhost:3000/hapi-fhir-jpaserver/fhir/    
```

The amount of data to generate can be configured in [data_sources/random.json](data_sources/random.json).

### MIMIC-III

This approach uses a downloaded [MIMIC-III](https://physionet.org/content/mimiciii/1.4/) dataset to populate a FHIR server with NICU patients and ventilator observations. Note that the MIMIC-III dataset requires credentialed access on PhysioNet.

1. Get access to and download [MIMIC-III](https://physionet.org/content/mimiciii/1.4/).
2. Configure [data_sources/mimic3.json](data_sources/mimic3.json) to point to the location of your downloaded data and the MIMIC-III schema files:
    ```json
    "args":
    {
        "mimic3_data_dir": "path/to/mimic3/data/dir",
        "mimic3_schemas_dir": "path/to/mimic3/schema/dir"
    }
    ```
    The schema files are provided in this repository [here](mimic3-schemas).
3. Run `populate_fhir_server.py`:
    ```sh
    python populate_fhir_server.py --json_file ./data_sources/mimic3.json
    	--fhir_server http://localhost:3000/hapi-fhir-jpaserver/fhir/    
    ```


### Custom data source

To populate the FHIR server with custom data, a bit of Python is needed.
The procedure is to subclass the `PatientDataSource`, `Patient`, and `Observation` classes in [data_sources/patient_data_source.py](data_sources/patient_data_source.py), specifying how the patient and observation data should be created.

A more in-depth explanation with examples can be found [here](example/).

#### Adding Custom Observation Types

In cases where the custom data source has additional observation types
not supported in [observation_types.json](observation_types.json), it is possible to add
new observation types by simply adding an entry to [observation_types.json](observation_types.json):

```json
"ObservationTypeName":
{
    "display_string": "...",
    "unit_code": "...",
    "loinc_code": "..."
}
```
- The `display_string` is a a human readable description of the observation type, e.g. "heart rate".
- The `unit_code` describes the observation's unit of measure in the format of the [UCUM system](http://unitsofmeasure.org)
- The `loinc_code` is a [LOINC code](https://en.wikipedia.org/wiki/LOINC) identifying the observation type. You can search for LOINC codes [here](https://loinc.org/search/).

## Limitations

This tool only works with only two out of the [many types of FHIR resources](https://www.hl7.org/fhir/resourcelist.html): Patients and Observations. Extending this tool to work with other types of FHIR resources requires a more involved development effort, as well as getting friendly with the FHIR documentation.

## References

Johnson, A., Pollard, T., & Mark, R. (2016). MIMIC-III Clinical Database (version 1.4). PhysioNet. https://doi.org/10.13026/C2XW26.

## Acknowledgements

This work was supported by the National Institutes of Health under Award Number R42HL145669. The content is solely the responsibility of the authors and does not necessarily represent the official views of the National Institutes of Health.
