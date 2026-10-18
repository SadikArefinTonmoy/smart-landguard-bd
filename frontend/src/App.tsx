import { useEffect, useRef, useState } from 'react';
import heroLandscape from './assets/bangladesh-rural-landscape.jpg';
import bangladeshOutline from './assets/bangladesh-outline.svg';

type Property = {
  id: string;
  title: string;
  location: string;
  mouza?: string;
  price: string;
  status: string;
  risk_level: string;
  verification_progress: number;
};

type RiskFlag = {
  title: string;
  severity: string;
  evidence: string;
  source: string;
  recommendation: string;
  requires_human_review: boolean;
};

type PropertyDetail = {
  id: string;
  title: string;
  location: string;
  mouza: string;
  khatian: string;
  dag: string;
  area: string;
  asking_price: string;
  verification_status: string;
  risk_level: string;
  evidence_summary: string;
  risk_flags: RiskFlag[];
};

type ReportSummary = {
  property_id: string;
  report_title: string;
  status: string;
  summary: string;
  recommendations: string[];
};

type PurchaseChecklistStep = {
  id: string;
  title: string;
  status: 'done' | 'in_progress' | 'pending';
  detail: string;
  urgency: string;
};

type PurchaseChecklist = {
  property_id: string;
  title: string;
  overall_status: string;
  progress: number;
  checklist: PurchaseChecklistStep[];
};

type ModerationItem = {
  id: string;
  property_id: string;
  title: string;
  status: string;
  priority: string;
  reason: string;
  reviewer: string;
  updated_at: string;
};

type DemoRegistryRecord = {
  id: string; owner_name: string; district: string; upazila: string; mouza: string;
  khatian: string; dag: string; land_area: string; status: string;
};
type DemoHistory = { id: string; record_id: string; result: string; purpose: string; created_at: string; matched_fields: string[]; mismatched_fields: string[]; };
type PrivateDocument = { id: string; original_filename: string; byte_count: number; created_at: string; expires_at?: string; };

type AuthSession = {
  user_id?: string;
  user_role: 'buyer' | 'seller' | 'admin';
  user_name: string;
};

type DashboardStat = {
  label: string;
  value: number;
};

type VerificationFormData = {
  propertyName: string;
  ownerName: string;
  district: string;
  upazila: string;
  mouza: string;
  khatianNumber: string;
  dagNumber: string;
  landArea: string;
  documents: File[];
};

type VerificationComparisonItem = {
  field: string;
  value?: string;
  expected?: string;
  actual?: string;
  filename?: string;
  evidence?: string;
  reason?: string;
  normalized?: string;
  normalized_expected?: string;
  normalized_actual?: string;
};

type VerificationDocumentAnalysis = {
  status: string;
  review_assessment?: string;
  message: string;
  matched: VerificationComparisonItem[];
  mismatched: VerificationComparisonItem[];
  ambiguous: VerificationComparisonItem[];
  not_extracted: VerificationComparisonItem[];
  documents: Array<{
    filename: string;
    status: string;
    message: string;
    extracted_fields: Record<string, string | null>;
    field_evidence?: Record<string, string>;
  }>;
};

type VerificationResult = {
  propertyName: string;
  ownerName: string;
  district: string;
  upazila: string;
  mouza: string;
  khatianNumber: string;
  dagNumber: string;
  landArea: string;
  uploadedDocuments: string[];
  missingEvidence: string[];
  possibleInconsistencies: string[];
  riskWarnings: string[];
  recommendedNextSteps: string[];
  documentComparison?: VerificationDocumentAnalysis | null;
};

type VerificationTextField =
  | 'propertyName'
  | 'ownerName'
  | 'district'
  | 'upazila'
  | 'mouza'
  | 'khatianNumber'
  | 'dagNumber'
  | 'landArea';

const featureCards = [
  {
    icon: 'deed',
    title: 'দ্রুত দলিল যাচাই',
    description: 'নির্ভরযোগ্য তথ্য দ্রুত ও নিরাপদভাবে যাচাই করুন',
    englishTitle: 'Fast deed verification',
    englishDescription: 'Verify reliable information quickly and safely.',
  },
  {
    icon: 'shield',
    title: 'ঝুঁকি শনাক্তকরণ',
    description: 'জালিয়াতি ও গরমিলের ঝুঁকি আগেই জানুন',
    englishTitle: 'Risk detection',
    englishDescription: 'Identify fraud and inconsistencies early.',
  },
  {
    icon: 'location',
    title: 'মৌজা ও খতিয়ান তথ্য',
    description: 'মৌজা, দাগ ও খতিয়ানের তথ্য সাজিয়ে দেখুন',
    englishTitle: 'Mouza and khatian information',
    englishDescription: 'Review organized mouza, plot, and khatian details.',
  },
  {
    icon: 'report',
    title: 'বিশদ প্রতিবেদন',
    description: 'সম্পূর্ণ যাচাই প্রতিবেদন ডাউনলোড করুন',
    englishTitle: 'Detailed reports',
    englishDescription: 'Download a complete verification report.',
  },
];

// All browser requests share the website origin; Vite proxies /api to local Flask.
const apiBase = '/api';
const sampleDataNotice = 'Sample / Demo Data';
const governmentVerificationNotice = 'Government record verification has not been performed in this prototype.';

const demoProperties: Property[] = [
  {
    id: 'DEMO-1001',
    title: 'North View Land Plot',
    location: 'Pabna Sadar, Pabna',
    price: 'BDT 48,00,000',
    status: 'Demo listing',
    risk_level: 'Additional verification recommended',
    verification_progress: 68,
  },
  {
    id: 'DEMO-1002',
    title: 'Green Valley Parcel',
    location: 'Gazipur Sadar, Gazipur',
    price: 'BDT 39,00,000',
    status: 'Demo listing',
    risk_level: 'Significant unresolved concern',
    verification_progress: 54,
  },
  {
    id: 'DEMO-1003',
    title: 'River Edge Plot',
    location: 'Chandpur Sadar, Chandpur',
    price: 'BDT 52,00,000',
    status: 'Demo listing',
    risk_level: 'No issue identified in available checks',
    verification_progress: 82,
  },
];

const defaultStats: DashboardStat[] = [
  { label: 'Properties viewed', value: 0 },
  { label: 'Saved properties', value: 0 },
  { label: 'Verification requests', value: 0 },
  { label: 'Completed checks', value: 0 },
  { label: 'Pending checks', value: 0 },
  { label: 'Unresolved issues', value: 0 },
];

const demoPropertyDetails: Record<string, PropertyDetail> = {
  'DEMO-1001': {
    id: 'DEMO-1001',
    title: 'North View Land Plot',
    location: 'Pabna Sadar, Pabna',
    mouza: 'Bharatpur',
    khatian: 'K-221/445',
    dag: 'Dag 18',
    area: '1.26 bigha',
    asking_price: 'BDT 48,00,000',
    verification_status: 'Partial evidence',
    risk_level: 'Additional verification recommended',
    evidence_summary: 'This demo record includes deed and tax evidence, but the mutation record and name consistency still require review before any buyer decision.',
    risk_flags: [
      {
        title: 'Name mismatch in deed and khatian',
        severity: 'High',
        evidence: 'The uploaded deed and khatian show inconsistent buyer or owner names in this sample review.',
        source: 'Sample document comparison',
        recommendation: 'Request identity proof and compare against the mutation record before continuing.',
        requires_human_review: true,
      },
      {
        title: 'Mutation record missing',
        severity: 'Medium',
        evidence: 'No mutation approval record is attached in this demo review.',
        source: 'Sample checklist review',
        recommendation: 'Collect the mutation document and confirm approval status with a qualified reviewer.',
        requires_human_review: true,
      },
    ],
  },
  'DEMO-1002': {
    id: 'DEMO-1002',
    title: 'Green Valley Parcel',
    location: 'Gazipur Sadar, Gazipur',
    mouza: 'Madhabdi',
    khatian: 'K-545/112',
    dag: 'Dag 9',
    area: '0.92 bigha',
    asking_price: 'BDT 39,00,000',
    verification_status: 'Awaiting mutation proof',
    risk_level: 'Significant unresolved concern',
    evidence_summary: 'The sample documents are partly consistent, but the ownership chain and mutation evidence remain incomplete in this demo scenario.',
    risk_flags: [
      {
        title: 'Ownership chain incomplete',
        severity: 'High',
        evidence: 'A gap appears between the last known transfer and the current deed holder in this fictional record.',
        source: 'Sample timeline review',
        recommendation: 'Ask for the full transfer chain and verify any missing legal documents with a professional reviewer.',
        requires_human_review: true,
      },
      {
        title: 'Possible case reference in demo dataset',
        severity: 'Medium',
        evidence: 'This fictional dataset flags a prior dispute reference matching the land location.',
        source: 'Sample risk screening',
        recommendation: 'Review the case reference and confirm whether the issue was resolved before purchase.',
        requires_human_review: true,
      },
    ],
  },
  'DEMO-1003': {
    id: 'DEMO-1003',
    title: 'River Edge Plot',
    location: 'Chandpur Sadar, Chandpur',
    mouza: 'Madhya Char',
    khatian: 'K-812/300',
    dag: 'Dag 12',
    area: '1.45 bigha',
    asking_price: 'BDT 52,00,000',
    verification_status: 'Document review in progress',
    risk_level: 'No issue identified in available checks',
    evidence_summary: 'The sample record shows no major inconsistency in the available documents, but mutation confirmation and final professional review are still recommended.',
    risk_flags: [
      {
        title: 'No major inconsistency found in available documents',
        severity: 'Low',
        evidence: 'The deed, khatian, and tax records are consistent in this demo example.',
        source: 'Sample consistency review',
        recommendation: 'Continue with a final mutation check and legal review before completing the purchase.',
        requires_human_review: false,
      },
    ],
  },
};

const maxDocumentSizeBytes = 10 * 1024 * 1024;
const allowedDocumentTypes = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

const createEmptyVerificationForm = (): VerificationFormData => ({
  propertyName: '',
  ownerName: '',
  district: '',
  upazila: '',
  mouza: '',
  khatianNumber: '',
  dagNumber: '',
  landArea: '',
  documents: [],
});

const validateVerificationStepOne = (form: VerificationFormData, language: 'bn' | 'en') => {
  const errors: Record<string, string> = {};
  const requiredMessage = (field: string, translatedField: string) =>
    language === 'bn' ? `${translatedField} আবশ্যক।` : `${field} is required.`;

  if (!form.propertyName.trim()) {
    errors.propertyName = requiredMessage('Property name', 'সম্পত্তির নাম');
  }

  if (!form.district.trim()) {
    errors.district = requiredMessage('District', 'জেলা');
  }

  if (!form.upazila.trim()) {
    errors.upazila = requiredMessage('Upazila', 'উপজেলা');
  }

  if (!form.mouza.trim()) {
    errors.mouza = requiredMessage('Mouza', 'মৌজা');
  }

  if (!form.khatianNumber.trim()) {
    errors.khatianNumber = requiredMessage('Khatian number', 'খতিয়ান নম্বর');
  }

  if (!form.dagNumber.trim()) {
    errors.dagNumber = requiredMessage('Dag number', 'দাগ নম্বর');
  }

  if (!form.landArea.trim()) {
    errors.landArea = requiredMessage('Land area', 'জমির পরিমাণ');
  }

  return errors;
};

const buildVerificationResult = (form: VerificationFormData): VerificationResult => {
  const missingEvidence: string[] = [];
  const recommendedNextSteps: string[] = [];
  if (!form.documents.length) missingEvidence.push('No supporting document was uploaded.');
  if (!form.ownerName.trim()) missingEvidence.push('Owner name was not provided.');
  if (!form.documents.length) recommendedNextSteps.push('Upload a readable deed or khatian to compare with the entered information.');
  else recommendedNextSteps.push('Review extracted fields against the information entered in the form.');
  return {
    propertyName: form.propertyName.trim() || 'Not provided',
    ownerName: form.ownerName.trim() || 'Not provided',
    district: form.district.trim() || 'Not provided',
    upazila: form.upazila.trim() || 'Not provided',
    mouza: form.mouza.trim() || 'Not provided',
    khatianNumber: form.khatianNumber.trim() || 'Not provided',
    dagNumber: form.dagNumber.trim() || 'Not provided',
    landArea: form.landArea.trim() || 'Not provided',
    uploadedDocuments: form.documents.map((file) => file.name),
    missingEvidence,
    possibleInconsistencies: [],
    riskWarnings: [],
    recommendedNextSteps,
  };
};

// Localized evidence statements are never replaced by a generic government warning.
const verificationTranslations: Record<string, string> = {
  'No supporting document was uploaded.': 'তুলনার জন্য কোনো সহায়ক নথি আপলোড করা হয়নি।',
  'Owner name was not provided.': 'মালিকের নাম দেওয়া হয়নি; নামের মিল পরীক্ষা করা সম্ভব নয়।',
  'Upload a readable deed or khatian to compare with the entered information.': 'তুলনা করার জন্য একটি পাঠযোগ্য দলিল বা খতিয়ান আপলোড করুন।',
  'Review extracted fields against the information entered in the form.': 'উদ্ধার করা তথ্য ফর্মে দেওয়া তথ্যের সঙ্গে মিলিয়ে দেখুন।',
  'One or more uploaded documents could not be read locally. Please upload a clearer scan or a text-based file.': 'এক বা একাধিক নথি পড়া যায়নি। পরিষ্কার স্ক্যান বা লেখা-সমর্থিত ফাইল দিন।',
  'Mismatched details require manual review; do not rely on this report for a purchase.': 'উদ্ধার করা তথ্যের সঙ্গে অমিল পাওয়া গেছে; সিদ্ধান্তের আগে ম্যানুয়াল পর্যালোচনা প্রয়োজন।',
  'No document analysis result was returned. The uploaded files were not processed by the local extraction endpoint.': 'নথি বিশ্লেষণের ফল পাওয়া যায়নি; ফাইলগুলো প্রক্রিয়াকরণ সম্পন্ন হয়নি।',
};
const verificationFieldNamesBn: Record<string, string> = {
  owner_name: 'মালিকের নাম', district: 'জেলা', upazila: 'উপজেলা', mouza: 'মৌজা',
  khatian_number: 'খতিয়ান নম্বর', dag_number: 'দাগ নম্বর', land_area: 'জমির পরিমাণ',
};
const translateVerificationMessage = (value: string, language: 'bn' | 'en'): string => {
  if (language === 'en') return value;
  if (verificationTranslations[value]) return verificationTranslations[value];
  const fieldMismatch = value.match(/^Field mismatch: (.+?) expected (.+?) but found (.+)\.$/);
  if (fieldMismatch) return `${verificationFieldNamesBn[fieldMismatch[1]] || fieldMismatch[1]}: ফর্মে দেওয়া তথ্য “${fieldMismatch[2]}”, নথিতে পাওয়া তথ্য “${fieldMismatch[3]}” — মিলছে না।`;
  const notExtracted = value.match(/^(.+?) could not be extracted from uploaded evidence\.$/);
  if (notExtracted) return `আপলোড করা নথি থেকে “${verificationFieldNamesBn[notExtracted[1].replace(/ /g, '_')] || notExtracted[1]}” তথ্য উদ্ধার করা যায়নি।`;
  return value;
};

function App() {
  const [language, setLanguage] = useState<'bn' | 'en'>('bn');
  const text = (english: string, bengali: string) => (language === 'bn' ? bengali : english);
  const localizeMessage = (message: string, translations: Record<string, string>) =>
    language === 'bn' ? translations[message] ?? message : message;
  const [properties, setProperties] = useState<Property[]>(demoProperties);
  const [stats, setStats] = useState<DashboardStat[]>(defaultStats);
  const [selectedId, setSelectedId] = useState<string>('DEMO-1001');
  const [detail, setDetail] = useState<PropertyDetail | null>(null);
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [purchaseChecklist, setPurchaseChecklist] = useState<PurchaseChecklist | null>(null);
  const [moderationQueue, setModerationQueue] = useState<ModerationItem[]>([]);
  const [search, setSearch] = useState('');
  const [filterRisk, setFilterRisk] = useState('all');
  const [showSampleSearch, setShowSampleSearch] = useState(false);
  const [showPropertyDetail, setShowPropertyDetail] = useState(false);
  const [activeNav, setActiveNav] = useState('home');
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(true);
  const [apiError, setApiError] = useState<string>('');
  const [detailError, setDetailError] = useState<string>('');
  const [dataMode, setDataMode] = useState<'live' | 'demo'>('demo');
  const [verificationOpen, setVerificationOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginPending, setLoginPending] = useState(false);
  const [sessionChecking, setSessionChecking] = useState(true);
  const [loginRetrySeconds, setLoginRetrySeconds] = useState(0);
  const [verificationPurpose, setVerificationPurpose] = useState('purchase_due_diligence');
  const [authorityAttested, setAuthorityAttested] = useState(false);
  const [privacyStatus, setPrivacyStatus] = useState('');
  const csrfForWrite = async (): Promise<string> => {
    const response = await fetch(`${apiBase}/auth/csrf`, { credentials: 'include', cache: 'no-store' });
    if (!response.ok) throw new Error('csrf_failed');
    const data: { csrf_token: string } = await response.json();
    return data.csrf_token;
  };
  const [registerMode, setRegisterMode] = useState(false);
  const [registerName, setRegisterName] = useState('');
  const [acceptDemoTerms, setAcceptDemoTerms] = useState(false);
  const [registry, setRegistry] = useState<DemoRegistryRecord[]>([]);
  const [registryHistory, setRegistryHistory] = useState<DemoHistory[]>([]);
  const [extractionHistory, setExtractionHistory] = useState<{id:string;purpose:string;evidence_status:string;created_at:string}[]>([]);
  const [registrySearch, setRegistrySearch] = useState('');
  const [showAllAdminRecords, setShowAllAdminRecords] = useState(false);
  const [vaultOwned, setVaultOwned] = useState<PrivateDocument[]>([]);
  const [vaultShared, setVaultShared] = useState<PrivateDocument[]>([]);
  const [demoStatus, setDemoStatus] = useState('');
  const [currentDemoResult, setCurrentDemoResult] = useState<string | null>(null);
  const [showSavedDemoHistory, setShowSavedDemoHistory] = useState(false);
  const [selectedDemoRecord, setSelectedDemoRecord] = useState('');
  const [demoValues, setDemoValues] = useState({owner_name:'',district:'',mouza:'',khatian:'',dag:'',land_area:''});
  const [demoShareEmail, setDemoShareEmail] = useState('');
  const [adminRecord, setAdminRecord] = useState({owner_name:'',district:'',upazila:'',mouza:'',khatian:'',dag:'',land_area:''});
  const [adminSummary, setAdminSummary] = useState<Record<string, number> | null>(null);
  const [selectedVaultFile, setSelectedVaultFile] = useState<File | null>(null);
  const [vaultConsent, setVaultConsent] = useState(false);
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [headerCompact, setHeaderCompact] = useState(false);
  const loginDialogRef = useRef<HTMLElement>(null);
  const loginCloseButtonRef = useRef<HTMLButtonElement>(null);
  const [verificationStep, setVerificationStep] = useState(1);
  const [verificationForm, setVerificationForm] = useState<VerificationFormData>(createEmptyVerificationForm());
  const [verificationErrors, setVerificationErrors] = useState<Record<string, string>>({});
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [extractionLoading, setExtractionLoading] = useState(false);
  const [extractionError, setExtractionError] = useState<string>('');
  const [reportExportMessage, setReportExportMessage] = useState<string>('');

  useEffect(() => {
    const navSections = authSession
      ? ['home', 'features', 'verification', 'dashboard', 'my-documents', 'reports']
      : ['home', 'features', 'help'];
    const updateHeaderAndActiveSection = () => {
      setHeaderCompact(window.scrollY > 65);
      const offset = window.scrollY + 155;
      let current = 'home';
      for (const id of navSections) {
        const element = document.getElementById(id);
        if (element && element.getBoundingClientRect().top + window.scrollY <= offset) current = id;
      }
      setActiveNav(current);
    };
    updateHeaderAndActiveSection();
    window.addEventListener('scroll', updateHeaderAndActiveSection, { passive: true });
    window.addEventListener('hashchange', updateHeaderAndActiveSection);
    return () => {
      window.removeEventListener('scroll', updateHeaderAndActiveSection);
      window.removeEventListener('hashchange', updateHeaderAndActiveSection);
    };
  }, [authSession]);

  // Session identifier stays only in an HttpOnly cookie, never in browser storage.
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${apiBase}/auth/me`, { credentials: 'include', signal: controller.signal })
      .then((response) => response.ok ? response.json() : null)
      .then((user: AuthSession | null) => { if (!controller.signal.aborted) setAuthSession(user); })
      .catch(() => {})
      .finally(() => { if (!controller.signal.aborted) setSessionChecking(false); });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (authSession?.user_role !== 'admin') {
      setModerationQueue([]);
      return;
    }
    const controller = new AbortController();
    fetch(`${apiBase}/moderation`, {
      credentials: 'include',
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error('Could not load admin queue');
        return response.json();
      })
      .then((data: { queue?: ModerationItem[] }) => setModerationQueue(data.queue ?? []))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) console.error('Admin queue request failed:', error);
      });
    return () => controller.abort();
  }, [authSession]);

  const fetchDemoWorkspace = async () => {
    if (!authSession) return;
    const options: RequestInit = { credentials: 'include', cache: 'no-store' };
    const [recordsRes, historyRes, docsRes, privacyRes, dashboardRes] = await Promise.all([
      fetch(`${apiBase}/demo-registry`, options), fetch(`${apiBase}/demo-registry/history`, options),
      fetch(`${apiBase}/documents`, options), fetch(`${apiBase}/privacy/me`, options),
      fetch(`${apiBase}/dashboard`, options),
    ]);
    if (!recordsRes.ok || !historyRes.ok || !docsRes.ok || !privacyRes.ok || !dashboardRes.ok) throw new Error('Could not load private demo workspace.');
    const recordData: { records: DemoRegistryRecord[] } = await recordsRes.json();
    const historyData: { history: DemoHistory[] } = await historyRes.json();
    const documentData: { owned: PrivateDocument[]; shared_with_me: PrivateDocument[] } = await docsRes.json();
    const privacyData: {verification_activity_metadata: {id:string;purpose:string;evidence_status:string;created_at:string}[]} = await privacyRes.json();
    const activity: {total_properties_viewed:number;demo_documents:number;verification_requests:number;completed_checks:number;pending_checks:number;unresolved_issues:number} = await dashboardRes.json();
    setStats([
      {label:'Properties viewed',value:activity.total_properties_viewed},
      {label:'My demo documents',value:activity.demo_documents},
      {label:'Verification requests',value:activity.verification_requests},
      {label:'Processed local checks',value:activity.completed_checks},
      {label:'Unreadable uploads',value:activity.pending_checks},
      {label:'Needs follow-up review',value:activity.unresolved_issues},
    ]);
    setExtractionHistory(privacyData.verification_activity_metadata);
    setRegistry(recordData.records);
    setRegistryHistory(historyData.history);
    setVaultOwned(documentData.owned);
    setVaultShared(documentData.shared_with_me);
    if (authSession.user_role === 'admin') {
      const adminRes = await fetch(`${apiBase}/demo-admin/summary`, options);
      if (adminRes.ok) {
        const result: { counts: Record<string, number> } = await adminRes.json();
        setAdminSummary(result.counts);
      }
    }
  };

  useEffect(() => {
    if (!authSession) {
      setRegistry([]); setRegistryHistory([]); setExtractionHistory([]); setVaultOwned([]); setVaultShared([]);
      setSelectedDemoRecord(''); setAdminSummary(null); setDemoStatus('');
      setCurrentDemoResult(null); setShowSavedDemoHistory(false);
      return;
    }
    // Refresh on login; subsequent writes refresh explicitly.
    void fetchDemoWorkspace().catch(() => setDemoStatus('ডেমো তথ্য এই মুহূর্তে পাওয়া যাচ্ছে না। কিছুক্ষণ পরে আবার চেষ্টা করুন।'));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authSession]);

  const demoWrite = async (path: string, method: string, payload?: unknown, fileData?: FormData) => {
    const csrfToken = await csrfForWrite();
    const response = await fetch(`${apiBase}${path}`, {
      method, credentials: 'include',
      headers: fileData ? {'X-CSRF-Token':csrfToken} : {'X-CSRF-Token':csrfToken,'Content-Type':'application/json'},
      body: fileData ?? (payload === undefined ? undefined : JSON.stringify(payload)),
    });
    const data: Record<string, unknown> = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(String(data.detail || `Server error ${response.status}`));
    return data;
  };

  const refreshDemo = async () => {
    try { await fetchDemoWorkspace(); setDemoStatus(text('Demo workspace refreshed.', 'ডেমো তথ্য আপডেট হয়েছে।')); }
    catch (error) { setDemoStatus(error instanceof Error ? error.message : 'Connection error'); }
  };

  const resetDemoComparison = () => {
    const hasInput = selectedDemoRecord || registrySearch || Object.values(demoValues).some(Boolean);
    if (hasInput && !window.confirm(text('Discard the unsaved comparison values?', 'সংরক্ষণ না করা তুলনার তথ্য মুছে ফেলবেন?'))) return;
    setRegistrySearch('');
    setSelectedDemoRecord('');
    setDemoValues({owner_name:'',district:'',mouza:'',khatian:'',dag:'',land_area:''});
    setDemoStatus('');
    setCurrentDemoResult(null);
    setShowSavedDemoHistory(false);
  };

  const resetAdminRecord = (confirm: boolean) => {
    if (confirm && Object.values(adminRecord).some(Boolean) &&
        !window.confirm(text('Discard the unsaved new-record values?', 'সংরক্ষণ না করা নতুন রেকর্ডের তথ্য মুছে ফেলবেন?'))) return;
    setAdminRecord({owner_name:'',district:'',upazila:'',mouza:'',khatian:'',dag:'',land_area:''});
  };

  const submitDemoCheck = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedDemoRecord) return;
    setCurrentDemoResult(null);
    try {
      const result = await demoWrite('/demo-registry/check','POST',{
        record_id:selectedDemoRecord, purpose:'purchase_due_diligence', acknowledge_demo:true, ...demoValues,
      });
      const status = String(result.result || 'unknown');
      setCurrentDemoResult(`${status} · ${text('Only fictional demo registry checked; NOT government verified.', 'শুধু পরীক্ষামূলক ডেমো রেকর্ড মিলেছে; সরকারি যাচাই নয়।')}`);
      setDemoStatus('');
      await fetchDemoWorkspace();
    } catch (error) { setCurrentDemoResult(null); setDemoStatus(error instanceof Error ? error.message : 'Demo check failed'); }
  };

  const submitPrivateFile = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedVaultFile || !vaultConsent) return;
    const form = new FormData();
    form.append('document',selectedVaultFile);
    form.append('demo_only','true'); form.append('authorityAttested','true');
    try {
      await demoWrite('/documents','POST',undefined,form);
      setDemoStatus(text('Encrypted demo file saved privately.', 'এনক্রিপ্টেড ডেমো ফাইল ব্যক্তিগতভাবে সংরক্ষিত হয়েছে।'));
      setSelectedVaultFile(null); setVaultConsent(false);
      await fetchDemoWorkspace();
    } catch (error) { setDemoStatus(error instanceof Error ? error.message : 'Upload failed'); }
  };

  const downloadPrivate = async (id: string) => {
    try {
      const response = await fetch(`${apiBase}/documents/${encodeURIComponent(id)}/download`, { credentials: 'include', cache:'no-store' });
      if (!response.ok) throw new Error('File is not accessible.');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url;
      a.download = [...vaultOwned,...vaultShared].find(f=>f.id===id)?.original_filename || 'landguard-demo-document';
      a.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1500);
    } catch (error) { setDemoStatus(error instanceof Error ? error.message : 'Download failed'); }
  };

  const doVaultAction = async (fileId: string, mode: 'delete'|'grant'|'revoke') => {
    if (mode === 'delete' && !window.confirm(text('Delete this demo document?', 'এই ডেমো নথিটি মুছে ফেলবেন?'))) return;
    try {
      await demoWrite(`/documents/${encodeURIComponent(fileId)}${mode === 'delete' ? '' : '/grant'}`,
        mode === 'grant' ? 'POST' : 'DELETE',
        mode === 'grant' ? {recipient_email: demoShareEmail.trim(), purpose:'purchase_due_diligence', confirm_demo:true} : undefined);
      setDemoStatus(text('Document permission updated.', 'নথির অনুমতি আপডেট হয়েছে।'));
      await fetchDemoWorkspace();
    } catch (error) { setDemoStatus(error instanceof Error ? error.message : 'Operation failed'); }
  };

  const createAdminRecord = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await demoWrite('/demo-registry/admin','POST',{...adminRecord, confirm_fictional:true});
      setDemoStatus(text('Demo record saved successfully.', 'নমুনা রেকর্ড সফলভাবে সংরক্ষিত হয়েছে।'));
      resetAdminRecord(false);
      await fetchDemoWorkspace();
    } catch (error) { setDemoStatus(error instanceof Error ? error.message : 'Could not add record'); }
  };

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (loginPending) return;
    setLoginPending(true);
    setLoginError('');
    setLoginRetrySeconds(0);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 12000);
    try {
      // One deadline for both CSRF handshake and the credential POST.
      const csrfResponse = await fetch(`${apiBase}/auth/csrf`, {
        credentials: 'include', cache: 'no-store', signal: controller.signal,
      });
      if (!csrfResponse.ok) throw new Error('connection_failed');
      const csrfData: { csrf_token: string } = await csrfResponse.json();
      const response = await fetch(`${apiBase}/auth/${registerMode ? 'register' : 'login'}`, {
        method: 'POST', credentials: 'include', signal: controller.signal,
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfData.csrf_token },
        body: JSON.stringify(registerMode ? { email: loginEmail.trim(), password: loginPassword, name: registerName.trim(), accept_demo_terms: acceptDemoTerms }
          : { email: loginEmail.trim(), password: loginPassword }),
      });
      if (!response.ok) {
        // Distinguish registration validation, duplicate account, CSRF, and temporary limits.
        // Never display raw server tracebacks or infrastructure details to a user.
        if (response.status === 429) {
          const details: {retry_after_seconds?: number} = await response.json().catch(() => ({}));
          const retry = Number(details.retry_after_seconds || response.headers.get('Retry-After') || (registerMode ? 3600 : 900));
          setLoginRetrySeconds(Math.max(1, Math.min(3600, retry)));
          throw new Error(registerMode ? 'registration_rate_limited' : 'rate_limited');
        }
        if (response.status === 403) throw new Error('csrf_failed');
        if (response.status === 409 && registerMode) throw new Error('account_exists');
        if (response.status === 400 && registerMode) {
          const details: {detail?: string} = await response.json().catch(() => ({}));
          if (details.detail?.startsWith('Confirm demo-only')) throw new Error('terms_required');
          throw new Error('invalid_registration');
        }
        if (response.status === 401) throw new Error('invalid_credentials');
        if (response.status >= 500) throw new Error('server_error');
        throw new Error(registerMode ? 'registration_failed' : 'server_error');
      }
      if (registerMode) {
        setRegisterMode(false); setAcceptDemoTerms(false); setLoginPassword('');
        setLoginError('registration_success');
        return;
      }
      const user: AuthSession = await response.json();
      setAuthSession(user);
      setLoginPassword('');
      setLoginOpen(false);
    } catch (error) {
      setLoginError(controller.signal.aborted ? 'timeout' : error instanceof TypeError ? 'connection_failed' : error instanceof Error ? error.message : 'server_error');
    } finally {
      window.clearTimeout(timeoutId);
      setLoginPending(false);
    }
  };

  const handleLogout = async () => {
    try {
      const csrfToken = await csrfForWrite();
      const response = await fetch(`${apiBase}/auth/logout`, {
        method: 'POST', credentials: 'include', headers: { 'X-CSRF-Token': csrfToken },
      });
      if (!response.ok) throw new Error('logout_failed');
      setAuthSession(null);
      setModerationQueue([]);
      // Clear private evidence from UI memory on logout/shared computers.
      setVerificationForm(createEmptyVerificationForm());
      setVerificationResult(null);
      setVerificationOpen(false);
      setVerificationStep(1);
      setAuthorityAttested(false);
      setLoginPassword('');
      setLoginError(''); setDemoStatus('');
    } catch {
      setPrivacyStatus(text('Logout failed. Please retry.', 'লগআউট ব্যর্থ হয়েছে, আবার চেষ্টা করুন।'));
    }
  };

  const submitPrivacyRequest = async (type: 'access' | 'delete') => {
    if (!authSession) { setLoginOpen(true); return; }
    setPrivacyStatus('');
    try {
      const csrfToken = await csrfForWrite();
      const response = await fetch(`${apiBase}/privacy/request`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
        body: JSON.stringify({ type }),
      });
      if (!response.ok) throw new Error('privacy_failed');
      setPrivacyStatus(text('Your privacy request was recorded for manual review.', 'আপনার তথ্য-সংক্রান্ত অনুরোধ নথিভুক্ত হয়েছে; ম্যানুয়াল পর্যালোচনা প্রয়োজন।'));
    } catch {
      setPrivacyStatus(text('Could not submit request. Please retry.', 'অনুরোধ পাঠানো যায়নি। আবার চেষ্টা করুন।'));
    }
  };

  useEffect(() => {
    if (!loginOpen) {
      return;
    }

    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    loginCloseButtonRef.current?.focus();

    const handleLoginDialogKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setLoginOpen(false);
        return;
      }

      if (event.key !== 'Tab') {
        return;
      }

      const focusableElements = loginDialogRef.current?.querySelectorAll<HTMLElement>(
        'button:not(:disabled), a[href], input:not(:disabled), [tabindex]:not([tabindex="-1"])',
      );
      if (!focusableElements?.length) {
        event.preventDefault();
        return;
      }

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    };

    document.addEventListener('keydown', handleLoginDialogKeyDown);
    return () => {
      document.removeEventListener('keydown', handleLoginDialogKeyDown);
      previouslyFocused?.focus();
    };
  }, [loginOpen]);

  useEffect(() => {
    if (!authSession) {
      setProperties([]); setStats(defaultStats); setShowSampleSearch(false);
      setShowPropertyDetail(false); setLoading(false); setApiError('');
      return;
    }
    const load = async () => {
      setLoading(true);
      setApiError('');

      try {
        const propertiesRes = await fetch(`${apiBase}/properties`, { credentials: 'include' });
        if (!propertiesRes.ok) throw new Error('Property API request failed');
        const propertyData = await propertiesRes.json();
        const dashboardRes = authSession ? await fetch(`${apiBase}/dashboard`, { credentials: 'include' }) : null;
        const dashboardData = dashboardRes?.ok ? await dashboardRes.json() : null;

        const nextProperties = Array.isArray(propertyData) && propertyData.length > 0 ? propertyData : demoProperties;
        const nextSelectedId = nextProperties[0]?.id ?? 'DEMO-1001';

        setProperties(nextProperties);
        setSelectedId(nextSelectedId);
        setDataMode('demo'); // API currently returns sample data, not live government records.
        setApiError(
          Array.isArray(propertyData) && propertyData.length > 0
            ? ''
            : 'No live property records were returned by the API. Demo mode is active for testing.'
        );
        setStats(dashboardData ? [
          { label: 'Properties viewed', value: dashboardData.total_properties_viewed },
          { label: 'My demo documents', value: dashboardData.demo_documents ?? dashboardData.saved_properties },
          { label: 'Verification requests', value: dashboardData.verification_requests },
          { label: 'Processed local checks', value: dashboardData.completed_checks },
          { label: 'Unreadable uploads', value: dashboardData.pending_checks },
          { label: 'Needs follow-up review', value: dashboardData.unresolved_issues },
        ] : defaultStats);
      } catch (error) {
        console.error('Failed to load demo data:', error);
        setProperties(demoProperties);
        setSelectedId('DEMO-1001');
        setDataMode('demo');
        setApiError('Could not reach the Smart LandGuard BD API. Demo mode is active so the interface can still be tested.');
        setStats(defaultStats);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [authSession]);

  useEffect(() => {
    const loadPropertyDetails = async () => {
      if (!authSession || !selectedId) {
        return;
      }

      if (selectedId.startsWith('DEMO-')) {
        const demoDetail = demoPropertyDetails[selectedId];
        if (demoDetail) {
          const demoRecommendations = demoDetail.risk_flags.map((flag) => flag.recommendation);
          setDetail(demoDetail);
          setReport({
            property_id: demoDetail.id,
            report_title: `Demo verification report for ${demoDetail.title}`,
            status: sampleDataNotice,
            summary: demoDetail.evidence_summary,
            recommendations: [...demoRecommendations, governmentVerificationNotice],
          });
          setPurchaseChecklist({
            property_id: demoDetail.id,
            title: 'Demo purchase readiness checklist',
            overall_status: 'Buyer caution required',
            progress: 60,
            checklist: [
              {
                id: 'identity',
                title: 'Confirm seller identity and deed holder',
                status: 'in_progress',
                detail: 'Compare the seller name with the deed holder in this demo review.',
                urgency: 'High',
              },
              {
                id: 'mutation',
                title: 'Review mutation history and transfer record',
                status: 'pending',
                detail: 'Check whether any mutation or transfer record is missing from the sample dataset.',
                urgency: 'High',
              },
              {
                id: 'documents',
                title: 'Validate supporting documents',
                status: 'done',
                detail: 'The available demo records were reviewed for consistency and basic mismatch warnings.',
                urgency: 'Medium',
              },
              {
                id: 'risk',
                title: 'Assess dispute and encumbrance signals',
                status: 'pending',
                detail: 'Use the evidence summary and risk flags to decide whether more human review is needed.',
                urgency: 'High',
              },
            ],
          });
          setDetailError('');
          setDetailLoading(false);
          return;
        }
      }

      setDetailLoading(true);
      setDetailError('');
      try {
        const [detailRes, reportRes, checklistRes] = await Promise.all([
          fetch(`${apiBase}/properties/${selectedId}`, { credentials: 'include' }),
          fetch(`${apiBase}/reports/${selectedId}`, { credentials: 'include' }),
          fetch(`${apiBase}/properties/${selectedId}/purchase-checklist`, { credentials: 'include' }),
        ]);

        if (!detailRes.ok || !reportRes.ok || !checklistRes.ok) {
          throw new Error('Selected property detail request failed');
        }

        const detailData = await detailRes.json();
        const reportData = await reportRes.json();
        const checklistData = await checklistRes.json();

        if (!detailData || !detailData.id) {
          setDetail(null);
          setReport(null);
          setPurchaseChecklist(null);
          setDetailError('No property details are available for the selected record.');
          return;
        }

        setDetail(detailData);
        setReport(reportData);
        setPurchaseChecklist(checklistData);
      } catch (error) {
        console.error('Failed to load selected property details:', error);
        setDetail(null);
        setReport(null);
        setPurchaseChecklist(null);
        setDetailError('Unable to load property details. Please check the backend server or choose another record.');
      } finally {
        setDetailLoading(false);
      }
    };

    loadPropertyDetails();
  }, [selectedId, authSession]);

  const filteredProperties = properties.filter((property) => {
    const matchesSearch =
      !search ||
      property.title.toLowerCase().includes(search.toLowerCase()) ||
      property.location.toLowerCase().includes(search.toLowerCase()) ||
      property.id.toLowerCase().includes(search.toLowerCase()) ||
      (property.mouza ?? '').toLowerCase().includes(search.toLowerCase());

    const matchesRisk =
      filterRisk === 'all' ||
      property.risk_level.toLowerCase().includes(filterRisk.toLowerCase());

    return matchesSearch && matchesRisk;
  });

  const resetVerificationWizard = () => {
    setVerificationOpen(false);
    setVerificationStep(1);
    setVerificationForm(createEmptyVerificationForm());
    setAuthorityAttested(false);
    setVerificationPurpose('purchase_due_diligence');
    setVerificationErrors({});
    setVerificationResult(null);
    setReportExportMessage('');
  };

  const handleVerificationInput = (field: VerificationTextField, value: string) => {
    setVerificationForm((current) => ({
      ...current,
      [field]: value,
    }));

    if (verificationErrors[field]) {
      setVerificationErrors((current) => ({
        ...current,
        [field]: '',
      }));
    }
  };

  const handleVerificationDocuments = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    if (files.length > 3) {
      setVerificationErrors((prev) => ({ ...prev, documents: text('Maximum three documents per request.', 'একবারে সর্বোচ্চ তিনটি নথি দেওয়া যাবে।') }));
      event.target.value = '';
      return;
    }
    const validFiles: File[] = [];
    const nextErrors: string[] = [];

    files.forEach((file) => {
      const isAllowedType = allowedDocumentTypes.includes(file.type) || /\.(pdf|png|jpe?g|docx)$/i.test(file.name);
      const isWithinSizeLimit = file.size <= maxDocumentSizeBytes;

      if (!isAllowedType) {
        nextErrors.push(language === 'bn' ? `${file.name}: অসমর্থিত ফাইলের ধরন।` : `${file.name}: unsupported file type.`);
      }

      if (!isWithinSizeLimit) {
        nextErrors.push(language === 'bn' ? `${file.name}: ফাইলের আকার ১০MB সীমা ছাড়িয়েছে।` : `${file.name}: exceeds the 10MB size limit.`);
      }

      if (isAllowedType && isWithinSizeLimit) {
        validFiles.push(file);
      }
    });

    setVerificationForm((current) => ({
      ...current,
      documents: validFiles,
    }));

    setVerificationErrors((current) => ({
      ...current,
      documents: nextErrors.length > 0 ? nextErrors.join(' ') : '',
    }));

    event.target.value = '';
  };

  const canMoveToNextStep = () => {
    if (verificationStep === 1) {
      const validationErrors = validateVerificationStepOne(verificationForm, language);
      setVerificationErrors(validationErrors);
      return Object.keys(validationErrors).length === 0;
    }

    return true;
  };

  const handleVerificationNext = async () => {
    if (!canMoveToNextStep()) {
      return;
    }

    setVerificationErrors((current) => ({
      ...current,
      documents: current.documents || '',
    }));

    if (verificationStep === 3) {
      if (!authSession) {
        setExtractionError(text('Login required before submitting documents.', 'নথি জমা দেওয়ার আগে লগইন করুন।'));
        setLoginOpen(true);
        return;
      }
      if (!authorityAttested || verificationForm.documents.length === 0) {
        setExtractionError(text('Upload a document and confirm your legal right to submit it.', 'নথি দিন এবং এটি জমা দেওয়ার বৈধ অনুমতি নিশ্চিত করুন।'));
        return;
      }
      const baseResult = buildVerificationResult(verificationForm);
      setExtractionLoading(true);
      setExtractionError('');

      try {
        const formData = new FormData();
        formData.append('propertyOwnerName', verificationForm.ownerName);
        formData.append('purpose', verificationPurpose);
        formData.append('authorityAttested', String(authorityAttested));
        formData.append('mouza', verificationForm.mouza);
        formData.append('khatianNumber', verificationForm.khatianNumber);
        formData.append('dagNumber', verificationForm.dagNumber);
        formData.append('landArea', verificationForm.landArea);

        verificationForm.documents.forEach((file) => {
          formData.append('documents', file);
        });

        const csrfToken = await csrfForWrite();
        const response = await fetch(`${apiBase}/verification/extract`, {
          method: 'POST', credentials: 'include',
          headers: { 'X-CSRF-Token': csrfToken },
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Document extraction request failed.');
        }

        const documentComparison: VerificationDocumentAnalysis = await response.json();

        if (documentComparison.status === 'unreadable') {
          setExtractionError(text(
            'No readable land-record fields were extracted. Try a clearer document or install OCR; no verification result has been created.',
            'নথিতে পাঠযোগ্য জমির তথ্য পাওয়া যায়নি। পরিষ্কার নথি দিন বা OCR চালু করুন; কোনো যাচাইয়ের ফল তৈরি হয়নি।'
          ));
          setVerificationResult(null);
          return;
        }

        const extractedWarnings = documentComparison.mismatched.length > 0
          ? documentComparison.mismatched.map((item) => `Field mismatch: ${item.field} expected ${item.expected || 'unknown'} but found ${item.actual || 'no value'}.`)
          : [];

        const unreadableWarnings = documentComparison.documents.some((doc) => doc.status === 'unreadable')
          ? ['One or more uploaded documents could not be read locally. Please upload a clearer scan or a text-based file.']
          : [];

        const mergedResult = {
          ...baseResult,
          possibleInconsistencies: [...baseResult.possibleInconsistencies, ...extractedWarnings],
          riskWarnings: [...baseResult.riskWarnings, ...unreadableWarnings,
            ...(documentComparison.review_assessment === 'information_mismatch_review_required'
              ? ['Mismatched details require manual review; do not rely on this report for a purchase.']
              : []),
          ],
          documentComparison,
        };

        if (documentComparison.not_extracted.length > 0) {
          mergedResult.missingEvidence = [
            ...baseResult.missingEvidence,
            ...documentComparison.not_extracted.map((item) => `${item.field.replace(/_/g, ' ')} could not be extracted from uploaded evidence.`),
          ];
        }

        if (!documentComparison.documents.length && !documentComparison.matched.length && !documentComparison.mismatched.length && !documentComparison.not_extracted.length) {
          mergedResult.riskWarnings = [
            ...mergedResult.riskWarnings,
            'No document analysis result was returned. The uploaded files were not processed by the local extraction endpoint.',
          ];
        }

        setVerificationResult(mergedResult);
        setVerificationStep(4);
        void fetchDemoWorkspace().catch(() => { /* Keep the current result visible if stats refresh fails. */ });
      } catch (error) {
        console.error('Failed to analyze document evidence:', error);
        setExtractionError('Document extraction could not be completed. Please upload a valid PDF, image, or text file and try again.');
        // Do not produce a purported verification report when processing failed.
        setVerificationResult(null);
      } finally {
        setExtractionLoading(false);
      }
      return;
    }

    setVerificationStep((current) => current + 1);
  };

  const handleVerificationBack = () => {
    if (verificationStep > 1) {
      setVerificationStep((current) => current - 1);
    }
  };

  const buildReportText = (result: VerificationResult): string => {
    const comparison = result.documentComparison;
    const matchedFields = comparison?.matched.map((item) => `- ${item.field}: ${item.value ?? item.expected ?? 'Not available'}`) ?? [];
    const mismatches = comparison?.mismatched.map((item) => `- ${item.field}: expected ${item.expected ?? 'unknown'}, found ${item.actual ?? 'no value'}`) ?? [];
    const ambiguous = comparison?.ambiguous.map((item) => `- ${item.field}: ${item.reason ?? 'Ambiguous value needs human review'} (expected ${item.expected ?? 'unknown'}, found ${item.actual ?? 'no value'})`) ?? [];
    const missing = result.missingEvidence.length > 0 ? result.missingEvidence.map((item) => `- ${item}`) : ['- None'];
    const evidence = comparison?.documents.flatMap((document) => {
      const entries = Object.entries(document.field_evidence ?? {});
      return entries.length > 0
        ? entries.map(([field, value]) => `- ${document.filename}: ${field} => ${value}`)
        : [`- ${document.filename}: no extracted evidence was recorded.`];
    }) ?? ['- No document evidence was extracted.'];

    return [
      'Smart LandGuard BD Verification Report',
      'DEMO LOCAL TEXT COMPARISON — not official government verification or legal proof of ownership.',
      '',
      'Property details',
      `- Property: ${result.propertyName}`,
      `- District / Upazila: ${result.district}, ${result.upazila}`,
      `- Mouza: ${result.mouza}`,
      `- Khatian: ${result.khatianNumber}`,
      `- Dag: ${result.dagNumber}`,
      `- Land area: ${result.landArea}`,
      '',
      'Extracted evidence',
      ...evidence,
      '',
      'Matched fields',
      ...(matchedFields.length > 0 ? matchedFields : ['- None']),
      '',
      'Mismatches',
      ...(mismatches.length > 0 ? mismatches : ['- None']),
      '',
      'Ambiguous values',
      ...(ambiguous.length > 0 ? ambiguous : ['- None']),
      '',
      'Missing evidence',
      ...missing,
      '',
      'Risk warnings',
      ...(result.riskWarnings.length > 0 ? result.riskWarnings.map((item) => `- ${item}`) : ['- None']),
      '',
      'Review recommendations',
      ...(result.recommendedNextSteps.length > 0 ? result.recommendedNextSteps.map((item) => `- ${item}`) : ['- None']),
      '',
      'Disclaimer',
      'This report is generated by a local prototype review workflow and does not constitute official government verification, legal title confirmation, or proof of ownership.',
    ].join('\n');
  };

  const handleCopyReport = async () => {
    if (!verificationResult) {
      return;
    }

    try {
      const reportText = buildReportText(verificationResult);
      await navigator.clipboard.writeText(reportText);
      setReportExportMessage('Verification report copied to clipboard.');
    } catch (error) {
      console.error('Unable to copy report:', error);
      setReportExportMessage('Copy failed. Please try again or use the browser share option.');
    }
  };

  const handleDownloadPdf = () => {
    if (!verificationResult) return;
    // Use the browser's Unicode-capable PDF print engine instead of the old
    // hand-written one-page Helvetica PDF (which cut off lines and Bangla).
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      setReportExportMessage('Please allow pop-ups for this site and try Print / Save PDF again.');
      return;
    }
    const doc = printWindow.document;
    doc.open();
    doc.write(`<!doctype html><html lang="en"><head><meta charset="utf-8" />
      <title>Smart LandGuard BD - Demo Evidence Report</title>
      <style>
      @page { size: A4; margin: 18mm; }
      body { font-family: "Noto Sans Bengali", "Nirmala UI", "Segoe UI", Arial, sans-serif;
        font-size: 11pt; line-height: 1.5; color: #162b23; background: #fff; }
      .notice { border: 2px solid #8a5800; padding: 12px; font-weight: 700;
        margin-bottom: 16px; overflow-wrap: anywhere; }
      pre { font-family: inherit; font-size: 10pt; white-space: pre-wrap;
        overflow-wrap: anywhere; margin: 0; }
      .help { margin-top: 24px; font-size: 10pt; color: #555; }
      @media print { .help { display:none; } }
      </style></head><body><div class="notice">DEMO EVIDENCE REPORT — NOT GOVERNMENT VERIFIED. Not legal proof of ownership.</div>
      <pre id="report"></pre>
      <p class="help">Choose Print → Save as PDF, and enable background graphics if desired.</p>
      </body></html>`);
    doc.close();
    // All report content is inserted as text, never parsed as user-supplied HTML.
    const content = doc.getElementById('report');
    if (content) content.textContent = buildReportText(verificationResult);
    printWindow.focus();
    printWindow.setTimeout(() => printWindow.print(), 250);
    setReportExportMessage('Print dialog opened. Select Save as PDF to save your multi-page report.');
  };

  const handleShareReport = async () => {
    if (!verificationResult) {
      return;
    }

    const reportText = buildReportText(verificationResult);

    try {
      if (navigator.share) {
        await navigator.share({
          title: 'Smart LandGuard BD Verification Report',
          text: reportText,
        });
        setReportExportMessage('Verification report shared successfully.');
        return;
      }

      await navigator.clipboard.writeText(reportText);
      setReportExportMessage('Sharing is not supported in this browser, so the report text was copied to your clipboard instead.');
    } catch (error) {
      console.error('Unable to share report:', error);
      try {
        await navigator.clipboard.writeText(reportText);
        setReportExportMessage('Unable to share directly. The report text was copied to your clipboard instead.');
      } catch (copyError) {
        console.error('Unable to copy fallback report:', copyError);
        setReportExportMessage('Sharing and copying are both unavailable in this browser.');
      }
    }
  };

  return (
    <div className="container" lang={language}>
      <header className={`topbar${headerCompact ? ' topbar--compact' : ''}`}>
        <div className="topbar-inner">
          <a className="brand" href="#home" aria-label={text('Smart LandGuard BD home', 'স্মার্ট ল্যান্ডগার্ড বিডি হোম')}>
            <span className="brand-mark" aria-hidden="true">
              <img src={bangladeshOutline} alt="" />
              <span />
            </span>
            <div className="brand-copy">
              <strong>Smart LandGuard BD</strong>
              <span className="brand-tag">{text('Land verification, safe future', 'জমি যাচাই, নিরাপদ ভবিষ্যৎ')}</span>
            </div>
          </a>

          <nav className="nav" aria-label={text('Main navigation', 'প্রধান নেভিগেশন')}>
            {([
              ['home', 'Home', 'হোম'],
              ['features', 'Services', 'সেবা সমূহ'],
              ['verification', 'Verify documents', 'দলিল যাচাই'],
              ['dashboard', 'Dashboard', 'ড্যাশবোর্ড'],
              ['my-documents', 'My documents', 'আমার নথি'],
              ['reports', 'Reports', 'রিপোর্ট'],
              ['help', 'Help', 'সহায়তা'],
            ] as const).filter(([id]) => authSession ? id !== 'help' : ['home', 'features', 'help'].includes(id)).map(([id, en, bn]) => (
              <a key={id} href={`#${id}`} aria-current={activeNav === id ? 'page' : undefined}
                 onClick={() => setActiveNav(id)}>{text(en, bn)}</a>
            ))}
          </nav>

          <div className="header-tools">
            <button
              type="button"
              className="language-switch"
              aria-label={text('Switch language to Bengali', 'ভাষা ইংরেজিতে পরিবর্তন করুন')}
              onClick={() => setLanguage((current) => (current === 'bn' ? 'en' : 'bn'))}
            >
              <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7.2" /><path d="M3 10h14M10 2.8c2 2 3 4.4 3 7.2s-1 5.2-3 7.2c-2-2-3-4.4-3-7.2s1-5.2 3-7.2Z" /></svg>
              {language === 'bn' ? 'English' : 'বাংলা'} <span aria-hidden="true">⌄</span>
            </button>
            {authSession ? (
              <>
                <span className="signed-in-user" title={authSession.user_name}>
                  {authSession.user_name} <small>({authSession.user_role})</small>
                </span>
                <button type="button" className="login-button logout-button" onClick={handleLogout}>
                  {text('Logout', 'লগআউট')}
                </button>
              </>
            ) : (
              <button type="button" className="login-button" onClick={() => { setLoginError(''); setLoginOpen(true); }}>
                <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="6.2" r="3" /><path d="M3.8 17c.4-3.1 2.5-5 6.2-5s5.8 1.9 6.2 5" /></svg>
                {text('Login', 'লগইন')}
              </button>
            )}
          </div>
        </div>
      </header>

      <main>
        <section id="home" className="hero">
          <div className="hero-inner">
            <div className="hero-copy">
              <span className="badge"><span className="brand-leaf" aria-hidden="true">◆</span> {text('Reliable land information verification', 'নির্ভরযোগ্য জমি তথ্য যাচাই সেবা')}</span>
              <h1>{text('Smart LandGuard BD', 'স্মার্ট ল্যান্ডগার্ড বিডি')}</h1>
              <h2>{text('Verify land documents easily and safely', 'জমির কাগজপত্র যাচাই করুন সহজে ও নিরাপদে')}</h2>
              <p>
                {text('Verify the accuracy of deeds, khatians, plot numbers, and land information.', 'দলিল, খতিয়ান ও দাগ নম্বরের তথ্য তুলনা করে সম্ভাব্য অসংগতি দেখুন।')}
                <br />
                {text('Reduce misinformation risks and make safer transactions.', 'ভুল তথ্যের ঝুঁকি শনাক্ত করুন; চূড়ান্ত সিদ্ধান্তের আগে সরকারি উৎসে যাচাই করুন।')}
              </p>
              <div className="hero-actions">
                {authSession ? <a className="primary-button" href="#verification">
                  <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 13V3m0 0L6.5 6.5M10 3l3.5 3.5M4 12.5v3A1.5 1.5 0 0 0 5.5 17h9a1.5 1.5 0 0 0 1.5-1.5v-3" /></svg>
                  {text('Verify documents', 'কাগজপত্র যাচাই করুন')} <span aria-hidden="true">→</span>
                </a> : <button type="button" className="primary-button" onClick={() => setLoginOpen(true)}>
                  {text('Log in to verify documents', 'দলিল যাচাই করতে লগইন করুন')} <span aria-hidden="true">→</span>
                </button>}
                {!authSession && <a className="secondary-button" href="#help">
                  <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 2.8h7l3 3V17H5zM12 3v3h3M8 10h4M8 13h4" /><path d="m11.5 14.4 1.5 1.5 3-3" /></svg>
                  {text('How to verify', 'যেভাবে যাচাই করবেন')} <span aria-hidden="true">→</span>
                </a>}
              </div>
            </div>

            <div className="hero-panel" aria-label={text('Rural Bangladesh landscape', 'বাংলাদেশের গ্রামীণ দৃশ্য')}>
              <img
                src={heroLandscape}
                alt={text('Green rural fields in Bangladesh', 'বাংলাদেশের সবুজ গ্রামীণ মাঠ')}
                className="hero-visual"
              />
              <div className="hero-photo-fade" aria-hidden="true" />
            </div>
          </div>
        </section>

        <section id="features" className="info-section" aria-label={text('Services', 'সেবা সমূহ')}>
          <div className="feature-grid">
            {featureCards.map((feature) => (
              <article key={feature.title} className="feature-card">
                <div className="feature-icon" aria-hidden="true">
                  {feature.icon === 'deed' && <svg viewBox="0 0 32 32"><path d="M8 3h11l7 7v18H8zM19 3v7h7M12 16h10M12 20h10M12 24h6" /><path d="m5 7 0 22h17" /></svg>}
                  {feature.icon === 'shield' && <svg viewBox="0 0 32 32"><path d="M16 3 27 7v8c0 7-4.5 12-11 15C9.5 27 5 22 5 15V7l11-4Z"/><path d="m11 16 4 4 7-8"/></svg>}
                  {feature.icon === 'location' && <svg viewBox="0 0 32 32"><path d="M5 25V8l7-4 7 4 8-4v17l-8 4-7-4-7 4Z"/><path d="m12 4 0 17m7-13v17M14 14c0-2 1.4-3.5 3.2-3.5s3.2 1.5 3.2 3.5c0 2.5-3.2 6-3.2 6s-3.2-3.5-3.2-6Z"/></svg>}
                  {feature.icon === 'report' && <svg viewBox="0 0 32 32"><path d="M8 3h11l7 7v18H8zM19 3v7h7M12 16h10M12 20h10M12 24h6"/></svg>}
                </div>
                <div className="feature-copy">
                  <h3>{language === 'bn' ? feature.title : feature.englishTitle}</h3>
                  <p>{language === 'bn' ? feature.description : feature.englishDescription}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-panels" aria-label={text('Document upload, recent activity, and important information', 'নথি আপলোড, সাম্প্রতিক কার্যক্রম ও গুরুত্বপূর্ণ তথ্য')}>
          <aside className="landing-card notice-card">
            <div className="landing-card-heading">
              <span className="landing-shield" aria-hidden="true">
                <svg viewBox="0 0 52 60"><path d="M26 2 48 10v16c0 14-9 25-22 32C13 51 4 40 4 26V10L26 2Z" fill="#087344"/><path d="m15 28 8 8 15-18" fill="none" stroke="#fff" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </span>
              <div>
                <h2>{text('This is a prototype system', 'এটি একটি প্রোটোটাইপ সিস্টেম')}</h2>
                <p>{text('Independent land information assistance platform', 'স্বাধীন জমি তথ্য সহায়ক প্ল্যাটফর্ম')}</p>
              </div>
            </div>
            <p>{text('This system supports khatian analysis, deed review, and information comparison. It is not connected to any government land-record database.', 'এই সিস্টেমটি খতিয়ান বিশ্লেষণ, দলিল যাচাই এবং তথ্য তুলনার জন্য তৈরি করা হয়েছে। এখানে কোনো সরকারি ভূমি রেকর্ড ডেটাবেসের সাথে সংযোগ করা হয়নি।')}</p>
            <div className="notice-warning">
              <strong><span aria-hidden="true">i</span> {text('Notice', 'সতর্কতা')}</strong>
              <p>{text('Displayed information may be sample data. Check official sources before making decisions.', 'এখানে প্রদর্শিত তথ্য ডেমো বা নমুনা ডেটা হতে পারে। প্রকৃত সিদ্ধান্তের আগে সংশ্লিষ্ট সরকারি সূত্র থেকে যাচাই করুন।')}</p>
            </div>
          </aside>
        </section>

      </main>



      {!authSession && !sessionChecking && (
        <section id="help" className="landguard-help-section guest-help card" aria-label={text('How to review land documents', 'জমির কাগজপত্র যাচাইয়ের নির্দেশিকা')}>
          <p className="eyebrow">{text('Practical guidance', 'সহজ ব্যবহার নির্দেশিকা')}</p>
          <h2>{text('How to review land documents', 'যেভাবে জমির কাগজপত্র যাচাই করবেন')}</h2>
          <ol className="landguard-help-steps">
            <li>{text('Create a demo account and log in. Never upload real identity documents to this academic prototype.', 'ডেমো অ্যাকাউন্ট তৈরি করে লগইন করুন। এই পরীক্ষামূলক সংস্করণে আসল NID বা ব্যক্তিগত দলিল দেবেন না।')}</li>
            <li>{text('Open Document Verification and enter the land details with authorized sample files.', 'দলিল যাচাই অংশে জমির তথ্য ও অনুমোদিত নমুনা নথি দিন।')}</li>
            <li>{text('Review extracted text, mismatches and missing evidence. OCR can be wrong.', 'উদ্ধার করা লেখা, অমিল ও অনুপস্থিত প্রমাণ যাচাই করুন। OCR ভুল করতে পারে।')}</li>
            <li>{text('Compare sample data as an exercise; it is not government verification.', 'নমুনা রেকর্ডের সঙ্গে তথ্যের তুলনা শুধু উদাহরণ; এটি সরকারি যাচাই নয়।')}</li>
            <li>{text('For real purchases, consult authorized government offices and qualified legal professionals.', 'বাস্তবে জমি কেনার আগে সংশ্লিষ্ট সরকারি অফিস ও যোগ্য আইনজীবীর মাধ্যমে যাচাই করুন।')}</li>
          </ol>
          <div className="guest-help-actions">
            <button type="button" className="primary-button" onClick={() => {setRegisterMode(false);setLoginOpen(true);}}>{text('Log in', 'লগইন করুন')}</button>
            <button type="button" className="secondary-button" onClick={() => {setRegisterMode(true);setLoginOpen(true);}}>{text('Create account', 'অ্যাকাউন্ট তৈরি করুন')}</button>
          </div>
        </section>
      )}

      {authSession && <main className="dashboard-content">
        {apiError && (
          <div className="status-banner" role="status">
            <span className="demo-mode">{text(dataMode === 'demo' ? 'Demo mode' : 'Live data', dataMode === 'demo' ? 'ডেমো মোড' : 'সরাসরি ডেটা')}</span>
            <p>{language === 'bn' ? ({
              'No live property records were returned by the API. Demo mode is active for testing.': 'API থেকে কোনো সরাসরি সম্পত্তির তথ্য পাওয়া যায়নি। পরীক্ষার জন্য ডেমো মোড চালু আছে।',
              'Could not reach the Smart LandGuard BD API. Demo mode is active so the interface can still be tested.': 'Smart LandGuard BD API-তে সংযোগ করা যায়নি। ইন্টারফেস পরীক্ষা করার জন্য ডেমো মোড চালু আছে।',
            }[apiError] ?? apiError) : apiError}</p>
          </div>
        )}

        <section id="search" className="search-panel card">
          <div className="section-header">
            <div>
              <p className="eyebrow">{text('Search', 'অনুসন্ধান')}</p>
              <h2>{text('Find land records and risk signals', 'জমির রেকর্ড ও ঝুঁকির তথ্য খুঁজুন')}</h2>
            </div>
          </div>

          <div className="search-row">
            <input
              type="text"
              placeholder={text('Search by property, location, ID, or mouza...', 'সম্পত্তি, অবস্থান, আইডি বা মৌজা দিয়ে খুঁজুন...')}
              value={search}
              onChange={(event) => { setSearch(event.target.value); setShowSampleSearch(true); setShowPropertyDetail(false); }}
            />
            <select value={filterRisk} onChange={(event) => { setFilterRisk(event.target.value); setShowSampleSearch(true); setShowPropertyDetail(false); }}>
              <option value="all">{text('All risk levels', 'সব ঝুঁকির স্তর')}</option>
              <option value="additional verification recommended">{text('Additional verification recommended', 'অতিরিক্ত যাচাই প্রয়োজন')}</option>
              <option value="significant unresolved concern">{text('Significant unresolved concern', 'উল্লেখযোগ্য অমীমাংসিত ঝুঁকি')}</option>
              <option value="no issue identified in available checks">{text('No issue identified', 'কোনো সমস্যা শনাক্ত হয়নি')}</option>
            </select>
          </div>
          <div className="search-actions">
            <button type="button" className="secondary-button" onClick={() => {setShowSampleSearch(true); setShowPropertyDetail(false);}}>
              {text('Browse fictional samples', 'নমুনা রেকর্ড দেখুন')}
            </button>
            {showSampleSearch && <button type="button" className="secondary-button" onClick={() => {setShowSampleSearch(false); setShowPropertyDetail(false); setSearch(''); setFilterRisk('all');}}>
              {text('Close sample results', 'নমুনা তালিকা বন্ধ করুন')}
            </button>}
          </div>
          <p className="source-note">{text('These are fictional samples, not actual properties offered for sale.', 'এগুলো পরীক্ষামূলক রেকর্ড—বিক্রয়ের জন্য প্রকৃত জমির তালিকা নয়।')}</p>
        <div id="reports" className="sample-analysis-section search-inline-results">
          <div className="section-header"><div>
            <p className="eyebrow">{text('Fictional samples only', 'শুধু পরীক্ষামূলক নমুনা')}</p>
            <h2>{text('Sample property information and risk review', 'নমুনা জমির তথ্য ও ঝুঁকি পর্যালোচনা')}</h2>
            <p>{text('Select a fictional record from Search to open its details. Nothing is government verified.', 'অনুসন্ধান থেকে নমুনা রেকর্ড বেছে নিলে বিস্তারিত খুলবে। কোনো তথ্য সরকারি যাচাইকৃত নয়।')}</p>
          </div></div>
          {showSampleSearch ? <div className="property-layout">
          <div className="property-list">
            <div className="section-header">
              <h2>{text('Fictional search results', 'নমুনা অনুসন্ধানের ফলাফল')}</h2>
            </div>

            {loading ? (
              <p>{text('Loading demo records...', 'ডেমো রেকর্ড লোড হচ্ছে...')}</p>
            ) : filteredProperties.length === 0 ? (
              <div className="empty-state" role="status">
                <h3>{text('No matching land records found', 'মিলে যাওয়া জমির রেকর্ড পাওয়া যায়নি')}</h3>
                <p>{text('Try another search, use a demo property, or enter a plot ID, mouza, or location to continue testing.', 'অন্যভাবে খুঁজুন, ডেমো সম্পত্তি বেছে নিন অথবা প্লট আইডি, মৌজা বা অবস্থান লিখুন।')}</p>
                <div className="empty-actions">
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => {
                      setSearch('');
                      setFilterRisk('all');
                    }}
                  >
                    {text('Try another search', 'আবার খুঁজুন')}
                  </button>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => {
                      setSearch('');
                      setFilterRisk('all');
                      setSelectedId(demoProperties[0]?.id ?? '');
                    }}
                  >
                    {text('Use demo property', 'ডেমো সম্পত্তি ব্যবহার করুন')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid">
                {filteredProperties.map((property) => (
                  <article
                    key={property.id}
                    className={`card property-card ${selectedId === property.id ? 'selected' : ''}`}
                    onClick={() => { setSelectedId(property.id); setShowPropertyDetail(true); }}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        setSelectedId(property.id);
                        setShowPropertyDetail(true);
                      }
                    }}
                  >
                    <div className="meta">
                      <span className="status">{text('Fictional record', 'নমুনা রেকর্ড')}</span>
                    </div>
                    <h3>{property.title}</h3>
                    <p>{property.location}</p>
                    <div className="meta">
                      <span>ID: {property.id}</span>
                      <span>{text('Not for sale', 'বিক্রয়ের জন্য নয়')}</span>
                    </div>
                    <span className="sample-open-note">{text('Click to view fictional evidence and caveats →', 'নমুনা তথ্য ও সতর্কতা দেখতে ক্লিক করুন →')}</span>
                  </article>
                ))}
              </div>
            )}
          </div>

          <aside className="property-detail">
            <h2>{text('Property verification detail', 'সম্পত্তি যাচাইয়ের বিবরণ')}</h2>
            {!showPropertyDetail ? (
              <div className="card detail-empty-state">
                <p>{text('No record opened. Choose a fictional sample from the search results.', 'এখনো কোনো নমুনা খোলা হয়নি। অনুসন্ধানের ফলাফল থেকে একটি রেকর্ড নির্বাচন করুন।')}</p>
              </div>
            ) : detailLoading ? (
              <div className="card">
                <p>{text('Loading evidence and verification status...', 'প্রমাণ ও যাচাইয়ের অবস্থা লোড হচ্ছে...')}</p>
              </div>
            ) : detailError ? (
              <div className="card empty-state detail-empty-state">
                <h3>{text('Property details unavailable', 'সম্পত্তির বিবরণ পাওয়া যাচ্ছে না')}</h3>
                <p>{localizeMessage(detailError, {
                  'No property details are available for the selected record.': 'নির্বাচিত রেকর্ডের কোনো সম্পত্তির বিবরণ নেই।',
                  'Unable to load property details. Please check the backend server or choose another record.': 'সম্পত্তির বিবরণ লোড করা যায়নি। ব্যাকএন্ড সার্ভার পরীক্ষা করুন অথবা অন্য রেকর্ড বেছে নিন।',
                })}</p>
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => setSelectedId(demoProperties[0]?.id ?? '')}
                >
                  {text('Choose a demo property', 'একটি ডেমো সম্পত্তি বেছে নিন')}
                </button>
              </div>
            ) : detail ? (
              <>
                <div className="card detail-box">
                  <div className="meta">
                    <span className="status">{text(detail.verification_status, 'ডেমো নথির পর্যালোচনা')}</span>
                    <span className="risk">{text(detail.risk_level, 'সরকারি যাচাই হয়নি—আরও পর্যালোচনা প্রয়োজন')}</span>
                  </div>
                  <h3>{detail.title}</h3>
                  <p>{detail.location}</p>

                  <div className="meta-list">
                    <div><strong>{text('Mouza:', 'মৌজা:')}</strong> {detail.mouza}</div>
                    <div><strong>{text('Khatian:', 'খতিয়ান:')}</strong> {detail.khatian}</div>
                    <div><strong>{text('Dag:', 'দাগ:')}</strong> {detail.dag}</div>
                    <div><strong>{text('Area:', 'আয়তন:')}</strong> {detail.area}</div>
                    <div><strong>{text('Record type:', 'রেকর্ডের ধরন:')}</strong> {text('Fictional demo (not for sale)', 'নমুনা রেকর্ড (বিক্রয়ের জন্য নয়)')}</div>
                  </div>

                  <p className="evidence-summary">{text(detail.evidence_summary, 'এই নমুনা রেকর্ডের কিছু তথ্য মেলানো হয়েছে, কিন্তু মালিকানা, নামজারি ও অন্যান্য গুরুত্বপূর্ণ প্রমাণ সরকারি উৎসে যাচাই করা হয়নি।')}</p>
                </div>

                <div className="card detail-box">
                  <h4>{text('Risk flags', 'ঝুঁকির সংকেত')}</h4>
                  {detail.risk_flags.map((flag) => (
                    <div key={flag.title} className="flag-item">
                      <div className="meta">
                        <strong>{text(flag.title, ({
                          'Name mismatch in deed and khatian': 'দলিল ও খতিয়ানে নামের সম্ভাব্য অমিল',
                          'Mutation record missing': 'নামজারি নথি অনুপস্থিত',
                          'Ownership chain incomplete': 'মালিকানা পরিবর্তনের ইতিহাস অসম্পূর্ণ',
                          'Possible case reference in demo dataset': 'ডেমো রেকর্ডে মামলার সম্ভাব্য উল্লেখ',
                          'No major inconsistency found in available documents': 'প্রাপ্ত নমুনা নথিতে বড় অমিল পাওয়া যায়নি',
                        } as Record<string,string>)[flag.title] ?? 'নমুনা যাচাইয়ে সতর্কতা')}</strong>
                        <span className="severity">{text(flag.severity, flag.severity === 'High' ? 'জরুরি' : flag.severity === 'Medium' ? 'মাঝারি' : 'নিম্ন')}</span>
                      </div>
                      <p>{text(flag.evidence, 'এটি নমুনা রেকর্ডের সতর্কবার্তা; বাস্তব নথির অমিল বা অপরাধের প্রমাণ নয়।')}</p>
                      <p>
                        <strong>{text('Source:', 'উৎস:')}</strong> {text(flag.source, 'পরীক্ষামূলক ডেমো তথ্য')}
                      </p>
                      <p>
                        <strong>{text('Next step:', 'পরবর্তী পদক্ষেপ:')}</strong> {text(flag.recommendation, 'প্রয়োজনীয় সহায়ক নথি সংগ্রহ করে সংশ্লিষ্ট সরকারি অফিস এবং যোগ্য পর্যালোচকের মাধ্যমে যাচাই করুন।')}
                      </p>
                      <p>
                        <strong>{text('Human review:', 'মানব পর্যালোচনা:')}</strong> {flag.requires_human_review ? text('Required', 'প্রয়োজন') : text('Not required', 'প্রয়োজন নেই')}
                      </p>
                    </div>
                  ))}
                </div>

                {report && (
                  <div className="card detail-box">
                    <h4>{text(report.report_title, 'নমুনা নথি পর্যালোচনার সারসংক্ষেপ')}</h4>
                    <p className="report-status">{text(report.status, 'শুধু নমুনা তথ্য—সরকারি যাচাই নয়')}</p>
                    <p>{text(report.summary, 'কিছু নমুনা তথ্য তুলনা করা হয়েছে; এটি মালিকানা, দলিলের সত্যতা বা বৈধতার প্রমাণ নয়।')}</p>
                    <p className="source-note">{text(governmentVerificationNotice, 'এই প্রোটোটাইপে সরকারি রেকর্ড যাচাই করা হয়নি।')}</p>
                    <ul>
                      {report.recommendations.map((item) => (
                        <li key={item}>{text(item, 'প্রকৃত সিদ্ধান্তের আগে সংশ্লিষ্ট সরকারি কর্তৃপক্ষের রেকর্ড ও যোগ্য পেশাজীবীর সঙ্গে যাচাই করুন।')}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="card empty-state detail-empty-state">
                <h3>{text('No property details available.', 'সম্পত্তির কোনো বিবরণ নেই।')}</h3>
                <p>{text('Select a property from the list or use a demo record to continue testing.', 'তালিকা থেকে একটি সম্পত্তি বেছে নিন অথবা ডেমো রেকর্ড দিয়ে পরীক্ষা চালিয়ে যান।')}</p>
                <button type="button" className="primary-button" onClick={() => setSelectedId(demoProperties[0]?.id ?? '')}>
                  {text('Choose a demo property', 'একটি ডেমো সম্পত্তি বেছে নিন')}
                </button>
              </div>
            )}
          </aside>
          </div> : <p className="analysis-placeholder">{text('Nothing is displayed automatically. Use the Search section to browse fictional sample records.', 'এখানে স্বয়ংক্রিয়ভাবে কোনো জমির বিবরণ দেখানো হয় না। নমুনা রেকর্ড দেখতে অনুসন্ধান অংশ ব্যবহার করুন।')}</p>}
        </div>

        </section>

        <section id="verification" className="verification-section">
          <div className="verification-toolbar">
            <div>
              <p className="eyebrow">{text('Verification workflow', 'যাচাই প্রক্রিয়া')}</p>
              <h2>{text('Document upload and analysis', 'নথি আপলোড ও বিশ্লেষণ')}</h2>
              <p>{text('Step-by-step land evidence review — enter land details, upload documents, and review extracted information.', 'ধাপে ধাপে জমির প্রমাণ পর্যালোচনা—জমির তথ্য দিন, নথি আপলোড করুন এবং তুলনার ফলাফল দেখুন।')}</p>
            </div>
            <button type="button" className="primary-button" onClick={() => setVerificationOpen(true)}>
              {text('Start New Verification', 'নতুন যাচাই শুরু করুন')}
            </button>
          </div>

          {verificationOpen && (
            <div className="verification-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="verification-modal-title">
              <div className="verification-modal">
                <div className="verification-header">
                  <div>
                    <p className="eyebrow">{text('Verification wizard', 'যাচাই নির্দেশিকা')}</p>
                    <h3 id="verification-modal-title">{text('New evidence review', 'নতুন প্রমাণ পর্যালোচনা')}</h3>
                  </div>
                  <button type="button" className="secondary-button" onClick={resetVerificationWizard}>
                    {text('Cancel', 'বাতিল')}
                  </button>
                </div>

                <div className="verification-progress" aria-label={text('Verification progress', 'যাচাইয়ের অগ্রগতি')}>
                  {(language === 'bn' ? ['সম্পত্তির তথ্য', 'নথিপত্র', 'পর্যালোচনা', 'ফলাফল'] : ['Property information', 'Documents', 'Review', 'Results']).map((label, index) => (
                    <div key={label} className={`verification-step-pill ${verificationStep === index + 1 ? 'active' : ''}`}>
                      <span>{index + 1}</span>
                      <strong>{label}</strong>
                    </div>
                  ))}
                </div>

                {verificationStep === 1 && (
                  <div className="verification-form">
                    <div className="verification-grid">
                      <div className="field">
                        <label htmlFor="propertyName">{text('Property name', 'সম্পত্তির নাম')}</label>
                        <input id="propertyName" name="propertyName" value={verificationForm.propertyName} onChange={(event) => handleVerificationInput('propertyName', event.target.value)} placeholder={text('North View Land Plot', 'নর্থ ভিউ ল্যান্ড প্লট')} />
                        {verificationErrors.propertyName && <small className="error-text">{text('Property name is required.', 'সম্পত্তির নাম আবশ্যক।')}</small>}
                      </div>

                      <div className="field">
                        <label htmlFor="ownerName">{text('Deed owner name (optional, distinct from property title)', 'দলিলে উল্লেখিত মালিকের নাম (ঐচ্ছিক)')}</label>
                        <input id="ownerName" name="ownerName" value={verificationForm.ownerName} onChange={(event) => handleVerificationInput('ownerName', event.target.value)} placeholder={text('Enter only if known', 'জানা থাকলে লিখুন')} />
                      </div>

                      <div className="field">
                        <label htmlFor="district">{text('District', 'জেলা')}</label>
                        <input id="district" name="district" value={verificationForm.district} onChange={(event) => handleVerificationInput('district', event.target.value)} placeholder={text('Pabna', 'পাবনা')} />
                        {verificationErrors.district && <small className="error-text">{text('District is required.', 'জেলা আবশ্যক।')}</small>}
                      </div>

                      <div className="field">
                        <label htmlFor="upazila">{text('Upazila', 'উপজেলা')}</label>
                        <input id="upazila" name="upazila" value={verificationForm.upazila} onChange={(event) => handleVerificationInput('upazila', event.target.value)} placeholder={text('Sadar', 'সদর')} />
                        {verificationErrors.upazila && <small className="error-text">{text('Upazila is required.', 'উপজেলা আবশ্যক।')}</small>}
                      </div>

                      <div className="field">
                        <label htmlFor="mouza">{text('Mouza', 'মৌজা')}</label>
                        <input id="mouza" name="mouza" value={verificationForm.mouza} onChange={(event) => handleVerificationInput('mouza', event.target.value)} placeholder={text('Bharatpur', 'ভারতপুর')} />
                        {verificationErrors.mouza && <small className="error-text">{text('Mouza is required.', 'মৌজা আবশ্যক।')}</small>}
                      </div>

                      <div className="field">
                        <label htmlFor="khatianNumber">{text('Khatian number', 'খতিয়ান নম্বর')}</label>
                        <input id="khatianNumber" name="khatianNumber" value={verificationForm.khatianNumber} onChange={(event) => handleVerificationInput('khatianNumber', event.target.value)} placeholder="K-221/445" />
                        {verificationErrors.khatianNumber && <small className="error-text">{text('Khatian number is required.', 'খতিয়ান নম্বর আবশ্যক।')}</small>}
                      </div>

                      <div className="field">
                        <label htmlFor="dagNumber">{text('Dag number', 'দাগ নম্বর')}</label>
                        <input id="dagNumber" name="dagNumber" value={verificationForm.dagNumber} onChange={(event) => handleVerificationInput('dagNumber', event.target.value)} placeholder="Dag 18" />
                        {verificationErrors.dagNumber && <small className="error-text">{text('Dag number is required.', 'দাগ নম্বর আবশ্যক।')}</small>}
                      </div>

                      <div className="field full-width">
                        <label htmlFor="landArea">{text('Land area', 'জমির পরিমাণ')}</label>
                        <input id="landArea" name="landArea" value={verificationForm.landArea} onChange={(event) => handleVerificationInput('landArea', event.target.value)} placeholder="1.26 bigha" />
                        {verificationErrors.landArea && <small className="error-text">{text('Land area is required.', 'জমির পরিমাণ আবশ্যক।')}</small>}
                      </div>
                    </div>
                  </div>
                )}

                {verificationStep === 2 && (
                  <div className="verification-form">
                    <div className="upload-box verification-upload-box">
                      <div className="upload-dropzone compact-upload-zone">
                        <p>{text('Upload available land documents such as the deed, khatian, mutation record, or tax receipt.', 'দলিল, খতিয়ান, নামজারি রেকর্ড বা ভূমি উন্নয়ন করের রসিদের মতো নথি আপলোড করুন।')}</p>
                        <label className="primary-button file-upload-button">
                          <span>{text('Select files', 'ফাইল নির্বাচন করুন')}</span>
                          <input type="file" accept=".pdf,.png,.jpg,.jpeg,.docx" multiple onChange={handleVerificationDocuments} />
                        </label>
                        <p className="verification-note">{text('Files are analyzed temporarily. Raw documents are not stored by this local server. OCR requires Tesseract. There is no government verification.', 'ফাইল অস্থায়ীভাবে বিশ্লেষণ করা হয়, এই লোকাল সার্ভারে মূল দলিল সংরক্ষিত হয় না। OCR-এর জন্য Tesseract প্রয়োজন। সরকারি যাচাই হয় না।')}</p>
                      </div>
                      {verificationErrors.documents && <small className="error-text">{verificationErrors.documents}</small>}
                    </div>

                    {verificationForm.documents.length > 0 && (
                      <div className="document-list">
                        {verificationForm.documents.map((file) => (
                          <span key={`${file.name}-${file.size}`} className="file-badge">
                            {file.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {verificationStep === 3 && (
                  <div className="verification-form">
                    <div className="verification-review-grid">
                      <div className="result-panel">
                        <h4>{text('Provided information', 'প্রদত্ত তথ্য')}</h4>
                        <ul>
                          <li><strong>{text('Property name:', 'সম্পত্তির নাম:')}</strong> {verificationForm.propertyName || text('Not provided', 'প্রদান করা হয়নি')}</li>
                          <li><strong>{text('Owner name (if supplied):', 'মালিকের নাম (যদি দেওয়া হয়):')}</strong> {verificationForm.ownerName || text('Not provided', 'প্রদান করা হয়নি')}</li>
                          <li><strong>{text('District:', 'জেলা:')}</strong> {verificationForm.district || text('Not provided', 'প্রদান করা হয়নি')}</li>
                          <li><strong>{text('Upazila:', 'উপজেলা:')}</strong> {verificationForm.upazila || text('Not provided', 'প্রদান করা হয়নি')}</li>
                          <li><strong>{text('Mouza:', 'মৌজা:')}</strong> {verificationForm.mouza || text('Not provided', 'প্রদান করা হয়নি')}</li>
                          <li><strong>{text('Khatian:', 'খতিয়ান:')}</strong> {verificationForm.khatianNumber || text('Not provided', 'প্রদান করা হয়নি')}</li>
                          <li><strong>{text('Dag:', 'দাগ:')}</strong> {verificationForm.dagNumber || text('Not provided', 'প্রদান করা হয়নি')}</li>
                          <li><strong>{text('Land area:', 'জমির পরিমাণ:')}</strong> {verificationForm.landArea || text('Not provided', 'প্রদান করা হয়নি')}</li>
                        </ul>
                      </div>

                      <div className="result-panel">
                        <h4>{text('Available evidence', 'উপলভ্য প্রমাণ')}</h4>
                        {verificationForm.documents.length > 0 ? (
                          <ul>
                            {verificationForm.documents.map((file) => (
                              <li key={`${file.name}-${file.size}`}>{file.name}</li>
                            ))}
                          </ul>
                        ) : (
                          <p>{text('No documents have been uploaded yet.', 'এখনো কোনো নথি আপলোড করা হয়নি।')}</p>
                        )}
                      </div>
                    </div>
                    <div className="landguard-safety-note">
                      <strong>{text('Authorized use only', 'শুধু অনুমোদিত ব্যবহার')}</strong>
                      <label className="privacy-label">
                        {text('Purpose:', 'যাচাইয়ের উদ্দেশ্য:')}
                        <select value={verificationPurpose} onChange={(event) => setVerificationPurpose(event.target.value)}>
                          <option value="purchase_due_diligence">{text('Land purchase due diligence', 'জমি কেনার আগে যাচাই')}</option>
                          <option value="own_records">{text('Review my own records', 'নিজের রেকর্ড পর্যালোচনা')}</option>
                          <option value="professional_review">{text('Authorized professional review', 'অনুমোদিত পেশাগত পর্যালোচনা')}</option>
                        </select>
                      </label>
                      <label className="privacy-checkbox">
                        <input type="checkbox" checked={authorityAttested} onChange={(event) => setAuthorityAttested(event.target.checked)} />
                        <span>{text('I lawfully obtained these documents, have permission to submit them, and will not use the service to harass or unlawfully access anyone’s information.', 'আমি নথিগুলো বৈধভাবে পেয়েছি ও জমা দেওয়ার অনুমতি আছে; কারও তথ্য বেআইনিভাবে নেওয়া বা হয়রানি করব না।')}</span>
                      </label>
                      <p>{text('This statement is not proof of consent. No private government record search is available.', 'এই ঘোষণা নিজে অনুমতির প্রমাণ নয়। ব্যক্তিগত সরকারি রেকর্ড খোঁজার সুবিধা নেই।')}</p>
                      {extractionError && <p role="alert" className="error-text">{extractionError}</p>}
                    </div>
                  </div>
                )}

                {verificationStep === 4 && verificationResult && (
                  <div className="verification-form">
                    <div className="result-grid">
                      <div className="result-panel">
                        <div className="result-header-row">
                          <h4>{text('Verification result', 'যাচাইয়ের ফলাফল')}</h4>
                          <span className="sample-badge">{text(sampleDataNotice, 'নমুনা / ডেমো ডেটা')}</span>
                        </div>
                        <ul>
                          <li><strong>{text('Property:', 'সম্পত্তি:')}</strong> {verificationResult.propertyName}</li>
                          <li><strong>{text('Location:', 'অবস্থান:')}</strong> {verificationResult.district}, {verificationResult.upazila}</li>
                          <li><strong>{text('Mouza:', 'মৌজা:')}</strong> {verificationResult.mouza}</li>
                          <li><strong>{text('Khatian:', 'খতিয়ান:')}</strong> {verificationResult.khatianNumber}</li>
                          <li><strong>{text('Dag:', 'দাগ:')}</strong> {verificationResult.dagNumber}</li>
                          <li><strong>{text('Land area:', 'জমির পরিমাণ:')}</strong> {verificationResult.landArea}</li>
                        </ul>
                        <p className="source-note"><strong>{text('Local document analysis only — NOT OFFICIALLY VERIFIED.', 'শুধু স্থানীয় নথি বিশ্লেষণ — সরকারি যাচাই হয়নি।')}</strong> {text(governmentVerificationNotice, 'এই প্রোটোটাইপে সরকারি রেকর্ড যাচাই করা হয়নি।')}</p>
                      </div>

                      <div className="result-panel">
                        <h4>{text('Missing evidence', 'অনুপস্থিত প্রমাণ')}</h4>
                        {verificationResult.missingEvidence.length > 0 ? (
                          <ul>
                            {verificationResult.missingEvidence.map((item) => (
                              <li key={item}>{translateVerificationMessage(item, language)}</li>
                            ))}
                          </ul>
                        ) : (
                          <p>{text('No missing evidence in the current draft.', 'বর্তমান খসড়ায় কোনো প্রমাণ অনুপস্থিত নেই।')}</p>
                        )}
                      </div>

                      <div className="result-panel">
                        <h4>{text('Possible inconsistencies', 'সম্ভাব্য অসংগতি')}</h4>
                        {verificationResult.possibleInconsistencies.length > 0 ? <ul>
                          {verificationResult.possibleInconsistencies.map((item) => (
                            <li key={item}>{translateVerificationMessage(item, language)}</li>
                          ))}
                        </ul> : <p>{text('No mismatch was established by the supplied comparison.', 'প্রদত্ত নথি ও তথ্যের তুলনায় কোনো অমিল নিশ্চিত হয়নি।')}</p>}
                      </div>

                      <div className="result-panel">
                        <h4>{text('Risk warnings', 'ঝুঁকির সতর্কতা')}</h4>
                        {verificationResult.riskWarnings.length > 0 ? <ul>
                          {verificationResult.riskWarnings.map((item) => (
                            <li key={item}>{translateVerificationMessage(item, language)}</li>
                          ))}
                        </ul> : <p>{text('No specific warning established by this local check; authenticity remains unverified.', 'এই স্থানীয় বিশ্লেষণে নির্দিষ্ট সতর্কতা শনাক্ত হয়নি; দলিলের সত্যতা নিশ্চিত করা হয়নি।')}</p>}
                      </div>

                      {verificationResult.documentComparison && (
                        <div className="result-panel full-width">
                          <h4>{text('Evidence comparison', 'প্রমাণের তুলনা')}</h4>
                          {verificationResult.documentComparison.status === 'unreadable' ? (
                            <p>{verificationResult.documentComparison.message}</p>
                          ) : (
                            <>
                              <div className="match-grid">
                                <div className="comparison-group">
                                  <h5>{text('Matched fields', 'মিলে যাওয়া তথ্য')}</h5>
                                  {verificationResult.documentComparison.matched.length > 0 ? (
                                    <ul className="comparison-list">
                                      {verificationResult.documentComparison.matched.map((item) => (
                                        <li key={`${item.field}-${item.filename || 'file'}`}>
                                          <div className="meta-line"><strong>{item.field}</strong><span>{item.filename ? `${text('Source', 'উৎস')}: ${item.filename}` : text('Source: uploaded document', 'উৎস: আপলোড করা নথি')}</span></div>
                                          <div className="value-row"><span>{text('Extracted:', 'উদ্ধার করা তথ্য:')}</span><strong>{item.value ?? text('Not available', 'পাওয়া যায়নি')}</strong></div>
                                          {item.evidence && <p className="evidence-snippet">{item.evidence}</p>}
                                        </li>
                                      ))}
                                    </ul>
                                  ) : (
                                    <p>{text('No matched fields were extracted.', 'কোনো মিলে যাওয়া তথ্য উদ্ধার করা যায়নি।')}</p>
                                  )}
                                </div>

                                <div className="comparison-group">
                                  <h5>{text('Mismatched fields', 'অমিল তথ্য')}</h5>
                                  {verificationResult.documentComparison.mismatched.length > 0 ? (
                                    <ul className="comparison-list">
                                      {verificationResult.documentComparison.mismatched.map((item) => (
                                        <li key={`${item.field}-${item.filename || 'file'}`}>
                                          <div className="meta-line"><strong>{item.field}</strong><span>{item.filename ? `${text('Source', 'উৎস')}: ${item.filename}` : text('Source: uploaded document', 'উৎস: আপলোড করা নথি')}</span></div>
                                          <div className="value-row"><span>{text('Expected:', 'প্রত্যাশিত:')}</span><strong>{item.expected ?? text('Not provided', 'প্রদান করা হয়নি')}</strong></div>
                                          <div className="value-row"><span>{text('Extracted:', 'উদ্ধার করা তথ্য:')}</span><strong>{item.actual ?? text('Not found', 'পাওয়া যায়নি')}</strong></div>
                                          {item.evidence && <p className="evidence-snippet">{item.evidence}</p>}
                                        </li>
                                      ))}
                                    </ul>
                                  ) : (
                                    <p>{text('No mismatched fields detected in the extracted text.', 'উদ্ধার করা তথ্যে কোনো অমিল পাওয়া যায়নি।')}</p>
                                  )}
                                </div>

                                <div className="comparison-group">
                                  <h5>{text('Ambiguous values', 'দ্ব্যর্থক তথ্য')}</h5>
                                  {verificationResult.documentComparison.ambiguous.length > 0 ? (
                                    <ul className="comparison-list">
                                      {verificationResult.documentComparison.ambiguous.map((item) => (
                                        <li key={`${item.field}-${item.filename || 'file'}`}>
                                          <div className="meta-line"><strong>{item.field}</strong><span>{item.filename ? `${text('Source', 'উৎস')}: ${item.filename}` : text('Source: uploaded document', 'উৎস: আপলোড করা নথি')}</span></div>
                                          <div className="value-row"><span>{text('Expected:', 'প্রত্যাশিত:')}</span><strong>{item.expected ?? text('Not provided', 'প্রদান করা হয়নি')}</strong></div>
                                          <div className="value-row"><span>{text('Extracted:', 'উদ্ধার করা তথ্য:')}</span><strong>{item.actual ?? text('Not found', 'পাওয়া যায়নি')}</strong></div>
                                          <p className="warning-copy">{item.reason ?? text('This value is ambiguous and needs human review.', 'এই তথ্যটি দ্ব্যর্থক; ম্যানুয়াল পর্যালোচনা প্রয়োজন।')}</p>
                                        </li>
                                      ))}
                                    </ul>
                                  ) : (
                                    <p>{text('No ambiguous field values were detected.', 'কোনো দ্ব্যর্থক তথ্য শনাক্ত হয়নি।')}</p>
                                  )}
                                </div>

                                <div className="comparison-group">
                                  <h5>{text('Not extracted', 'উদ্ধার করা যায়নি')}</h5>
                                  {verificationResult.documentComparison.not_extracted.length > 0 ? (
                                    <ul className="comparison-list">
                                      {verificationResult.documentComparison.not_extracted.map((item) => (
                                        <li key={`${item.field}-${item.filename || 'file'}`}>
                                          <div className="meta-line"><strong>{item.field}</strong><span>{item.filename ? `${text('Source', 'উৎস')}: ${item.filename}` : text('Source: uploaded document', 'উৎস: আপলোড করা নথি')}</span></div>
                                          <p className="warning-copy">{text('Expected value:', 'প্রত্যাশিত তথ্য:')} {item.expected || text('Not provided', 'প্রদান করা হয়নি')}. {text('The field could not be extracted from the uploaded document.', 'আপলোড করা নথি থেকে এই তথ্যটি উদ্ধার করা যায়নি।')}</p>
                                        </li>
                                      ))}
                                    </ul>
                                  ) : (
                                    <p>{text('All expected fields were successfully extracted from the uploaded evidence.', 'আপলোড করা প্রমাণ থেকে সব প্রত্যাশিত তথ্য উদ্ধার করা হয়েছে।')}</p>
                                  )}
                                </div>

                                <div className="comparison-group full-span">
                                  <h5>{text('Extracted evidence', 'উদ্ধার করা প্রমাণ')}</h5>
                                  {verificationResult.documentComparison.documents.some((document) => Object.keys(document.field_evidence ?? {}).length > 0) ? (
                                    <ul className="comparison-list">
                                      {verificationResult.documentComparison.documents.flatMap((document) =>
                                        Object.entries(document.field_evidence ?? {}).map(([field, evidence]) => (
                                          <li key={`${document.filename}-${field}`}>
                                            <div className="meta-line"><strong>{field}</strong><span>{document.filename}</span></div>
                                            <p className="evidence-snippet">{evidence}</p>
                                          </li>
                                        ))
                                      )}
                                    </ul>
                                  ) : (
                                    <p>{text('No supported evidence text could be extracted from the uploaded files.', 'আপলোড করা ফাইল থেকে সমর্থিত কোনো প্রমাণের লেখা উদ্ধার করা যায়নি।')}</p>
                                  )}
                                </div>
                              </div>
                              <p className="verification-note">{verificationResult.documentComparison.message}</p>
                            </>
                          )}
                        </div>
                      )}

                      <div className="result-panel full-width">
                        <h4>{text('Recommended next steps', 'পরবর্তী করণীয়')}</h4>
                        <ul>
                          {verificationResult.recommendedNextSteps.map((item) => (
                            <li key={item}>{translateVerificationMessage(item, language)}</li>
                          ))}
                        </ul>
                        <p className="verification-note">{text('This prototype uses local document text extraction, OCR only when Tesseract is installed and configured, and does not perform official government verification or legal ownership confirmation.', 'এখানে নথি থেকে লেখা উদ্ধার ও তুলনা করা হয়। স্ক্যান করা নথির জন্য Tesseract OCR প্রয়োজন হতে পারে।')}</p>
                      </div>

                      <div className="result-panel full-width">
                        <h4>{text('Report actions', 'রিপোর্টের কাজ')}</h4>
                        <div className="report-actions" aria-live="polite">
                          <button type="button" className="primary-button" onClick={handleCopyReport}>{text('Copy Report', 'রিপোর্ট কপি করুন')}</button>
                          <button type="button" className="secondary-button" onClick={handleDownloadPdf}>{text('Print / Save PDF', 'প্রিন্ট / PDF হিসেবে সংরক্ষণ')}</button>
                          <button type="button" className="secondary-button" onClick={handleShareReport}>{text('Share Report', 'রিপোর্ট শেয়ার করুন')}</button>
                        </div>
                        {reportExportMessage && (
                          <p className="verification-note">{localizeMessage(reportExportMessage, {
                            'Verification report copied to clipboard.': 'যাচাই প্রতিবেদন ক্লিপবোর্ডে কপি করা হয়েছে।',
                            'Copy failed. Please try again or use the browser share option.': 'কপি করা যায়নি। আবার চেষ্টা করুন অথবা ব্রাউজারের শেয়ার অপশন ব্যবহার করুন।',
                            'PDF report downloaded.': 'PDF প্রতিবেদন ডাউনলোড হয়েছে।',
                            'Verification report shared successfully.': 'যাচাই প্রতিবেদন সফলভাবে শেয়ার করা হয়েছে।',
                            'Sharing is not supported in this browser, so the report text was copied to your clipboard instead.': 'এই ব্রাউজারে শেয়ার করা যায় না, তাই প্রতিবেদনের লেখা ক্লিপবোর্ডে কপি করা হয়েছে।',
                            'Unable to share directly. The report text was copied to your clipboard instead.': 'সরাসরি শেয়ার করা যায়নি। প্রতিবেদনের লেখা ক্লিপবোর্ডে কপি করা হয়েছে।',
                            'Sharing and copying are both unavailable in this browser.': 'এই ব্রাউজারে শেয়ার ও কপি—দুটিই করা যাচ্ছে না।',
                          })}</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <div className="verification-actions">
                  {verificationStep > 1 && verificationStep < 4 && (
                    <button type="button" className="secondary-button" onClick={handleVerificationBack}>
                      {text('Back', 'পেছনে')}
                    </button>
                  )}

                  {extractionError && verificationStep === 4 && (
                    <div className="error-banner">{localizeMessage(extractionError, {
                      'Document extraction could not be completed. Please upload a valid PDF, image, or text file and try again.': 'নথি থেকে তথ্য উদ্ধার করা যায়নি। একটি বৈধ PDF, ছবি বা টেক্সট ফাইল আপলোড করে আবার চেষ্টা করুন।',
                    })}</div>
                  )}

                  {verificationStep === 4 ? (
                    <>
                      <button type="button" className="secondary-button" onClick={() => setVerificationStep(3)}>
                        {text('Back to Review', 'পর্যালোচনায় ফিরে যান')}
                      </button>
                      <button type="button" className="primary-button" onClick={resetVerificationWizard}>
                        {text('Close', 'বন্ধ করুন')}
                      </button>
                    </>
                  ) : (
                    <>
                      <button type="button" className="secondary-button" onClick={resetVerificationWizard}>
                        {text('Cancel', 'বাতিল')}
                      </button>
                      <button type="button" className="primary-button" onClick={() => { void handleVerificationNext(); }} disabled={extractionLoading}>
                        {extractionLoading ? text('Processing...', 'প্রক্রিয়াকরণ চলছে...') : verificationStep === 3 ? text('Submit', 'জমা দিন') : text('Next', 'পরবর্তী')}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>

        <section id="dashboard" className="stats-section">
          <div className="stat-grid">
            {stats.map((stat) => (
              <div key={stat.label} className="stat-box">
                <span>{language === 'bn' ? ({
                  'Properties viewed': 'দেখা সম্পত্তি',
                  'Saved properties': 'সংরক্ষিত সম্পত্তি',
                  'Verification requests': 'যাচাইয়ের অনুরোধ',
                  'Completed checks': 'সম্পন্ন যাচাই',
                  'Processed local checks': 'স্থানীয় বিশ্লেষণ সম্পন্ন',
                  'Pending checks': 'অপেক্ষমাণ যাচাই',
                  'Unreadable uploads': 'অপাঠ্য নথি',
                  'Unresolved issues': 'অমীমাংসিত বিষয়',
                  'Needs follow-up review': 'পুনরায় পর্যালোচনা প্রয়োজন',
                }[stat.label] ?? stat.label) : stat.label}</span>
                <strong>{stat.value}</strong>
              </div>
            ))}
          </div>
        </section>

        {authSession.user_role !== 'buyer' && <section id="demo-registry" className="landguard-demo-workspace card">
          <div className="section-header">
            <div>
              <p className="eyebrow">SMART LANDGUARD BD 2.0</p>
              <h2>{text('Land record comparison and private document management', 'জমির তথ্য যাচাই ও ব্যক্তিগত নথি ব্যবস্থাপনা')}</h2>
              <p>{text('The sample registry records are fictional. Documents uploaded by users may not be fictional; use sample files only. No official verification is available.', 'এই সিস্টেমে পরীক্ষামূলক ভূমি রেকর্ড ব্যবহৃত হয়। শুধু নমুনা নথি আপলোড করুন। এখানে সরকারি ডেটাবেসের সঙ্গে সরাসরি যাচাইয়ের সুবিধা নেই।')}</p>
              {authSession?.user_id && <p><strong>User ID:</strong> {authSession.user_id}</p>}
            </div>
            <span className="report-status">{text('DEMO ONLY — NOT GOVERNMENT VERIFIED', 'শুধু ডেমো — সরকারি যাচাই নয়')}</span>
          </div>
          {!authSession ? (
            <div className="moderation-empty-state">
              <div><h3>{text('Sign in to compare land data and manage documents', 'জমির তথ্য যাচাই ও নথি ব্যবস্থাপনার জন্য লগইন করুন')}</h3>
                <p>{text('Register as a new buyer or sign in to your account. Seller and Admin accounts are issued by an authorized operator.', 'নতুন ব্যবহারকারী হিসেবে নিবন্ধন করুন অথবা লগইন করুন। Seller ও Admin অ্যাকাউন্ট অনুমোদিত পরিচালক তৈরি করেন।')}</p>
                <button className="primary-button" type="button" onClick={() => { setRegisterMode(true);setLoginError('');setLoginOpen(true); }}>{text('Create account', 'নতুন অ্যাকাউন্ট তৈরি করুন')}</button>
              </div>
            </div>
          ) : (
            <div className="demo-workspace-layout">
              <article className="demo-workspace-card">
                <h3>{text('Synthetic sample registry', 'নমুনা জমির নমুনা রেকর্ড')}</h3>
                <p>{text('Select one of the invented records, enter matching fields and run a local comparison.', 'একটি নমুনা রেকর্ড বাছাই করে তথ্য লিখে ডেমো তুলনা করুন।')}</p>
                <form onSubmit={submitDemoCheck} className="demo-stack">
                  <label>{text('Search fictional records', 'নমুনা রেকর্ড খুঁজুন')}
                    <input value={registrySearch} onChange={e=>setRegistrySearch(e.target.value)} placeholder="DEMO-LR-1001, Mouza, District"/>
                  </label>
                  <label>{text('Demo record', 'ডেমো রেকর্ড')}
                    <select value={selectedDemoRecord} onChange={e => setSelectedDemoRecord(e.target.value)} required>
                      <option value="">{text('Choose fictional record', 'নমুনা রেকর্ড বাছাই করুন')}</option>
                      {registry.filter(r=> !registrySearch || Object.values(r).some(v=>String(v).toLowerCase().includes(registrySearch.trim().toLowerCase()))).map(r => <option value={r.id} key={r.id}>{r.id} · {r.district} · {r.mouza}</option>)}
                    </select>
                  </label>
                  {selectedDemoRecord && <p className="demo-record-preview">{text('Sample registry values:', 'ডেমো রেকর্ডের নমুনা তথ্য:')}
                    {' '}{Object.entries(registry.find(r=>r.id===selectedDemoRecord) || {}).filter(([key])=>['owner_name','mouza','khatian','dag','land_area'].includes(key)).map(([key,value])=>`${key}: ${value}`).join(' · ')}
                  </p>}
                  {(['owner_name','district','mouza','khatian','dag','land_area'] as const).map(key => (
                    <label key={key}>{key.replace(/_/g,' ')}
                      <input value={demoValues[key]} onChange={e=>setDemoValues(old=>({...old,[key]:e.target.value}))} maxLength={120} placeholder={text('Enter sample text', 'ডেমো তথ্য লিখুন')}/>
                    </label>
                  ))}
                  <div className="demo-form-actions">
                    <button type="submit" className="primary-button">{text('Check demo record (not official)', 'ডেমো তথ্য মিলিয়ে দেখুন')}</button>
                    <button type="button" className="secondary-button" onClick={resetDemoComparison}>{text('Clear comparison form', 'ফর্ম পরিষ্কার করুন')}</button>
                  </div>
                </form>
                {currentDemoResult && <p className="demo-current-result" role="status">{currentDemoResult}</p>}
                <button type="button" className="secondary-button demo-history-toggle"
                  aria-expanded={showSavedDemoHistory} onClick={() => setShowSavedDemoHistory(v => !v)}>
                  {showSavedDemoHistory ? text('Hide saved history', 'সংরক্ষিত ইতিহাস লুকান') : text('Show saved history', 'সংরক্ষিত ইতিহাস দেখুন')}
                  {' '}({registryHistory.length})
                </button>
                {showSavedDemoHistory && <>
                <h4>{text('My demo check history', 'আমার ডেমো যাচাইয়ের ইতিহাস')}</h4>
                <div className="demo-history">
                  {registryHistory.length === 0 ? <p>{text('No checks yet.', 'এখনো কোনো যাচাই নেই।')}</p> : registryHistory.slice(0,8).map(item=>(
                    <p key={item.id}><strong>{item.record_id}</strong> · {item.result} · {item.created_at.slice(0,10)}</p>
                  ))}
                </div>
                <h4>{text('My document evidence review activity', 'আমার নথি বিশ্লেষণের ইতিহাস')}</h4>
                <div className="demo-history">
                  {extractionHistory.length ? extractionHistory.slice(0,8).map(item=><p key={item.id}>
                    {item.created_at.slice(0,10)} · {item.purpose} · {item.evidence_status} · {text('Not government checked','সরকারি যাচাই হয়নি')}
                  </p>) : <p>{text('No document evidence activity yet.','এখনো নথি বিশ্লেষণের ইতিহাস নেই।')}</p>}
                </div>
                </>}
              </article>
              {authSession.user_role === 'admin' && <article className="demo-workspace-card demo-admin-card">
                <h3>{text('Admin: fictional registry management', 'অ্যাডমিন: নমুনা রেকর্ড পরিচালনা')}</h3>
                <p>{text('Cannot access users’ private documents. All additions are explicitly marked DEMO.', 'ব্যবহারকারীর ব্যক্তিগত নথি দেখতে পারবেন না। সব সংযোজন DEMO হিসেবে চিহ্নিত।')}</p>
                {adminSummary && <p className="demo-summary">{Object.entries(adminSummary).map(([key,value])=><span key={key}>{key.replace(/_/g,' ')}: <strong>{value}</strong></span>)}</p>}
                <div className="demo-admin-record-list">
                  {registry.slice(0, showAllAdminRecords ? registry.length : 4).map(item=><div className="demo-file-row" key={item.id}><span>{item.id} · {item.mouza}</span>
                    <button type="button" onClick={async ()=>{
                      if (!window.confirm(text('Deactivate this sample?', 'এই নমুনা রেকর্ড নিষ্ক্রিয় করবেন?'))) return;
                      try { await demoWrite(`/demo-registry/admin/${encodeURIComponent(item.id)}`,'DELETE'); await fetchDemoWorkspace(); setDemoStatus('Demo record disabled.'); }
                      catch(e) { setDemoStatus(e instanceof Error ? e.message:'Action failed'); }
                    }}>{text('Deactivate', 'নিষ্ক্রিয়')}</button></div>)}
                  {registry.length > 4 && <button type="button" className="secondary-button demo-show-more" aria-expanded={showAllAdminRecords} onClick={() => setShowAllAdminRecords(current => !current)}>
                    {showAllAdminRecords ? text('Show less', 'কম দেখুন') : text(`Show more (${registry.length - 4} remaining)`, `আরও দেখুন (${registry.length - 4}টি)`)}
                  </button>}
                </div>
                <form className="demo-stack" onSubmit={createAdminRecord}>
                  {(['owner_name','district','upazila','mouza','khatian','dag','land_area'] as const).map(key=>(
                    <label key={key}>{key.replace(/_/g,' ')}
                      <input required minLength={2} maxLength={100} value={adminRecord[key]} onChange={e=>setAdminRecord(old=>({...old,[key]:e.target.value}))} placeholder="Invented data only"/>
                    </label>
                  ))}
                  <div className="demo-form-actions">
                    <button type="submit" className="primary-button">{text('Add fictional demo record','নমুনা রেকর্ড যুক্ত করুন')}</button>
                    <button type="button" className="secondary-button" onClick={() => resetAdminRecord(true)}>{text('Clear form / new entry', 'নতুন তথ্য লিখুন / ফর্ম পরিষ্কার')}</button>
                  </div>
                </form>
              </article>}
            </div>
          )}
          <div className="demo-bottom-tools">
            {authSession && <button type="button" className="secondary-button" onClick={()=>void refreshDemo()}>{text('Refresh demo workspace', 'ডেমো তথ্য রিফ্রেশ করুন')}</button>}
            {demoStatus && <p role="status" aria-live="polite">{demoStatus}</p>}
          </div>
        </section>}

        <section id="my-documents" className="landguard-demo-workspace card">
          <div className="section-header"><div><h2>{text('My private documents', 'আমার ব্যক্তিগত নথি')}</h2>
            <p>{text('Demo files only. Your files are not government-verified.', 'শুধু নমুনা নথি ব্যবহার করুন। এগুলো সরকারি যাচাইকৃত নয়।')}</p>
          </div></div>
          <div className="demo-workspace-layout">
              <article className="demo-workspace-card">
                <h3>{text('My encrypted demo documents', 'আমার এনক্রিপ্টেড ডেমো নথি')}</h3>
                <p>{text('Upload fictional files only. Files are private, encrypted and not shared automatically with Admin.', 'শুধু পরীক্ষামূলক নথি ব্যবহার করুন। ফাইল ব্যক্তিগত, এনক্রিপ্টেড এবং Admin-ও স্বয়ংক্রিয়ভাবে দেখতে পারেন না।')}</p>
                <form onSubmit={submitPrivateFile} className="demo-stack">
                  <label>{text('Sample PDF, DOCX or image (max 10 MB)', 'ডেমো PDF, DOCX বা ছবি (সর্বোচ্চ ১০ MB)')}
                    <input type="file" accept=".pdf,.docx,.png,.jpg,.jpeg" onChange={e=>setSelectedVaultFile(e.target.files?.[0]??null)}/>
                  </label>
                  <label className="demo-checkbox"><input type="checkbox" checked={vaultConsent} onChange={e=>setVaultConsent(e.target.checked)}/>
                    {text('I confirm this is fabricated demo data and I am authorized to upload it.', 'এটি পরীক্ষামূলক ডেমো তথ্য এবং আপলোডের অনুমতি আছে—আমি নিশ্চিত করছি।')}
                  </label>
                  <button className="primary-button" type="submit" disabled={!selectedVaultFile||!vaultConsent}>{text('Save encrypted demo file', 'এনক্রিপ্টেড ডেমো ফাইল রাখুন')}</button>
                </form>
                <label>{text('Share privately for 24 hours with another demo-user email', 'অন্য ডেমো ব্যবহারকারীর ইমেইলে ২৪ ঘণ্টার জন্য অনুমতি দিন')}
                  <input type="email" value={demoShareEmail} onChange={e=>setDemoShareEmail(e.target.value)} placeholder="other-demo@example.test"/>
                </label>
                <h4>{text('My documents', 'আমার নথি')}</h4>
                {vaultOwned.length ? vaultOwned.map(f=>(
                  <div className="demo-file-row" key={f.id}>
                    <span>{f.original_filename} <small>({Math.ceil(f.byte_count/1024)} KB)</small></span>
                    <div className="demo-file-buttons">
                      <button type="button" onClick={()=>void downloadPrivate(f.id)}>{text('Download','ডাউনলোড')}</button>
                      <button type="button" disabled={!demoShareEmail} onClick={()=>void doVaultAction(f.id,'grant')}>{text('Share','অনুমতি')}</button>
                      <button type="button" onClick={()=>void doVaultAction(f.id,'revoke')}>{text('Revoke','বাতিল')}</button>
                      <button type="button" onClick={()=>void doVaultAction(f.id,'delete')}>{text('Delete','মুছুন')}</button>
                    </div>
                  </div>
                )) : <p>{text('No stored demo files.', 'সংরক্ষিত ডেমো নথি নেই।')}</p>}
                <h4>{text('Shared with me (temporary)', 'আমাকে দেওয়া অস্থায়ী অনুমতি')}</h4>
                {vaultShared.length ? vaultShared.map(f=>(
                  <div className="demo-file-row" key={f.id}><span>{f.original_filename} · {f.expires_at?.slice(0,16)}</span>
                    <button type="button" onClick={()=>void downloadPrivate(f.id)}>{text('Download','ডাউনলোড')}</button></div>
                )) : <p>{text('No shared demo files.', 'শেয়ার করা ডেমো নথি নেই।')}</p>}
              </article>
          </div>
          {demoStatus && <p role="status">{demoStatus}</p>}
        </section>
        {showPropertyDetail && (
        <section className="purchase-panel card">
          <div className="section-header">
            <h2>{text('Purchase readiness checklist', 'ক্রয়ের প্রস্তুতি যাচাইতালিকা')}</h2>
            <span className="report-status">
              {purchaseChecklist ? text(`${purchaseChecklist.checklist.filter(step=>step.status==='done').length}/${purchaseChecklist.checklist.length} self-reported steps`, `${purchaseChecklist.checklist.filter(step=>step.status==='done').length}/${purchaseChecklist.checklist.length} ধাপ নথিভুক্ত`) : text('Checklist pending', 'যাচাইতালিকা প্রস্তুত হচ্ছে')}
            </span>
          </div>

          {purchaseChecklist ? (
            <>
              <div className="checklist-progress" aria-label={text('Purchase readiness progress', 'ক্রয়ের প্রস্তুতির অগ্রগতি')}>
                <div style={{ width: `${purchaseChecklist.checklist.length ? purchaseChecklist.checklist.filter(step=>step.status==='done').length / purchaseChecklist.checklist.length * 100 : 0}%` }} />
              </div>

              <div className="purchase-summary">
                <strong>{text('Buyer action checklist (demo)', 'ক্রেতার করণীয় যাচাইতালিকা (ডেমো)')}</strong>
                <span>{text('This is not a property safety score or an officially verified progress percentage.', 'এটি জমির নিরাপত্তার স্কোর নয় এবং কোনো সরকারি যাচাইয়ের অগ্রগতি নয়।')}</span>
              </div>

              <div className="checklist-grid">
                {purchaseChecklist.checklist.map((step) => (
                  <div key={step.id} className={`checklist-step ${step.status}`}>
                    <div className="checklist-topline">
                      <span className="step-tag">{text(step.urgency, step.urgency === 'Critical' ? 'অত্যন্ত জরুরি' : step.urgency === 'High' ? 'জরুরি' : 'মাঝারি')}</span>
                      <span className={`step-status ${step.status}`}>
                        {step.status === 'done' ? text('Marked done (demo)', 'ডেমোতে সম্পন্ন হিসেবে চিহ্নিত') : step.status === 'in_progress' ? text('In progress', 'চলমান') : text('Pending', 'অপেক্ষমাণ')}
                      </span>
                    </div>
                    <h4>{text(step.title, ({'Confirm seller identity and deed holder':'বিক্রেতা ও দলিলের মালিকের পরিচয় মিলিয়ে দেখুন','Review mutation history and transfer record':'নামজারি ও মালিকানা হস্তান্তরের ইতিহাস যাচাই করুন','Validate supporting documents':'দলিল, খতিয়ান ও করের সহায়ক কাগজপত্র দেখুন','Assess dispute and encumbrance signals':'মামলা, বিরোধ বা দায় আছে কি না যাচাই করুন','Validate tax, khatian, and agreement records':'কর, খতিয়ান ও চুক্তির তথ্য মিলিয়ে দেখুন','Arrange official verification before final registration':'নিবন্ধনের আগে সরকারি দপ্তরে যাচাই করুন'} as Record<string,string>)[step.title] ?? 'নমুনা নথি পর্যালোচনার ধাপ')}</h4>
                    <p>{text(step.detail, ({'Compare the seller name with the deed holder in this demo review.':'ডেমো দলিলে বিক্রেতার নাম ও মালিকের নাম মিলিয়ে দেখুন।','Check whether any mutation or transfer record is missing from the sample dataset.':'নামজারি বা হস্তান্তরের নথি অনুপস্থিত কি না পরীক্ষা করুন।','The available demo records were reviewed for consistency and basic mismatch warnings.':'ডেমো রেকর্ডে প্রাথমিক মিল ও অমিল পরীক্ষা করা হয়েছে; সরকারি যাচাই হয়নি।','Use the evidence summary and risk flags to decide whether more human review is needed.':'সম্ভাব্য অসংগতি নিয়ে যোগ্য ব্যক্তির পর্যালোচনা প্রয়োজন কি না দেখুন।'} as Record<string,string>)[step.detail] ?? 'এই ধাপে দলিল যাচাইয়ের উপযুক্ত প্রমাণ প্রয়োজন।')}</p>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p>{text('Preparing purchase checklist...', 'ক্রয়ের যাচাইতালিকা প্রস্তুত হচ্ছে...')}</p>
          )}
        </section>
        )}

        {authSession.user_role === 'admin' && <section id="admin-review" className="moderation-panel card">
          <div className="moderation-section-header">
            <div className="moderation-heading-copy">
              <p className="eyebrow">{text('ADMIN WORKSPACE', 'অ্যাডমিন ওয়ার্কস্পেস')}</p>
              <h2>{text('Admin moderation queue', 'অ্যাডমিন পর্যালোচনার তালিকা')}</h2>
              <p>{text('Sample moderation items only — no government data.', 'শুধু ডেমো পর্যালোচনার তথ্য—কোনো সরকারি ডেটা নয়।')}</p>
            </div>
            <span className="moderation-count">
              <span aria-hidden="true" />
              {text(`${moderationQueue.length} items`, `${moderationQueue.length}টি আইটেম`)}
            </span>
          </div>

          {authSession?.user_role !== 'admin' ? (
            <div className="moderation-empty-state">
              <div>
                <h3>{text('Admin login required', 'অ্যাডমিন লগইন প্রয়োজন')}</h3>
                <p>{text('Sign in with an authorized admin account to view the moderation queue.', 'পর্যালোচনার তালিকা দেখতে অনুমোদিত অ্যাডমিন অ্যাকাউন্টে লগইন করুন।')}</p>
                {!authSession && <button type="button" className="secondary-button" onClick={() => setLoginOpen(true)}>{text('Admin login', 'অ্যাডমিন লগইন')}</button>}
              </div>
            </div>
          ) : moderationQueue.length > 0 ? (
            <div className="moderation-list">
              {moderationQueue.map((item) => (
                <div key={item.id} className="moderation-item">
                  <div className="moderation-header">
                    <div className="moderation-title">
                      <strong>{item.title}</strong>
                      <span>{item.property_id}</span>
                    </div>
                    <span className={`priority-badge ${item.priority.toLowerCase()}`}>{item.priority}</span>
                  </div>
                  <p>{item.reason}</p>
                  <div className="moderation-meta">
                    <span>{item.status}</span>
                    <span>{item.reviewer}</span>
                    <span>{item.updated_at}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="moderation-empty-state">
              <span className="moderation-empty-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M12 3.5 19 6v5.4c0 4.2-2.9 7.5-7 9.1-4.1-1.6-7-4.9-7-9.1V6l7-2.5Z" />
                  <path d="m8.8 12 2.1 2.1 4.4-4.5" />
                </svg>
              </span>
              <div>
                <h3>{text('Nothing needs review right now', 'এই মুহূর্তে পর্যালোচনার কিছু নেই')}</h3>
                <p>{text('Newly flagged records will appear here when they are available.', 'নতুন কোনো রেকর্ড পর্যালোচনার জন্য এলে এখানে দেখা যাবে।')}</p>
              </div>
            </div>
          )}
        </section>}
      </main>}

      <section className="landguard-privacy-bar" aria-label={text('Privacy and security', 'গোপনীয়তা ও নিরাপত্তা')}>
        <strong>{text('Your documents, your control', 'আপনার নথি, আপনার নিয়ন্ত্রণ')}</strong>
        <span>{text('Document uploads are processed temporarily; no government database is connected. Do not upload others’ private documents without authorization.', 'নথি অস্থায়ীভাবে বিশ্লেষণ করা হয়; সরকারি ডেটাবেস সংযুক্ত নয়। অনুমতি ছাড়া অন্যের ব্যক্তিগত দলিল আপলোড করবেন না।')}</span>
        {authSession && <details className="landguard-privacy-settings">
          <summary>{text('Account settings and privacy requests', 'অ্যাকাউন্ট সেটিংস ও গোপনীয়তার অনুরোধ')}</summary>
          <div className="landguard-privacy-buttons">
            <button type="button" className="secondary-button" onClick={() => submitPrivacyRequest('access')}>{text('Request my data', 'আমার তথ্য চাই')}</button>
            <button type="button" className="secondary-button" onClick={() => submitPrivacyRequest('delete')}>{text('Request deletion', 'তথ্য মুছতে চাই')}</button>
          </div>
        </details>}
        {privacyStatus && <p role="status">{privacyStatus}</p>}
      </section>

      <footer className="site-footer">
        <div className="footer-inner">
          <a className="footer-brand" href="#home">
            <span className="footer-logo"><img src={bangladeshOutline} alt="" /><i /></span>
            <span><strong>Smart LandGuard BD</strong><small>{text('Land verification, safe future', 'জমি যাচাই, নিরাপদ ভবিষ্যৎ')}</small></span>
          </a>
          <nav className="footer-nav" aria-label={text('Footer navigation', 'ফুটার নেভিগেশন')}>
            <a href="#home">{text('Home', 'হোম')}</a><a href="#features">{text('Services', 'সেবা সমূহ')}</a>{authSession ? <><a href="#verification">{text('Verify documents', 'দলিল যাচাই')}</a><a href="#dashboard">{text('Dashboard', 'ড্যাশবোর্ড')}</a><a href="#my-documents">{text('My documents', 'আমার নথি')}</a><a href="#reports">{text('Reports', 'রিপোর্ট')}</a></> : <a href="#help">{text('Help', 'সহায়তা')}</a>}
          </nav>
          <div className="footer-legal">
            <span>{text('© 2026 Smart LandGuard BD · Prototype project', '© 2026 Smart LandGuard BD · একটি প্রোটোটাইপ প্রকল্প')}</span>
            <span className="footer-divider">|</span>
            <span><span aria-hidden="true">◈</span> {text('Not a government database', 'সরকারি ডেটাবেস নয়')}</span>
          </div>
        </div>
      </footer>

      {loginOpen && (
        <div
          className="login-modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setLoginOpen(false);
            }
          }}
        >
          <section
            ref={loginDialogRef}
            className="login-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="login-modal-title"
          >
            <div className="login-modal-header">
              <div>
                <p className="eyebrow">Smart LandGuard BD</p>
                <h2 id="login-modal-title">{registerMode ? text('Create buyer demo account', 'নতুন অ্যাকাউন্ট তৈরি করুন (ডেমো)') : text('Log in to your account', 'অ্যাকাউন্টে লগইন করুন')}</h2>
              </div>
              <button
                ref={loginCloseButtonRef}
                type="button"
                className="login-modal-close"
                aria-label={text('Close login dialog', 'লগইন উইন্ডো বন্ধ করুন')}
                onClick={() => setLoginOpen(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleLogin}>
              {registerMode && <label className="login-modal-field">{text('Your name (demo only)', 'নাম (শুধু ডেমো)')}
                <input required minLength={2} value={registerName} onChange={event=>setRegisterName(event.target.value)} placeholder="Demo User" />
              </label>}
              <label className="login-modal-field">
                {text('Email address', 'ইমেইল ঠিকানা')}
                <input type="email" autoComplete="username" required value={loginEmail} onChange={(event) => setLoginEmail(event.target.value)} placeholder="name@example.com" />
              </label>
              <label className="login-modal-field">
                {text('Password', 'পাসওয়ার্ড')}
                <input type="password" autoComplete={registerMode ? 'new-password' : 'current-password'} required minLength={registerMode ? 12 : undefined} maxLength={registerMode ? 128 : undefined} value={loginPassword} onChange={(event) => setLoginPassword(event.target.value)} placeholder={text('Enter password (12+ characters for sign up)', 'পাসওয়ার্ড লিখুন (নতুন অ্যাকাউন্টে কমপক্ষে ১২ অক্ষর)')} />
              </label>
              {registerMode && <label className="demo-checkbox"><input type="checkbox" required checked={acceptDemoTerms} onChange={e=>setAcceptDemoTerms(e.target.checked)}/>
                {text('I will use only fictional demo information. I understand email/identity is not verified.', 'শুধু পরীক্ষামূলক ডেমো তথ্য ব্যবহার করব। এখানে ইমেইল/পরিচয় যাচাই হয় না।')}
              </label>}
              {loginError && <div className={`login-feedback ${loginError === 'registration_success' ? 'login-feedback--success' : ''}`} role="status" aria-live="polite">
                <strong>{loginError === 'registration_success' ? text('Account created', 'অ্যাকাউন্ট তৈরি হয়েছে') : registerMode ? text('Could not create account', 'অ্যাকাউন্ট তৈরি করা যাচ্ছে না') : text('Sign-in needs attention', 'লগইন সম্পন্ন করা যাচ্ছে না')}</strong>
                <p>{loginError === 'registration_success' ? text('Please log in with your new account.', 'এখন আপনার নতুন অ্যাকাউন্টে লগইন করুন।')
                  : loginError === 'invalid_credentials' ? text('The email or password does not match. Please check and try again.', 'ইমেইল অথবা পাসওয়ার্ড সঠিক নয়। আবার পরীক্ষা করে চেষ্টা করুন।')
                  : loginError === 'rate_limited' ? text(`For your security, sign-in is temporarily paused. Try again in about ${Math.ceil(loginRetrySeconds / 60)} minutes.`, `নিরাপত্তার জন্য লগইন সাময়িক সীমিত। প্রায় ${Math.ceil(loginRetrySeconds / 60)} মিনিট পর আবার চেষ্টা করুন।`)
                  : loginError === 'timeout' || loginError === 'connection_failed' ? text('The connection is taking longer than expected. Please try again shortly.', 'এই মুহূর্তে সংযোগে সমস্যা হচ্ছে। কিছুক্ষণ পর আবার চেষ্টা করুন।')
                  : loginError === 'csrf_failed' ? text('Your session has expired. Reload this page and try again.', 'আপনার সেশনের মেয়াদ শেষ হয়েছে। পেজ রিফ্রেশ করে আবার চেষ্টা করুন।')
                  : loginError === 'account_exists' ? text('An account already exists for this email. Please sign in instead.', 'এই ইমেইল দিয়ে আগে থেকেই অ্যাকাউন্ট রয়েছে। নতুন করে নিবন্ধন না করে লগইন করুন।')
                  : loginError === 'invalid_registration' ? text('Use a name of at least 2 characters, a valid email, and a password of 12–128 characters.', 'নাম কমপক্ষে ২ অক্ষর, সঠিক ইমেইল এবং ১২–১২৮ অক্ষরের পাসওয়ার্ড দিন।')
                  : loginError === 'terms_required' ? text('Please accept the demo use conditions to continue.', 'ডেমো ব্যবহারের শর্তগুলো নিশ্চিত করুন।')
                  : loginError === 'registration_rate_limited' ? text(`Too many registration requests. Try again in approximately ${Math.ceil(loginRetrySeconds / 60)} minutes.`, `অল্প সময়ে অনেকবার নিবন্ধনের চেষ্টা হয়েছে। প্রায় ${Math.ceil(loginRetrySeconds / 60)} মিনিট পরে চেষ্টা করুন।`)
                  : registerMode ? text('We could not create your account. Please try again later.', 'অ্যাকাউন্ট তৈরি করা যায়নি। কিছুক্ষণ পরে আবার চেষ্টা করুন।')
                  : text('We could not complete this request. Please try again later.', 'অনুরোধটি সম্পন্ন করা যায়নি। কিছুক্ষণ পর আবার চেষ্টা করুন।')}</p>
              </div>}
              <button type="submit" className="primary-button login-modal-submit" disabled={loginPending}>
                {loginPending ? text('Please wait...', 'অপেক্ষা করুন...') : registerMode ? text('Create demo account', 'ডেমো অ্যাকাউন্ট খুলুন') : text('Login', 'লগইন করুন')}
              </button>
            </form>
            <button type="button" className="secondary-button login-modal-dismiss" onClick={() => { setRegisterMode(!registerMode); setLoginError(''); setLoginPassword(''); }}>
              {registerMode ? text('Already registered? Log in', 'অ্যাকাউন্ট আছে? লগইন করুন') : text('Create a buyer account (demo)', 'নতুন অ্যাকাউন্ট তৈরি করুন (ডেমো)')}
            </button>
            <button type="button" className="secondary-button login-modal-dismiss" onClick={() => setLoginOpen(false)}>
              {text('Close', 'বন্ধ করুন')}
            </button>
          </section>
        </div>
      )}
    </div>
  );
}

export default App;
