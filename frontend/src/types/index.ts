export type Role = 'ADMIN' | 'DATA_ENGINEER' | 'VIEWER';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  is_superuser: boolean;
}

export interface Finding {
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  message: string;
  column?: string;
  evidence: Record<string, any>;
}

export interface EvidenceItem {
  evidence_id: string;
  finding_type: string;
  severity: string;
  message: string;
  evidence: Record<string, any>;
}

export interface RootCauseCandidate {
  cause: string;
  confidence: number;
  evidence: string[];
  affected_area: string;
  explanation: string;
  level?: string;
}

export interface Recommendation {
  id: string;
  category: string;
  priority: 'P0_CRITICAL' | 'P1_HIGH' | 'P2_MEDIUM' | 'P3_LOW';
  title: string;
  finding_ref: string;
  target_column: string;
  rationale: string;
  action_type: string;
  suggested_fix: string;
  impact: string;
}

export interface RecoveryCandidate {
  action_id: string;
  action_type: string;
  target_type: string;
  target: string;
  severity: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  policy_status: string;
  estimated_impact: string;
  action_parameters: Record<string, any>;
  remediation_code: string;
  required_role?: string;
}

export interface RecoveryExecutionResult {
  recovery_run_id: string;
  status: string;
  executed_by: string;
  user_role: string;
  actions_executed: Array<{
    action_id: string;
    action_type: string;
    target: string;
    status: string;
    [key: string]: any;
  }>;
  actions_skipped: Array<{
    action_id: string;
    action_type: string;
    target: string;
    status: string;
    reason: string;
    [key: string]: any;
  }>;
  dataset_path: string;
  remediated_file_path: string;
  remediated_file_hash: string;
  download_url: string;
  download_xlsx_url: string;
  download_csv_url: string;
  download_pdf_url: string;
  verification: VerificationResult;
  audit_trail_recorded: boolean;
}

export interface VerificationResult {
  engine: string;
  verified_at: string;
  verdict: 'PASS' | 'PARTIAL_PASS' | 'FAIL';
  metrics: {
    before_finding_count: number;
    after_finding_count: number;
    resolved_finding_count: number;
    anomaly_reduction_rate_pct: number;
    original_row_count: number;
    remediated_row_count: number;
    row_delta: number;
  };
  message: string;
  audit_trail: {
    pre_status: string;
    post_status: string;
    signed_off: boolean;
  };
}

export interface AuditReportInfo {
  pdf_report_path: string;
  pdf_filename: string;
  excel_report_path: string;
  excel_filename: string;
  generated_at: string;
}

export interface AuditDossier {
  id?: string;
  dataset_name?: string;
  created_at?: string;
  audit_status: string;
  highest_severity: string;
  dataset_path: string;
  row_count: number;
  column_count: number;
  inspection: {
    agent: string;
    status: string;
    highest_severity: string;
    finding_count: number;
    findings: Finding[];
    data_quality?: any;
    schema_drift?: any;
    ml_analysis?: any;
  };
  drift?: any;
  evidence: {
    engine: string;
    status: string;
    finding_count: number;
    evidence_count: number;
    evidence: EvidenceItem[];
  };
  root_cause: {
    agent: string;
    status: string;
    finding_count: number;
    primary_cause: string;
    overall_confidence: number;
    candidates: RootCauseCandidate[];
    summary: string;
  };
  recommendations: {
    recommendation_count: number;
    recommendations: Recommendation[];
  };
  recovery: {
    status: string;
    overall_policy: string;
    candidate_count: number;
    candidates: RecoveryCandidate[];
    summary: string;
  };
  reports?: AuditReportInfo;
}

export interface DashboardSummary {
  health_index: number;
  health_status: 'OPTIMAL' | 'DEGRADED' | 'CRITICAL_ATTENTION';
  formula_explanation?: string;
  kpis: {
    total_inspections: number;
    total_findings: number;
    total_etl_runs: number;
    critical_findings: number;
    high_findings: number;
    medium_findings: number;
    low_findings: number;
    active_agents?: number;
    total_agents?: number;
  };
  severity_distribution: Array<{
    severity: string;
    count: number;
    color: string;
  }>;
  recent_runs: Array<{
    id: string;
    dataset_path: string;
    friendly_name?: string;
    status: string;
    highest_severity: string;
    row_count: number;
    finding_count: number;
    created_at: string;
  }>;
}

export interface Alert {
  id: string;
  timestamp: string;
  severity: 'CRITICAL' | 'HIGH';
  dataset: string;
  finding_type: string;
  title: string;
  message: string;
  is_read: boolean;
}

export interface AgentStatus {
  name: string;
  role: string;
  status: 'ONLINE' | 'IDLE' | 'RUNNING' | 'ERROR' | 'OFFLINE';
  last_active: string;
  processed_count: number;
  memory_usage_mb: number;
}

export interface SwarmStatusResponse {
  agents: AgentStatus[];
  swarm_status: string;
  total_agents: number;
  active_agents: number;
}

export interface SystemHealth {
  status: 'HEALTHY' | 'DEGRADED';
  database: 'CONNECTED' | 'DISCONNECTED';
  runtime: string;
  active_agents: number;
  total_agents: number;
  version: string;
}

export interface BenchmarkDataset {
  id: string;
  name: string;
  category: string;
  records: number;
  file_path: string;
  description: string;
  tags: string[];
}

export interface SyntheticScenario {
  mode: string;
  name: string;
  category: string;
  description: string;
  anomalies: string[];
}

export interface GeneratedReport {
  filename: string;
  report_type: string;
  format: string;
  file_size: number;
  created_at: string;
  download_url: string;
}

export interface AuditSummaryItem {
  id: string;
  dataset_path: string;
  friendly_name: string;
  status: string;
  highest_severity: string;
  row_count: number;
  finding_count: number;
  created_at: string;
}

export interface RegisteredDataset {
  id: string;
  dataset_name: string;
  dataset_type: string;
  source: string;
  file_path: string;
  file_format: string;
  row_count: number;
  column_count: number;
  schema_metadata?: Record<string, any>;
  is_active: boolean;
  created_at: string;
}

// ML Detection Proof Interfaces
export interface ZScoreColumnProof {
  column: string;
  sample_size: number;
  mean: number;
  std_dev: number;
  threshold: string;
  threshold_value: number;
  max_z_score: number;
  flagged_count: number;
  status: string;
  formula: string;
  explanation: string;
  flagged_values: Array<{
    row_index: number;
    value: number;
    z_score: number;
    threshold: number;
    message?: string;
  }>;
  distribution_sample: Array<{
    value: number;
    z_score: number;
    is_anomaly: boolean;
  }>;
  related_finding_id?: string;
}

export interface ZScoreMethodProof {
  method: string;
  agent: string;
  classification: string;
  executed: boolean;
  execution_status: string;
  execution_time_ms?: number;
  status: string;
  columns_analyzed: number;
  total_flagged_count: number;
  max_z_score: number;
  threshold: string;
  threshold_value: number;
  formula: string;
  explanation: string;
  columns: ZScoreColumnProof[];
}

export interface IQRColumnProof {
  column: string;
  observations: number;
  sample_size: number;
  q1: number;
  q3: number;
  iqr: number;
  median: number;
  lower_bound: number;
  upper_bound: number;
  outlier_count: number;
  outlier_percentage: number;
  status: string;
  formula: string;
  explanation: string;
  outliers: Array<{
    row_index: number;
    value: number;
    bound_violated: string;
    bound_value: number;
    message?: string;
  }>;
  boxplot?: {
    min: number;
    q1: number;
    median: number;
    q3: number;
    max: number;
    iqr: number;
    lower_bound: number;
    upper_bound: number;
    outlier_count: number;
  };
  related_finding_id?: string;
}

export interface IQRMethodProof {
  method: string;
  agent: string;
  classification: string;
  executed: boolean;
  execution_status: string;
  execution_time_ms?: number;
  status: string;
  columns_analyzed: number;
  total_outliers_count: number;
  multiplier: number;
  method_rule: string;
  formulas: string[];
  explanation: string;
  columns: IQRColumnProof[];
}

export interface IsolationForestMethodProof {
  method: string;
  agent: string;
  classification: string;
  executed: boolean;
  execution_status: string;
  execution_time_ms?: number;
  status: string;
  reason?: string;
  features: string[];
  features_count: number;
  samples: number;
  anomalies_detected: number;
  anomalous_percentage?: number;
  contamination: string | number;
  model_parameters: Record<string, any>;
  score_range?: {
    min: number;
    max: number;
    mean: number;
  };
  separation_threshold?: number;
  prediction_definition: string;
  flagged_anomalies: Array<{
    row_index: number;
    decision_score: number;
    prediction: number;
    features: Record<string, any>;
  }>;
  score_distribution: Array<{
    bin: string;
    count: number;
    is_anomaly_bin: boolean;
  }>;
  related_finding_id?: string;
}

export interface KSTestColumnProof {
  column: string;
  baseline_sample_size: number;
  current_sample_size: number;
  ks_statistic: number;
  p_value: number;
  significance_level: number;
  d_threshold: number;
  decision: string;
  is_drift: boolean;
  baseline_mean: number;
  current_mean: number;
  decision_rule: string;
  explanation: string;
  cdf_curve: Array<{
    x: number;
    baseline_cdf: number;
    current_cdf: number;
  }>;
  related_finding_id?: string;
}

export interface KSTestMethodProof {
  method: string;
  agent: string;
  classification: string;
  executed: boolean;
  execution_status: string;
  execution_time_ms?: number;
  status: string;
  reason?: string;
  significance_level: number;
  d_threshold: number;
  decision_rule: string;
  columns_tested: number;
  drift_detected_count: number;
  columns: KSTestColumnProof[];
  explanation: string;
}

export interface MLDetectionMethodsResponse {
  z_score: ZScoreMethodProof;
  iqr: IQRMethodProof;
  isolation_forest: IsolationForestMethodProof;
  ks_test: KSTestMethodProof;
}

export interface MLDetectionProofResponse {
  inspection_id: string;
  dataset: string;
  created_at?: string;
  methods: MLDetectionMethodsResponse;
}

