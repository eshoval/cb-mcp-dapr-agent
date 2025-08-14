import random
import uuid
from datetime import datetime, timedelta
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions
import json

# Couchbase connection configuration
COUCHBASE_CONNECTION_STRING = "couchbase://localhost"
COUCHBASE_USERNAME = "CBadmin"  # Adjust as needed
COUCHBASE_PASSWORD = "LP2032653"       # Adjust as needed
BUCKET_NAME = "test-bucket1"

# Sample data pools for realistic generation
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra", "Donald", "Donna",
    "Steven", "Carol", "Paul", "Ruth", "Andrew", "Sharon", "Joshua", "Michelle",
    "Kenneth", "Laura", "Kevin", "Sarah", "Brian", "Kimberly", "George", "Deborah",
    "Edward", "Dorothy", "Ronald", "Lisa", "Timothy", "Nancy", "Jason", "Karen"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner"
]

TEST_TYPES = [
    "blood_test", "urine_test", "x_ray", "mri_scan", "ct_scan", "ultrasound",
    "ecg", "stress_test", "colonoscopy", "mammography", "bone_density",
    "thyroid_function", "liver_function", "kidney_function", "cholesterol_panel"
]

TEST_RESULTS = {
    "blood_test": [
        {"result_id": "hemoglobin", "result_value": lambda: f"{random.uniform(12.0, 16.0):.1f}"},
        {"result_id": "white_blood_cells", "result_value": lambda: f"{random.randint(4000, 11000)}"},
        {"result_id": "platelets", "result_value": lambda: f"{random.randint(150000, 450000)}"}
    ],
    "urine_test": [
        {"result_id": "protein", "result_value": lambda: random.choice(["negative", "trace", "positive"])},
        {"result_id": "glucose", "result_value": lambda: random.choice(["negative", "positive"])},
        {"result_id": "bacteria", "result_value": lambda: random.choice(["few", "moderate", "many"])}
    ],
    "x_ray": [
        {"result_id": "findings", "result_value": lambda: random.choice(["normal", "abnormal", "fracture detected", "no abnormalities"])}
    ],
    "thyroid_function": [
        {"result_id": "tsh", "result_value": lambda: f"{random.uniform(0.4, 4.0):.2f}"},
        {"result_id": "t4", "result_value": lambda: f"{random.uniform(4.5, 12.0):.1f}"}
    ],
    "cholesterol_panel": [
        {"result_id": "total_cholesterol", "result_value": lambda: f"{random.randint(150, 300)}"},
        {"result_id": "hdl", "result_value": lambda: f"{random.randint(30, 80)}"},
        {"result_id": "ldl", "result_value": lambda: f"{random.randint(70, 200)}"}
    ]
}

MEDICINES = [
    "ACAMOL", "ADVIL", "ASPIRIN", "TYLENOL", "IBUPROFEN", "METFORMIN", "LISINOPRIL",
    "AMLODIPINE", "METOPROLOL", "OMEPRAZOLE", "SIMVASTATIN", "LOSARTAN", "HYDROCHLOROTHIAZIDE",
    "ATORVASTATIN", "AZITHROMYCIN", "AMOXICILLIN", "PREDNISONE", "GABAPENTIN", "SERTRALINE",
    "CLOPIDOGREL", "MONTELUKAST", "ROSUVASTATIN", "ESCITALOPRAM", "PANTOPRAZOLE", "WARFARIN"
]

def generate_patient_id():
    """Generate a unique 9-digit patient ID"""
    return f"{random.randint(100000000, 999999999)}"

def generate_birth_year():
    """Generate realistic birth year (ages 18-90)"""
    current_year = datetime.now().year
    return random.randint(current_year - 90, current_year - 18)

def generate_test_date():
    """Generate test date within the last 2 years"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    random_date = start_date + timedelta(days=random.randint(0, 730))
    return random_date.strftime("%Y-%m-%d")

def generate_prescription_date():
    """Generate prescription date within the last year"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    random_date = start_date + timedelta(days=random.randint(0, 365))
    return random_date.strftime("%Y-%m-%d")

def generate_test_results(test_type):
    """Generate realistic test results based on test type"""
    if test_type in TEST_RESULTS:
        results = []
        for result_template in TEST_RESULTS[test_type]:
            result = {
                "result_id": result_template["result_id"],
                "result_value": result_template["result_value"]() if callable(result_template["result_value"]) else result_template["result_value"]
            }
            results.append(result)
        return results
    else:
        # Default result for test types not in our predefined list
        return [{"result_id": "status", "result_value": random.choice(["normal", "abnormal", "pending"])}]

def generate_patients(count=100):
    """Generate patient documents"""
    patients = []
    used_ids = set()
    
    for _ in range(count):
        # Ensure unique patient ID
        patient_id = generate_patient_id()
        while patient_id in used_ids:
            patient_id = generate_patient_id()
        used_ids.add(patient_id)
        
        patient = {
            "type": "patient",
            "id": patient_id,
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "gender": random.choice(["male", "female"]),
            "birth_date_year": generate_birth_year()
        }
        patients.append(patient)
    
    return patients

def generate_tests(patients):
    """Generate test documents for patients"""
    tests = []
    
    for patient in patients:
        # Each patient gets 0-5 tests
        num_tests = random.randint(0, 5)
        
        for i in range(num_tests):
            test_type = random.choice(TEST_TYPES)
            test = {
                "type": "test",
                "id": f"t{uuid.uuid4().hex[:8]}",  # Generate unique test ID
                "patient_id": patient["id"],
                "test_type": test_type,
                "result_date": generate_test_date(),
                "results": generate_test_results(test_type)
            }
            tests.append(test)
    
    return tests

def generate_prescriptions(patients):
    """Generate prescription documents for patients"""
    prescriptions = []
    
    for patient in patients:
        # Each patient gets 0-3 prescriptions
        num_prescriptions = random.randint(0, 3)
        
        for i in range(num_prescriptions):
            prescription = {
                "type": "prescription",
                "largo_code": f"{random.randint(10000, 99999)}",
                "patient_id": patient["id"],
                "medicine_name": random.choice(MEDICINES),
                "quantity": random.choice([10, 20, 30, 60, 90]),
                "valid_from": generate_prescription_date()
            }
            prescriptions.append(prescription)
    
    return prescriptions

def connect_to_couchbase():
    """Establish connection to Couchbase"""
    try:
        # Configure authentication
        auth = PasswordAuthenticator(COUCHBASE_USERNAME, COUCHBASE_PASSWORD)
        
        # Connect to cluster
        cluster = Cluster(COUCHBASE_CONNECTION_STRING, ClusterOptions(auth))
        
        # Get bucket
        bucket = cluster.bucket(BUCKET_NAME)
        collection = bucket.default_collection()
        
        return collection
    except Exception as e:
        print(f"Error connecting to Couchbase: {e}")
        return None

def insert_documents(collection, documents, doc_type):
    """Insert documents into Couchbase collection"""
    success_count = 0
    error_count = 0
    
    print(f"Inserting {len(documents)} {doc_type} documents...")
    
    for doc in documents:
        try:
            # Use the document ID as the key
            key = f"{doc_type}_{doc['id']}"
            collection.insert(key, doc)
            success_count += 1
            
            if success_count % 10 == 0:
                print(f"Inserted {success_count} {doc_type} documents...")
                
        except Exception as e:
            print(f"Error inserting {doc_type} document {doc['id']}: {e}")
            error_count += 1
    
    print(f"Completed {doc_type} insertion: {success_count} successful, {error_count} errors")
    return success_count, error_count

def generate_and_insert_test_data():
    """Main function to generate and insert all test data"""
    print("=== Couchbase Test Data Generator ===")
    print(f"Target bucket: {BUCKET_NAME}")
    print(f"Generating data for 100 patients...")
    
    # Connect to Couchbase
    collection = connect_to_couchbase()
    if not collection:
        print("Failed to connect to Couchbase. Please check your configuration.")
        return
    
    # Generate data
    print("\n1. Generating patients...")
    patients = generate_patients(100)
    print(f"Generated {len(patients)} patients")
    
    print("\n2. Generating tests...")
    tests = generate_tests(patients)
    print(f"Generated {len(tests)} tests")
    
    print("\n3. Generating prescriptions...")
    prescriptions = generate_prescriptions(patients)
    print(f"Generated {len(prescriptions)} prescriptions")
    
    # Insert data into Couchbase
    print("\n=== Inserting Data into Couchbase ===")
    
    # Insert patients
    patient_success, patient_errors = insert_documents(collection, patients, "patient")
    
    # Insert tests
    test_success, test_errors = insert_documents(collection, tests, "test")
    
    # Insert prescriptions
    prescription_success, prescription_errors = insert_documents(collection, prescriptions, "prescription")
    
    # Summary
    print("\n=== Summary ===")
    print(f"Patients: {patient_success} inserted, {patient_errors} errors")
    print(f"Tests: {test_success} inserted, {test_errors} errors")
    print(f"Prescriptions: {prescription_success} inserted, {prescription_errors} errors")
    print(f"Total documents: {patient_success + test_success + prescription_success}")

def preview_sample_data():
    """Preview sample data without inserting into database"""
    print("=== Sample Data Preview ===")
    
    # Generate small sample
    patients = generate_patients(3)
    tests = generate_tests(patients)
    prescriptions = generate_prescriptions(patients)
    
    sample_data = {
        "patients": patients,
        "tests": tests,
        "prescriptions": prescriptions
    }
    
    print(json.dumps(sample_data, indent=2))

if __name__ == "__main__":
    # Uncomment the line below to preview sample data
    # preview_sample_data()
    
    # Generate and insert test data
    generate_and_insert_test_data()