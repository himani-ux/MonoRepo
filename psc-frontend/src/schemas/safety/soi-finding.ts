export interface SafetySoiFindingAreaProgress {
  area_id: number;
  area_name: string;
}

export interface SafetySoiDigitalSignatureSnapshot {
  device_fingerprint_last8: string;
  signed_at: string;
  signer_display_name: string;
}

export interface SafetySoiRepeatFindingSnapshot {
  badge_text: string | null;
  is_repeat: boolean;
  occurrence_count: number;
}

export interface SafetySoiFindingItem {
  area_id: number;
  area_name: string;
  assigned_crew_id: string | null;
  description: string;
  due_date: string | null;
  id: number;
  incident_linked_id?: number | null;
  incident_linked_number?: string | null;
  incident_worthy_reason?: string | null;
  life_threat_escalation_target?: string | null;
  master_approval_state?: string | null;
  master_counter_signature?: SafetySoiDigitalSignatureSnapshot | null;
  pending_closure_signature?: SafetySoiDigitalSignatureSnapshot | null;
  photo_attachment_path: string | null;
  priority: "HIGH" | "MED" | "LOW";
  repeat?: SafetySoiRepeatFindingSnapshot;
  severity: "HIGH" | "MED" | "LOW";
  status: string;
  title: string;
}

export interface SafetySoiFindingsSnapshot {
  areas: SafetySoiFindingAreaProgress[];
  checklist_unique_id: string;
  completed_area_ids: number[];
  findings: SafetySoiFindingItem[];
  inspection_id: number;
  inspection_reference: string;
  safety_officer_crew_id: string;
}

export interface SafetySoiFindingDraft {
  area_id: number;
  description: string;
  priority: "HIGH" | "MED" | "LOW";
  severity: "HIGH" | "MED" | "LOW";
  title: string;
}

export const safetySoiLifeThreatPatterns: Array<{ label: string; pattern: RegExp }> = [
  { label: "fire", pattern: /\bfire\b/i },
  { label: "explosion", pattern: /\bexplosion\b/i },
  { label: "electrocution", pattern: /\belectrocution\b/i },
  { label: "gas leak", pattern: /\bgas leak\b/i },
  { label: "toxic exposure", pattern: /\btoxic exposure\b/i },
  { label: "confined space", pattern: /\bconfined space\b/i },
  { label: "asphyxiation", pattern: /\basphyxiation\b/i },
  { label: "man overboard", pattern: /\bman overboard\b/i },
  { label: "structural failure", pattern: /\bstructural failure\b/i },
  { label: "collapse", pattern: /\bcollapse\b/i },
  { label: "uncontrolled flooding", pattern: /\buncontrolled flooding\b/i },
  { label: "life-threatening", pattern: /\blife[- ]threatening\b/i },
  { label: "fatal", pattern: /\bfatal(?:ity)?\b/i },
];

export function findSafetySoiLifeThreatMatches(...parts: Array<string | null | undefined>): string[] {
  const haystack = parts.filter(Boolean).join(" ");
  const matches = safetySoiLifeThreatPatterns
    .filter(({ pattern }) => pattern.test(haystack))
    .map(({ label }) => label);
  return Array.from(new Set(matches));
}

export const safetySoiDemoFindingAreas: SafetySoiFindingAreaProgress[] = [
  { area_id: 3, area_name: "Navigating Bridge & Monkey Island" },
  { area_id: 5, area_name: "Mooring Deck + Forward Station" },
  { area_id: 8, area_name: "Engine Control Room + Machinery Flat" },
  { area_id: 13, area_name: "Cross-cutting Safety & Culture" },
];

export const safetySoiDemoFindingsSnapshot: SafetySoiFindingsSnapshot = {
  areas: safetySoiDemoFindingAreas,
  checklist_unique_id: "SOI-0000007-20260501-0007",
  completed_area_ids: [3, 13],
  findings: [
    {
      area_id: 3,
      area_name: "Navigating Bridge & Monkey Island",
      assigned_crew_id: "co-7",
      description: "Bridge wing emergency marker was faded and no longer legible in low light.",
      due_date: "2026-05-14",
      id: 901,
      incident_linked_id: 4101,
      incident_linked_number: "DRAFT-7/2026/T021",
      master_approval_state: null,
      master_counter_signature: null,
      pending_closure_signature: null,
      photo_attachment_path: "vessel-7/soi/bridge-marker-faded.jpg",
      priority: "HIGH",
      repeat: {
        badge_text: "Repeat - 2nd occurrence",
        is_repeat: true,
        occurrence_count: 2,
      },
      severity: "HIGH",
      status: "OPEN",
      title: "Emergency marker faded",
    },
    {
      area_id: 13,
      area_name: "Cross-cutting Safety & Culture",
      assigned_crew_id: null,
      description: "Toolbox talk notes did not capture challenge-and-response evidence for the past week.",
      due_date: "2026-05-18",
      id: 902,
      incident_linked_id: null,
      incident_linked_number: null,
      master_approval_state: null,
      master_counter_signature: null,
      pending_closure_signature: {
        device_fingerprint_last8: "co7-pad1",
        signed_at: "2026-04-29 09:40 LT",
        signer_display_name: "Chief Officer Arun",
      },
      photo_attachment_path: null,
      priority: "MED",
      repeat: {
        badge_text: null,
        is_repeat: false,
        occurrence_count: 1,
      },
      severity: "MED",
      status: "PENDING_CLOSURE",
      title: "Toolbox talk evidence gap",
    },
  ],
  inspection_id: 42,
  inspection_reference: "SOI/ABC/26/07",
  safety_officer_crew_id: "co-7",
};

export const safetySoiDemoFindingDraft: SafetySoiFindingDraft = {
  area_id: 5,
  description: "Forward mooring station drain cover was unsecured after the drill setup.",
  priority: "MED",
  severity: "MED",
  title: "Forward station drain cover unsecured",
};
