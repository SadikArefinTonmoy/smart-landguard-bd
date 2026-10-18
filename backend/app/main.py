"""Smart LandGuard BD 2.0 local secure development API.

This demo deliberately does NOT talk to a government database and MUST NOT be
exposed to the public Internet as a live verification service.
"""
import os
import secrets
import re
from io import BytesIO
import uuid
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from app.auth import (
    ph, authenticate, login_retry_after, record_login_failure, clear_login_failures,
    csrf_required, create_csrf, get_current_user, login_required, login_user,
    logout_user, role_required, allowed_origins, audit_action,
)
from app.database import connect, initialize, utcnow, backend_mode
from app.crud import get_dashboard_summary, get_moderation_queue, get_property_by_id, get_purchase_checklist, list_properties
from app.document_analysis import analyze_document_for_evidence
from app.upload_safety import validate_file, MAX_FILES
from app.demo_registry import seed as seed_demo_registry, list_records, single_record, check_record, COMPARE_FIELDS
from app.private_vault import store as vault_store, accessible as vault_accessible, read_file as vault_read, delete_own as vault_delete

load_dotenv()
if os.getenv('LANDGUARD_ENV', 'development') == 'production':
    raise RuntimeError('Public production mode is intentionally blocked until PostgreSQL, HTTPS, legal access and independent security review are completed.')
app = Flask(__name__)
app.secret_key = os.environ.get('LANDGUARD_SECRET_KEY') or secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=32 * 1024 * 1024, JSON_AS_ASCII=False)
CORS(app, resources={r'/api/*': {'origins': allowed_origins()}}, supports_credentials=True, allow_headers=['Content-Type','X-CSRF-Token'])
initialize()

@app.after_request
def secure_api_response(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
    return response

@app.errorhandler(RequestEntityTooLarge)
def oversized(_error):
    return jsonify({'detail': 'Upload exceeded the 32 MB total request limit.'}), 413

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'service': 'Smart LandGuard BD 2.0 API',
                    'demo_mode': True, 'database_backend': backend_mode(), 'official_verification_available': False})

@app.route('/api/official/status', methods=['GET'])
def official_status():
    return jsonify({'connected': False, 'status': 'not_integrated',
                    'detail': 'No government data access or official document authentication is available.'})

@app.route('/api/auth/csrf', methods=['GET'])
def auth_csrf():
    response = jsonify({'csrf_token': ''})
    response.set_data(jsonify({'csrf_token': create_csrf(response)}).get_data())
    return response

@app.route('/api/auth/register', methods=['POST'])
@csrf_required
def register():
    # Demonstration only: e-mail is not verified. No claims of legal identity.
    payload = request.get_json(silent=True) or {}
    email = str(payload.get('email') or '').strip().lower()[:254]
    name = str(payload.get('name') or '').strip()[:100]
    password = str(payload.get('password') or '')
    if payload.get('accept_demo_terms') is not True:
        return jsonify({'detail': 'Confirm demo-only use and fictitious data.'}), 400
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(name)<2 or len(password)<12 or len(password)>128:
        return jsonify({'detail': 'Name, valid email and a password of 12–128 characters are required.'}), 400
    from app.auth import rate_limit_key
    _, ip_hash = rate_limit_key(email)
    cutoff = (datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(timespec='seconds')
    with connect() as db:
        count = db.execute("SELECT COUNT(*) FROM audit_events WHERE event_type=? AND result=? AND created_at>=?", ('registration', ip_hash, cutoff)).fetchone()[0]
        if count >= 3:
            return jsonify({'detail': 'Too many registrations from this connection. Try later.'}), 429
        if db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone():
            return jsonify({'detail': 'Account already exists.'}), 409
        user_id = str(uuid.uuid4())
        db.execute('INSERT INTO users(id,email,name,role,password_hash,created_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                   (user_id, email, name, 'buyer', ph.hash(password), utcnow(), utcnow()))
    # Public registration can only create Buyer accounts. Admin/Seller via CLI.
    audit_action(user_id, 'registration', ip_hash)
    return jsonify({'status':'created','role':'buyer','notice':'DEMO ONLY. Email/identity NOT verified; do not use real documents.'}), 201

@app.route('/api/auth/login', methods=['POST'])
@csrf_required
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get('email') or '').strip().lower()[:254]
    password = str(payload.get('password') or '')
    if not email or not password:
        return jsonify({'detail': 'Email and password required'}), 400
    retry_after = login_retry_after(email)
    if retry_after:
        audit_action(None, 'login', 'rate_limited')
        response = jsonify({'detail': 'Temporary login throttling is active.',
                            'retry_after_seconds': retry_after})
        response.headers['Retry-After'] = str(retry_after)
        return response, 429
    user = authenticate(email, password)
    if not user:
        record_login_failure(email)
        audit_action(None, 'login', 'failed')
        return jsonify({'detail': 'Invalid credentials'}), 401
    clear_login_failures(email)
    response = jsonify({'user_id': user['id'], 'user_role': user['role'], 'user_name': user['name']})
    login_user(response, user['id'])
    audit_action(user['id'], 'login', 'success')
    return response

@app.route('/api/auth/me', methods=['GET'])
@login_required
def auth_me():
    user = g.current_user
    return jsonify({'user_id': user['id'], 'user_role': user['role'], 'user_name': user['name'], 'email': user['email'], 'email_verified': False, 'demo_mode': True})

@app.route('/api/auth/logout', methods=['POST'])
@csrf_required
@login_required
def auth_logout():
    audit_action(g.current_user['id'], 'logout', 'success')
    return logout_user(jsonify({'status': 'logged_out'}))

@app.route('/api/auth/change-password', methods=['POST'])
@csrf_required
@login_required
def change_password():
    payload = request.get_json(silent=True) or {}
    new = str(payload.get('new_password') or '')
    old = str(payload.get('old_password') or '')
    if len(new) < 12 or len(new) > 128 or new == old:
        return jsonify({'detail': 'Choose a different password of 12–128 characters.'}), 400
    if not authenticate(g.current_user['email'], old):
        return jsonify({'detail': 'Current password is incorrect.'}), 403
    with connect() as db:
        db.execute('UPDATE users SET password_hash=?,updated_at=? WHERE id=?', (ph.hash(new), utcnow(), g.current_user['id']))
        db.execute('UPDATE sessions SET revoked_at=? WHERE user_id=?', (utcnow(), g.current_user['id']))
    audit_action(g.current_user['id'], 'change_password', 'success')
    return logout_user(jsonify({'status': 'password_changed', 'detail': 'Sign in again.'}))

@app.route('/api/privacy/me', methods=['GET'])
@login_required
def privacy_me():
    with connect() as db:
        rows = db.execute('SELECT id,purpose,evidence_status,official_check_status,input_file_count,created_at FROM verification_events WHERE user_id=? ORDER BY created_at DESC LIMIT 100', (g.current_user['id'],)).fetchall()
        requests = db.execute('SELECT id,request_type,status,created_at FROM privacy_requests WHERE user_id=? ORDER BY created_at DESC', (g.current_user['id'],)).fetchall()
        owned_file_count = db.execute('SELECT COUNT(*) FROM private_documents WHERE owner_user_id=?', (g.current_user['id'],)).fetchone()[0]
    return jsonify({'account': {k: g.current_user[k] for k in ('name','email','role')},
                    'verification_activity_metadata': [dict(r) for r in rows],
                    'privacy_requests': [dict(r) for r in requests],
                    'stored_raw_documents': False, 'stored_encrypted_demo_files': owned_file_count,
                    'storage_notice': 'Private demo uploads are encrypted and retained until deleted by their owner. Verification input files are not persisted.',
                    'official_verification_available': False})

@app.route('/api/privacy/request', methods=['POST'])
@csrf_required
@login_required
def privacy_request():
    kind = str((request.get_json(silent=True) or {}).get('type') or '')
    if kind not in ('access', 'delete'):
        return jsonify({'detail': 'Request type must be access or delete'}), 400
    cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec='seconds')
    with connect() as db:
        total = db.execute('SELECT COUNT(*) FROM privacy_requests WHERE user_id=? AND created_at>=?',
                           (g.current_user['id'], cutoff)).fetchone()[0]
    if total >= 3:
        return jsonify({'detail': 'Privacy request rate limit reached. Please try again tomorrow.'}), 429
    request_id = str(uuid.uuid4())
    with connect() as db:
        db.execute('INSERT INTO privacy_requests(id,user_id,request_type,status,created_at) VALUES (?,?,?,?,?)',
                   (request_id, g.current_user['id'], kind, 'pending_manual_review', utcnow()))
    audit_action(g.current_user['id'], 'privacy_request', kind)
    return jsonify({'request_id': request_id, 'status': 'pending_manual_review',
                    'notice': 'A request was recorded locally; a manual fulfillment workflow must be established before public launch.'}), 202

# ------- Isolated SYNTHETIC registry and owner-scoped document storage ---------
@app.route('/api/demo-registry', methods=['GET'])
@login_required
def demo_registry_list():
    q = str(request.args.get('q', ''))[:80]
    return jsonify({'records':list_records(q),'demo_mode':True,'official_verification_available':False,
      'notice':'Entirely synthetic sample registry. No official government data.'})

@app.route('/api/demo-registry/<record_id>', methods=['GET'])
@login_required
def demo_registry_detail(record_id):
    record = single_record(record_id)
    if record is None:
        return jsonify({'detail':'No sample record found'}),404
    return jsonify({'record':record,'demo_mode':True,'government_verification_performed':False})

@app.route('/api/demo-registry/check', methods=['POST'])
@csrf_required
@login_required
def demo_registry_check():
    payload = request.get_json(silent=True) or {}
    if payload.get('acknowledge_demo') is not True:
        return jsonify({'detail':'Acknowledge demo-only result.'}),400
    record_id = str(payload.get('record_id') or '')[:80]
    purpose = str(payload.get('purpose') or '')
    if purpose not in ('own_records','purchase_due_diligence','professional_review'):
        return jsonify({'detail':'Choose a purpose.'}),400
    cutoff=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(timespec='seconds')
    with connect() as db:
        count=db.execute('SELECT COUNT(*) FROM registry_checks WHERE user_id=? AND created_at>=?',(g.current_user['id'],cutoff)).fetchone()[0]
    if count>=20:
        return jsonify({'detail':'Hourly demo-check limit reached.'}),429
    supplied={k:str(payload.get(k) or '').strip()[:120] for k in COMPARE_FIELDS}
    result=check_record(g.current_user['id'],record_id,purpose,supplied)
    if result is None:
        return jsonify({'detail':'Demo record not found'}),404
    audit_action(g.current_user['id'],'demo_registry_check',result['result'])
    return jsonify(result)

@app.route('/api/demo-registry/history', methods=['GET'])
@login_required
def demo_history():
    with connect() as db:
        rows=db.execute('''SELECT id,record_id,purpose,result,matched_fields,mismatched_fields,created_at
         FROM registry_checks WHERE user_id=? ORDER BY created_at DESC LIMIT 50''',(g.current_user['id'],)).fetchall()
    import json
    return jsonify({'history':[{**dict(r),'matched_fields':json.loads(r['matched_fields']),
      'mismatched_fields':json.loads(r['mismatched_fields'])} for r in rows], 'demo_mode':True})

@app.route('/api/demo-registry/admin', methods=['POST'])
@csrf_required
@role_required('admin')
def admin_demo_record():
    body=request.get_json(silent=True) or {}
    keys=('owner_name','district','upazila','mouza','khatian','dag','land_area')
    values={key: str(body.get(key) or '').strip()[:100] for key in keys}
    if any(not value or len(value)<2 for value in values.values()):
        return jsonify({'detail':'All fictional registry fields are required.'}),400
    if body.get('confirm_fictional') is not True:
        return jsonify({'detail':'Only invented demo records are permitted.'}),400
    uid='DEMO-LR-'+uuid.uuid4().hex[:10].upper()
    with connect() as db:
        db.execute('''INSERT INTO land_records(id,owner_name,district,upazila,mouza,khatian,dag,land_area,is_demo,status,created_by,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,1,'active',?,?,?)''', (uid,*[values[k] for k in keys],g.current_user['id'],utcnow(),utcnow()))
    audit_action(g.current_user['id'],'demo_registry_create','success')
    return jsonify({'record_id':uid,'demo_mode':True,'notice':'Fictional sample record only.'}),201

@app.route('/api/demo-registry/admin/<record_id>', methods=['DELETE'])
@csrf_required
@role_required('admin')
def deactivate_demo_record(record_id):
    with connect() as db:
        row=db.execute('SELECT id FROM land_records WHERE id=? AND is_demo=1',(record_id,)).fetchone()
        if not row:
            return jsonify({'detail':'Record not found'}),404
        db.execute('UPDATE land_records SET status=?,updated_at=? WHERE id=?',('inactive',utcnow(),record_id))
    audit_action(g.current_user['id'],'demo_registry_deactivate','success')
    return jsonify({'status':'inactive','demo_mode':True})

@app.route('/api/demo-admin/summary', methods=['GET'])
@role_required('admin')
def demo_admin_summary():
    with connect() as db:
        counts={
         'registered_users':db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
         'demo_registry_records':db.execute("SELECT COUNT(*) FROM land_records WHERE status='active'").fetchone()[0],
         'private_documents':db.execute('SELECT COUNT(*) FROM private_documents').fetchone()[0],
         'demo_registry_checks':db.execute('SELECT COUNT(*) FROM registry_checks').fetchone()[0],
        }
    return jsonify({'counts':counts,'demo_mode':True,'notice':'Counts only; admin cannot view private files by default.'})

@app.route('/api/documents', methods=['GET'])
@login_required
def my_docs():
    with connect() as db:
        rows=db.execute('''SELECT id,original_filename,byte_count,label,created_at FROM private_documents
                            WHERE owner_user_id=? ORDER BY created_at DESC LIMIT 100''',(g.current_user['id'],)).fetchall()
        shared=db.execute('''SELECT d.id,d.original_filename,d.byte_count,d.label,d.created_at,g.expires_at FROM private_documents d
                   JOIN document_grants g ON g.document_id=d.id WHERE g.grantee_user_id=? AND g.revoked_at IS NULL
                   AND g.expires_at > ? ORDER BY d.created_at DESC LIMIT 100''',(g.current_user['id'],utcnow())).fetchall()
    return jsonify({'owned':[dict(r) for r in rows],'shared_with_me':[dict(r) for r in shared], 'encrypted_at_rest':True})

@app.route('/api/documents', methods=['POST'])
@csrf_required
@login_required
def upload_private_document():
    if request.form.get('demo_only')!='true' or request.form.get('authorityAttested')!='true':
        return jsonify({'detail':'Confirm demo data and authorization before upload.'}),403
    uploaded=request.files.get('document')
    if not uploaded:
        return jsonify({'detail':'Select a file.'}),400
    try:
        name,data=validate_file(uploaded)
    except ValueError as exc:
        return jsonify({'detail':str(exc)}),400
    with connect() as db:
        count=db.execute('SELECT COUNT(*) FROM private_documents WHERE owner_user_id=?',(g.current_user['id'],)).fetchone()[0]
    if count>=10:
        return jsonify({'detail':'Demo limit: 10 files per account.'}),429
    try:
        document_id=vault_store(g.current_user['id'],name,data)
    except RuntimeError:
        return jsonify({'detail':'Encrypted storage is not configured on this server.'}),503
    audit_action(g.current_user['id'],'demo_document_upload','success')
    return jsonify({'document_id':document_id,'is_demo':True,'stored_encrypted':True,
       'notice':'Private demo storage only. Do not upload real personal or official documents.'}),201

@app.route('/api/documents/<file_id>/download', methods=['GET'])
@login_required
def private_download(file_id):
    item=vault_accessible(g.current_user['id'],file_id)
    if not item:
        return jsonify({'detail':'Document not found or not authorized'}),404
    try:
        content=vault_read(item)
    except Exception:
        return jsonify({'detail':'Unable to decrypt document.'}),503
    audit_action(g.current_user['id'],'demo_document_download','success')
    response=send_file(BytesIO(content),mimetype=item['mime_type'],as_attachment=True,
               download_name=item['original_filename'],max_age=0)
    response.headers['Content-Security-Policy']="sandbox; default-src 'none'"
    return response

@app.route('/api/documents/<file_id>', methods=['DELETE'])
@csrf_required
@login_required
def delete_private_document(file_id):
    if not vault_delete(g.current_user['id'],file_id):
        return jsonify({'detail':'Only the owner may delete the document.'}),404
    audit_action(g.current_user['id'],'demo_document_delete','success')
    return jsonify({'deleted':True})

@app.route('/api/documents/<file_id>/grant', methods=['POST'])
@csrf_required
@login_required
def share_demo_document(file_id):
    body=request.get_json(silent=True) or {}
    recipient=str(body.get('recipient_email') or '').strip().lower()[:254]
    purpose=str(body.get('purpose') or '')
    if purpose not in ('purchase_due_diligence','professional_review') or body.get('confirm_demo') is not True:
        return jsonify({'detail':'Confirm a permitted demo-sharing purpose.'}),400
    with connect() as db:
        owned=db.execute('SELECT id FROM private_documents WHERE id=? AND owner_user_id=?',(file_id,g.current_user['id'])).fetchone()
        user=db.execute('SELECT id FROM users WHERE email=? AND is_active=1',(recipient,)).fetchone()
        if not owned:
            return jsonify({'detail':'Only the owner can share this document.'}),403
        if not user or user['id']==g.current_user['id']:
            return jsonify({'detail':'Recipient must be another active demo user.'}),400
        now=utcnow()
        expiry=(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat(timespec='seconds')
        current=db.execute('SELECT id FROM document_grants WHERE document_id=? AND grantee_user_id=?',(file_id,user['id'])).fetchone()
        if current:
            db.execute('''UPDATE document_grants SET expires_at=?, revoked_at=NULL, purpose=?, created_at=? WHERE id=?''',
               (expiry,purpose,now,current['id']))
        else:
            db.execute('''INSERT INTO document_grants(id,document_id,grantee_user_id,granted_by,purpose,expires_at,created_at)
                       VALUES (?,?,?,?,?,?,?)''',(str(uuid.uuid4()),file_id,user['id'],g.current_user['id'],purpose,expiry,now))
    audit_action(g.current_user['id'],'demo_document_grant','success')
    return jsonify({'status':'shared','expires_at':expiry,'demo_mode':True})

@app.route('/api/documents/<file_id>/grant', methods=['DELETE'])
@csrf_required
@login_required
def revoke_demo_document(file_id):
    with connect() as db:
        owned=db.execute('SELECT id FROM private_documents WHERE id=? AND owner_user_id=?',(file_id,g.current_user['id'])).fetchone()
        if not owned:
            return jsonify({'detail':'Only owner can revoke grants.'}),403
        db.execute('UPDATE document_grants SET revoked_at=? WHERE document_id=?',(utcnow(),file_id))
    audit_action(g.current_user['id'],'demo_document_revoke','success')
    return jsonify({'revoked':True})

@app.route("/api/properties", methods=["GET"])
@login_required
def get_properties():
    properties = list_properties()
    response = []
    for item in properties:
        response.append({
            "id": item["id"],
            "title": item["title"],
            "location": item["location"],
            "mouza": item["mouza"],
            "price": item["asking_price"],
            "status": "Sample listing",
            "risk_level": item["risk_level"],
            "verification_progress": item["verification_progress"],
        })
    return jsonify(response)


@app.route("/api/properties/<property_id>", methods=["GET"])
@login_required
def get_property(property_id: str):
    property_item = get_property_by_id(property_id)
    if not property_item:
        return jsonify({"detail": "Property not found"}), 404

    return jsonify({
        "id": property_item["id"],
        "title": property_item["title"],
        "location": property_item["location"],
        "mouza": property_item["mouza"],
        "khatian": property_item["khatian"],
        "dag": property_item["dag"],
        "area": property_item["area"],
        "asking_price": property_item["asking_price"],
        "verification_status": "Sample review — official check not performed",
        "risk_level": property_item["risk_level"],
        "evidence_summary": property_item["evidence_summary"],
        "risk_flags": property_item["risk_flags"],
    })


@app.route("/api/properties/<property_id>/purchase-checklist", methods=["GET"])
@login_required
def purchase_checklist(property_id: str):
    checklist = get_purchase_checklist(property_id)
    if not checklist:
        return jsonify({"detail": "Property not found"}), 404
    return jsonify(checklist)


@app.route("/api/moderation", methods=["GET"])
@role_required("admin")
def moderation_queue():
    return jsonify(get_moderation_queue())


@app.route("/api/dashboard", methods=["GET"])
@login_required
def dashboard():
    data = get_dashboard_summary(g.current_user['id'])
    return jsonify(data)


@app.route("/api/reports/<property_id>", methods=["GET"])
@login_required
def risk_report(property_id: str):
    property_item = get_property_by_id(property_id)
    if not property_item:
        return jsonify({"detail": "Property not found"}), 404

    recommendations = [flag["recommendation"] for flag in property_item["risk_flags"]]
    return jsonify({
        "property_id": property_item["id"],
        "report_title": f"Verification report for {property_item['title']}",
        "status": "Sample / Demo Data — Not Officially Verified",
        "summary": property_item["evidence_summary"],
        "recommendations": recommendations,
        "government_verification_performed": False,
        "notice": "Government record verification has not been performed in this prototype.",
    })


@app.route('/api/verification/extract', methods=['POST'])
@csrf_required
@login_required
def extract_document_evidence():
    user = g.current_user
    form_data = request.form.to_dict(flat=True)
    purpose = form_data.get('purpose', '')
    if purpose not in ('own_records', 'purchase_due_diligence', 'professional_review'):
        return jsonify({'detail': 'Please select a valid verification purpose.'}), 400
    if form_data.get('authorityAttested') != 'true':
        return jsonify({'detail': 'Confirm that the document was lawfully obtained and you are authorized to submit it.'}), 403
    # No third-party database retrieval. A declaration is NOT proof of ownership or consent.
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec='seconds')
    with connect() as db:
        total = db.execute('SELECT COUNT(*) FROM verification_events WHERE user_id=? AND created_at>=?',
                           (user['id'], cutoff)).fetchone()[0]
    if total >= 10:
        return jsonify({'detail': 'Maximum 10 local verification attempts per hour.'}), 429
    uploaded_files = request.files.getlist('documents')
    if not uploaded_files or len(uploaded_files) > MAX_FILES:
        return jsonify({'detail': 'Upload 1–3 supported documents for a local check.'}), 400
    validated = []
    for upload in uploaded_files:
        try:
            validated.append(validate_file(upload))
        except ValueError as exc:
            audit_action(user['id'], 'verification_upload', 'rejected')
            return jsonify({'detail': str(exc)}), 400
    user_input = {
        'propertyOwnerName': form_data.get('propertyOwnerName', '').strip()[:120],
        'mouza': form_data.get('mouza', '').strip()[:120],
        'khatianNumber': form_data.get('khatianNumber', '').strip()[:120],
        'dagNumber': form_data.get('dagNumber', '').strip()[:120],
        'landArea': form_data.get('landArea', '').strip()[:120],
    }
    comparison = {'matched': [], 'mismatched': [], 'ambiguous': [], 'not_extracted': []}
    document_results = []
    unreadable_count = 0
    for name, raw_bytes in validated:
        analysis = analyze_document_for_evidence(user_input, name, raw_bytes)
        document_results.append(analysis)
        if analysis['status'] == 'unreadable':
            unreadable_count += 1
        for field in comparison:
            for item in analysis['comparison'].get(field, []):
                comparison[field].append({**item, 'filename': name,
                    'evidence': analysis.get('field_evidence', {}).get(item['field'])})
    status = 'unreadable' if unreadable_count == len(validated) else ('partial' if unreadable_count else 'success')
    # Parsing status is not authenticity. Separate conservative, explicit review signals.
    if status == 'unreadable':
        assessment = 'unable_to_assess'
    elif comparison['mismatched']:
        assessment = 'information_mismatch_review_required'
    elif comparison['ambiguous'] or comparison['not_extracted'] or unreadable_count:
        assessment = 'incomplete_evidence_review_required'
    else:
        assessment = 'information_compared_official_check_required'

    with connect() as db:
        db.execute('INSERT INTO verification_events (id,user_id,purpose,authority_attested,input_file_count,evidence_status,created_at) VALUES (?,?,?,?,?,?,?)',
           (str(uuid.uuid4()), user['id'], purpose, 1, len(validated), status, utcnow()))
    audit_action(user['id'], 'verification_upload', status)
    return jsonify({
        'status': status, 'review_assessment': assessment, 'message': ('No readable land-record fields could be extracted.' if status == 'unreadable'
            else 'Local document text analysis complete. This is NOT official verification.'),
        **comparison, 'documents': document_results,
        'government_verification_performed': False, 'official_status': 'not_checked',
        'notice': 'Information matching cannot authenticate a deed, prove ownership or replace a government record check.',
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=False)
