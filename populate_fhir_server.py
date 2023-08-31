import sys
import argparse
import json
import importlib.util
import os
from fhirclient import client
from transaction_bundles import create_transaction_bundle_object, post_transaction_bundle
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--json_file', type=str, help='JSON file for data generation to use', required=True)
parser.add_argument('--fhir_server', type=str, help='FHIR server', required=True)

args = parser.parse_args()

json_path = Path(args.json_file)

with open(json_path) as json_file: # Import data source and create instance of data source
  data_source_dict = json.load(json_file)
  module_path = Path(data_source_dict['module_path'])
  module_name = module_path.stem
  spec = importlib.util.spec_from_file_location(module_name, (json_path.parent)/module_path)
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  spec.loader.exec_module(module)
  klass = getattr(module, data_source_dict['class_name'])
  data_generator = eval('klass(**data_source_dict[\'args\'])')

fhir_server_url = args.fhir_server

smart = client.FHIRClient(settings={
  'app_id': 'my_web_app',
  'api_base': fhir_server_url
})

# Make sure the server is there
try:
  smart.server.request_json('Patient')
except BaseException as e:
  print(f"Trouble reading from the given FHIR server-- does the server exist at {fhir_server_url} ?", file=sys.stderr)
  raise

for patient in data_generator.get_all_patients():
  patient_resource = data_generator.create_patient(patient)
  try:
    response = patient_resource.create(smart.server)
  except BaseException as e:
    # Make sure to print error message in the response if there is one
    # (We caught BaseException because this could be a FHIRServer related exception or an HTTPError, but either way
    # the FHIRServer adds the response as an attribute to the exception)
    if hasattr(e, 'response') and hasattr(e.response, 'json') and callable(e.response.json):
      print("Error uploading patient {patient_row.name} to server, response json:", e.response.json(), file=sys.stderr, sep='\n')
    raise
  patient_id = response['id'] # get the patient id that was newly assigned by the fhir server
  observations = []
  for observation in data_generator.get_patient_observations(patient):
    observation_resource = data_generator.create_observation(observation, patient_id)
    observations.append(observation_resource)

  if len(observations)>0:
    transaction_bundle = create_transaction_bundle_object(observations)
    try:
      transaction_response = post_transaction_bundle(smart.server, transaction_bundle)
    except BaseException as e: # Again, make sure to print error message in the response if there is one
      if hasattr(e, 'response') and hasattr(e.response, 'json') and callable(e.response.json):
        print("Error uploading observation bundle to server, response json:", e.response.json(), file=sys.stderr, sep='\n')
    assert(len(observations) == len(transaction_response['entry'])) # There should be as many responses as resources that went in