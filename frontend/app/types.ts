export type Observation = {
  timestamp: string;
  subject_id: string;
  source: "live" | "replay" | "scenario";
  heart_rate?: number | null;
  spo2?: number | null;
  temperature?: number | null;
  activity?: string | null;
  signal_quality?: number | null;
};

export type MonitoringResult = {
  observation: Observation;
  signal_quality: {
    status: "trustworthy" | "insufficient";
    score: number | null;
    reasons: string[];
  };
  baseline: {
    subject_id: string;
    metric: string;
    center: number;
    scale: number;
    window_size: number;
  } | null;
  anomaly: {
    metric: string;
    severity: "unknown" | "normal" | "elevated" | "critical";
    deviation: number | null;
    consecutive_count: number;
    reasons: string[];
  };
  context: {
    activity: string | null;
    symptoms: string[];
    patient_feedback: string | null;
    is_available: boolean;
    missing_fields: string[];
  };
  risk: {
    score: number;
    severity: "unknown" | "normal" | "elevated" | "critical";
    reasons: string[];
    missing_context: string[];
  };
  decision: {
    action: "monitor" | "recheck" | "escalate";
    reasons: string[];
  };
};