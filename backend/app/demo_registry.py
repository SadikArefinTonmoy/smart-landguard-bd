"""Fully fabricated registry rows; NOT government records or title evidence."""
import json
import uuid
from datetime import datetime, timedelta, timezone
from app.database import connect, utcnow
from app.document_analysis import is_field_match

# Artificial names, locations and identifiers. None denotes a real owner's record.
SYNTHETIC = [
    ('DEMO-LR-1001', 'Demo Owner Alpha', 'Dhaka', 'Demo Upazila A', 'Sample Mouza A', 'DEMO-KH-101', 'DEMO-DAG-01', '5 decimal'),
    ('DEMO-LR-1002', 'Demo Owner Beta', 'Gazipur', 'Demo Upazila B', 'Sample Mouza B', 'DEMO-KH-102', 'DEMO-DAG-02', '7 decimal'),
    ('DEMO-LR-1003', 'Demo Owner Gamma', 'Pabna', 'Demo Upazila C', 'Sample Mouza C', 'DEMO-KH-103', 'DEMO-DAG-03', '3 decimal'),
    ('DEMO-LR-1004', 'Demo Owner Delta', 'Rajshahi', 'Demo Upazila D', 'Sample Mouza D', 'DEMO-KH-104', 'DEMO-DAG-04', '4 decimal'),
    ('DEMO-LR-1005', 'Demo Owner Epsilon', 'Khulna', 'Demo Upazila E', 'Sample Mouza E', 'DEMO-KH-105', 'DEMO-DAG-05', '2 decimal'),
    ('DEMO-LR-1006', 'Demo Owner Zeta', 'Barishal', 'Demo Upazila F', 'Sample Mouza F', 'DEMO-KH-106', 'DEMO-DAG-06', '8 decimal'),
    ('DEMO-LR-1007', 'Demo Owner Eta', 'Cumilla', 'Demo Upazila G', 'Sample Mouza G', 'DEMO-KH-107', 'DEMO-DAG-07', '6 decimal'),
    ('DEMO-LR-1008', 'Demo Owner Theta', 'Bogura', 'Demo Upazila H', 'Sample Mouza H', 'DEMO-KH-108', 'DEMO-DAG-08', '1 decimal'),
    ('DEMO-LR-1009', 'Demo Owner Iota', 'Rangpur', 'Demo Upazila I', 'Sample Mouza I', 'DEMO-KH-109', 'DEMO-DAG-09', '9 decimal'),
    ('DEMO-LR-1010', 'Demo Owner Kappa', 'Sylhet', 'Demo Upazila J', 'Sample Mouza J', 'DEMO-KH-110', 'DEMO-DAG-10', '5 decimal'),
    ('DEMO-LR-1011', 'Demo Owner Lambda', 'Mymensingh', 'Demo Upazila K', 'Sample Mouza K', 'DEMO-KH-111', 'DEMO-DAG-11', '3 decimal'),
    ('DEMO-LR-1012', 'Demo Owner Mu', 'Chattogram', 'Demo Upazila L', 'Sample Mouza L', 'DEMO-KH-112', 'DEMO-DAG-12', '4 decimal'),
]
PUBLIC_FIELDS = ('id','owner_name','district','upazila','mouza','khatian','dag','land_area','status','created_at')
COMPARE_FIELDS = {'owner_name':'owner_name', 'district':'district', 'mouza':'mouza', 'khatian':'khatian', 'dag':'dag', 'land_area':'land_area'}

def seed():
    count = 0
    with connect() as db:
        for sample in SYNTHETIC:
            exists = db.execute('SELECT id FROM land_records WHERE id=?', (sample[0],)).fetchone()
            if exists:
                continue
            db.execute('''INSERT INTO land_records (id,owner_name,district,upazila,mouza,khatian,dag,land_area,is_demo,status,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,1,'active',?,?)''', (*sample, utcnow(),utcnow()))
            count += 1
    return count

def list_records(q=''):
    with connect() as db:
        rows = db.execute('''SELECT id,owner_name,district,upazila,mouza,khatian,dag,land_area,status,created_at
                          FROM land_records WHERE is_demo=1 AND status='active' ORDER BY id LIMIT 100''').fetchall()
    term = q.strip().casefold()[:80]
    records = [dict(row) for row in rows]
    result = [record for record in records if not term or any(term in str(value).casefold() for value in record.values())]
    return result[:30]

def single_record(record_id):
    with connect() as db:
        row = db.execute('''SELECT id,owner_name,district,upazila,mouza,khatian,dag,land_area,status,created_at
                           FROM land_records WHERE id=? AND is_demo=1 AND status='active' ''', (record_id,)).fetchone()
    return dict(row) if row else None

def check_record(user_id, record_id, purpose, supplied):
    record = single_record(record_id)
    if not record:
        return None
    matched, mismatched, unprovided = [], [], []
    for key in COMPARE_FIELDS:
        value = str(supplied.get(key, '')).strip()
        if not value:
            unprovided.append(key)
        elif is_field_match(value, str(record[key])):
            matched.append(key)
        else:
            mismatched.append(key)
    # Never treat a partly filled form as a complete synthetic-record match.
    if not (matched or mismatched):
        result = 'insufficient_data'
    elif mismatched:
        result = 'demo_mismatch'
    elif unprovided:
        result = 'incomplete_demo_check'
    else:
        result = 'demo_match'
    ident = str(uuid.uuid4())
    with connect() as db:
        db.execute('''INSERT INTO registry_checks(id,user_id,record_id,purpose,result,matched_fields,mismatched_fields,created_at)
                    VALUES (?,?,?,?,?,?,?,?)''', (ident,user_id,record_id,purpose,result,json.dumps(matched),json.dumps(mismatched),utcnow()))
    return {'check_id':ident,'record_id':record_id,'result':result,'matched_fields':matched,
            'mismatched_fields':mismatched,'unprovided_fields':unprovided,'is_demo':True,
            'government_verification_performed':False,
            'notice':'DEMO DATA ONLY. A match DOES NOT prove document authenticity, ownership or government verification.'}
