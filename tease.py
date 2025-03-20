from gtfs_canonical_validator import CanonicalValidator
# Code used to test the validator report locally

# File path to the gtfs zip file available locally. Change this based on the need.
file_path = 'us-california-san-francisco-bay-area-water-emergency-transportation-authority-gtfs-62.zip'
canonical_validator = CanonicalValidator(zip_file=file_path)
try:
    report = canonical_validator.validate()
    print('Report received')
    print(report.status)
    print(report.error)
except Exception as e:
    report = e
    print(report)
# print(report)
