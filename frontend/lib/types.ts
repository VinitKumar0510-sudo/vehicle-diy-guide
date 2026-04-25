export interface Vehicle {
  make: string;
  model: string;
  year: number;
  engine?: string;
  desc: string;
}

export interface Step {
  step_number: number;
  title: string;
  instruction: string;
  why?: string;
  torque_spec?: string;
  tool_needed?: string;
  warning?: string;
  confidence: number;
  images?: { url: string; caption: string; source: string }[];
}

export interface Part {
  name: string;
  part_number?: string;
  quantity: number;
  consumable: boolean;
  notes?: string;
}

export interface Guide {
  title: string;
  summary: string;
  difficulty: number;
  time_estimate_minutes: number;
  safety_tier: "green" | "yellow" | "red";
  confidence_score: number;
  warnings: string[];
  tools_required: string[];
  parts_required: Part[];
  steps: Step[];
  from_cache: boolean;
}

export interface AppState {
  vehicle: Vehicle | null;
  repair: string;
  guide: Guide | null;
  sessionId: string;
}
