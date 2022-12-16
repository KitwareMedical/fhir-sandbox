from data_sources.patient_data_source import PatientDataSource, Patient, Observation
import pandas as pd
 
class ExamplePatient(Patient):

  def __init__(self, patient_info):
    self.patient_info = patient_info

  def get_identifier_value(self):
    return str(self.patient_info['patient_id'])

  def get_name(self):
    split_name = self.patient_info['patient_name'].split(' ')
    return split_name[1], split_name[0]

class ExampleObservation(Observation):

  def __init__(self, observation_info):
    self.observation_info = observation_info

  def get_observation_type(self):
    return 'bodyweight'

  def get_value(self):
    return self.observation_info['body_weight_kg']

  def get_time(self):
    return self.observation_info['date']


class ExampleDataSource(PatientDataSource):

  def __init__(self, csv_file):
    self.data = pd.read_csv(csv_file)


  def get_all_patients(self):
    unique_patients = self.data.drop_duplicates('patient_id')
    return (ExamplePatient(row) for _, row in unique_patients.iterrows())

  def get_patient_observations(self, patient):
    patient_id = int(patient.get_identifier_value())
    observations_for_patient = self.data[self.data['patient_id']==patient_id]
    return (ExampleObservation(row) for _, row in observations_for_patient.iterrows())